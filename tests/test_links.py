"""
Snapshot-based network tests for Wikipedia links in the
generated HTML encoding table.

These tests are slow and require internet access.
They are marked ``network`` and excluded from the default run.

Typical workflow
----------------
1. First run creates tests/wikipedia_snapshots.json::

       pytest -m network tests/test_links.py

   The test is skipped with a message; commit the snapshot file.

2. Subsequent runs compare live Wikipedia titles against the
   snapshot.  A mismatch means the link needs human review.

3. After reviewing and fixing a stale link, delete the snapshot
   and repeat from step 1, or manually update the JSON entry.
"""

import importlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

bit = importlib.import_module("8bit")

SNAPSHOT = Path(__file__).parent / "wikipedia_snapshots.json"
# The action API accepts up to 50 titles per request via '|'
_WP_API = (
    "https://en.wikipedia.org/w/api.php"
    "?action=query&prop=info&redirects=1&format=json"
    "&titles={}"
)
_HEADERS = {
    "User-Agent": "8bit-test/1.0 (github.com/tripleee/8bit)"
}


def _extract_links():
    """
    Return {encoding: article_path} for all Wikipedia links
    produced by encodingtable().

    article_path is the raw path component after /wiki/ with
    any #section anchor stripped, since the API operates on
    page titles rather than sections.
    """
    encs = bit.get_encodings()
    html = bit.HtmlFormatter().encodingtable(encs)
    found = re.findall(
        r'<a href="https://en\.wikipedia\.org/wiki/([^"]+)">'
        r'([^<]+)</a>',
        html,
    )
    return {enc: art.split('#')[0] for art, enc in found}


def _fetch_titles(article_paths):
    """
    Return {article_path: canonical_title_or_None} for every
    path in article_paths.  Uses the Wikipedia action API in
    batches of 50, with a 1-second pause between batches.

    The API normalises underscores to spaces and follows
    redirects; the returned title is the canonical page title.
    """
    article_paths = list(article_paths)
    result = {}
    for i in range(0, len(article_paths), 50):
        if i:
            time.sleep(1)
        batch = article_paths[i:i + 50]
        titles_param = '|'.join(
            urllib.parse.quote(a, safe='/') for a in batch)
        url = _WP_API.format(titles_param)
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        query = data['query']
        # Build forward chain: input → normalised → redirected
        norm = {
            n['from']: n['to']
            for n in query.get('normalized', [])
        }
        redir = {
            r['from']: r['to']
            for r in query.get('redirects', [])
        }
        by_title = {
            p['title']: p for p in query['pages'].values()
        }

        for art in batch:
            step = norm.get(art, art)
            step = redir.get(step, step)
            page = by_title.get(step)
            if page is None or 'missing' in page:
                result[art] = None
            else:
                result[art] = page['title']
    return result


@pytest.mark.network
class TestWikipediaLinks:
    """
    Verify that every Wikipedia link in the encoding table HTML
    still resolves to the same canonical page title as when the
    snapshot was taken.

    - title unchanged → PASS
    - page missing    → FAIL (needs review)
    - title changed   → FAIL (needs review)
    - new link added  → FAIL (update snapshot)
    - link removed    → FAIL (update snapshot)
    """

    def test_links_against_snapshot(self):
        links = _extract_links()
        assert links, (
            "encodingtable() produced no Wikipedia links")

        # Fetch all unique article titles in one batched call
        unique = list(set(links.values()))
        titles = _fetch_titles(unique)

        if not SNAPSHOT.exists():
            snapshot = {
                enc: {'article': art, 'title': titles[art]}
                for enc, art in sorted(links.items())
            }
            SNAPSHOT.write_text(
                json.dumps(snapshot, indent=2, sort_keys=True)
                + "\n"
            )
            pytest.skip(
                f"Snapshot written to {SNAPSHOT}; "
                "commit it and re-run to validate"
            )

        snapshot = json.loads(SNAPSHOT.read_text())
        problems = []

        for enc in sorted(set(links) | set(snapshot)):
            if enc not in links:
                problems.append(
                    f"{enc}: link removed from encodingtable()"
                )
                continue
            if enc not in snapshot:
                problems.append(
                    f"{enc}: new link {links[enc]!r} "
                    f"(title: {titles.get(links[enc])!r})"
                    " — add to snapshot"
                )
                continue

            ref = snapshot[enc]
            art = links[enc]

            if art != ref['article']:
                # URL changed; title may not be in our batch
                t = titles.get(art) or next(
                    iter(_fetch_titles([art]).values()))
                problems.append(
                    f"{enc}: URL changed "
                    f"{ref['article']!r} → {art!r} "
                    f"(now: {t!r}); needs review"
                )
                continue

            title = titles.get(art)
            if title is None:
                problems.append(
                    f"{enc} → {art!r}: "
                    "page deleted; needs review"
                )
            elif title != ref['title']:
                problems.append(
                    f"{enc} → {art!r}: title changed "
                    f"{ref['title']!r} → {title!r}; "
                    "needs review"
                )

        if problems:
            pytest.fail(
                "Wikipedia link issues (needs review):\n"
                + "\n".join(f"  {p}" for p in problems)
            )
