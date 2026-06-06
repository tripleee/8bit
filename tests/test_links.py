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

2. Subsequent runs compare live Wikipedia titles and section
   anchors against the snapshot.  A mismatch means the link
   needs human review.

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
# action=query for title/existence checks (batch up to 50)
_WP_QUERY = (
    "https://en.wikipedia.org/w/api.php"
    "?action=query&prop=info&redirects=1&format=json"
    "&titles={}"
)
# action=parse for section anchor enumeration (one page at a time)
_WP_SECTIONS = (
    "https://en.wikipedia.org/w/api.php"
    "?action=parse&prop=sections&format=json&page={}"
)
_HEADERS = {
    "User-Agent": "8bit-test/1.0 (github.com/tripleee/8bit)"
}


def _extract_links():
    """
    Return {encoding: {'article': path, 'anchor': str_or_None}}
    for all Wikipedia links in encodingtable() output.

    The article path is the component after /wiki/ and before any
    #fragment; the anchor is the fragment (without #) or None.
    """
    encs = bit.get_encodings()
    html = bit.HtmlFormatter().encodingtable(encs)
    found = re.findall(
        r'<a href="https://en\.wikipedia\.org/wiki/([^"]+)">'
        r'([^<]+)</a>',
        html,
    )
    result = {}
    for raw, enc in found:
        parts = raw.split('#', 1)
        result[enc] = {
            'article': parts[0],
            'anchor': parts[1] if len(parts) > 1 else None,
        }
    return result


def _fetch_titles(article_paths):
    """
    Return {article_path: canonical_title_or_None}.
    Uses Wikipedia action=query in batches of up to 50.
    """
    article_paths = list(article_paths)
    result = {}
    for i in range(0, len(article_paths), 50):
        if i:
            time.sleep(1)
        batch = article_paths[i:i + 50]
        param = '|'.join(
            urllib.parse.quote(a, safe='/') for a in batch)
        req = urllib.request.Request(
            _WP_QUERY.format(param), headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        query = data['query']
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


def _fetch_anchors(article_path):
    """
    Return the set of section anchor strings on the page,
    or None if the page cannot be parsed (missing or API error).
    """
    quoted = urllib.parse.quote(article_path, safe='/')
    req = urllib.request.Request(
        _WP_SECTIONS.format(quoted), headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if 'error' in data:
        return None
    return {s['anchor'] for s in data['parse']['sections']}


@pytest.mark.network
class TestWikipediaLinks:
    """
    Verify that every Wikipedia link — including #section anchors
    — in the encoding table HTML still resolves correctly.

    - title unchanged, anchor present → PASS
    - page missing                    → FAIL (needs review)
    - title changed                   → FAIL (needs review)
    - anchor absent from page         → FAIL (needs review)
    - new/removed links               → FAIL (update snapshot)
    """

    def test_links_against_snapshot(self):
        links = _extract_links()
        assert links, (
            "encodingtable() produced no Wikipedia links")

        unique_articles = list({
            info['article'] for info in links.values()
        })
        titles = _fetch_titles(unique_articles)

        if not SNAPSHOT.exists():
            snapshot = {
                enc: {
                    'article': info['article'],
                    'anchor': info['anchor'],
                    'title': titles.get(info['article']),
                }
                for enc, info in sorted(links.items())
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
        anchors_cache = {}

        def get_anchors(art):
            if art not in anchors_cache:
                time.sleep(0.3)
                anchors_cache[art] = _fetch_anchors(art)
            return anchors_cache[art]

        for enc in sorted(set(links) | set(snapshot)):
            if enc not in links:
                problems.append(
                    f"{enc}: link removed from encodingtable()"
                )
                continue
            if enc not in snapshot:
                info = links[enc]
                art = info['article']
                frag = (f"#{info['anchor']}"
                        if info['anchor'] else "")
                problems.append(
                    f"{enc}: new link {art!r}{frag} "
                    f"(title: {titles.get(art)!r})"
                    " — add to snapshot"
                )
                continue

            ref = snapshot[enc]
            info = links[enc]
            art = info['article']
            anchor = info['anchor']
            ref_anchor = ref.get('anchor')

            if art != ref['article'] or anchor != ref_anchor:
                t = titles.get(art)
                old = ref['article'] + (
                    f"#{ref_anchor}" if ref_anchor else "")
                new = art + (f"#{anchor}" if anchor else "")
                problems.append(
                    f"{enc}: URL changed "
                    f"{old!r} → {new!r} "
                    f"(now: {t!r}); needs review"
                )
                continue

            title = titles.get(art)
            if title is None:
                problems.append(
                    f"{enc} → {art!r}: "
                    "page deleted; needs review"
                )
                continue

            if title != ref['title']:
                problems.append(
                    f"{enc} → {art!r}: title changed "
                    f"{ref['title']!r} → {title!r}; "
                    "needs review"
                )

            if anchor:
                sections = get_anchors(art)
                if sections is None:
                    problems.append(
                        f"{enc} → {art}#{anchor}: "
                        "cannot fetch sections; needs review"
                    )
                elif anchor not in sections:
                    problems.append(
                        f"{enc} → {art}#{anchor}: "
                        "section no longer exists; needs review"
                    )

        if problems:
            pytest.fail(
                "Wikipedia link issues (needs review):\n"
                + "\n".join(f"  {p}" for p in problems)
            )
