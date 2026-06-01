import importlib
import re
import sys
import pytest

bit = importlib.import_module("8bit")


class TestGetEncodings:
    def test_returns_list(self):
        assert isinstance(bit.get_encodings(), list)

    def test_nonempty(self):
        assert len(bit.get_encodings()) > 10

    def test_excludes_utf8(self):
        assert 'utf_8' not in bit.get_encodings()

    def test_excludes_ascii(self):
        assert 'ascii' not in bit.get_encodings()

    def test_excludes_aliases(self):
        assert 'aliases' not in bit.get_encodings()

    def test_includes_cp437(self):
        assert 'cp437' in bit.get_encodings()

    def test_includes_latin_1(self):
        assert 'latin_1' in bit.get_encodings()

    def test_numeric_sort(self):
        encs = bit.get_encodings()
        # iso8859_2 must sort before iso8859_13
        assert encs.index('iso8859_2') < encs.index('iso8859_13')


class TestGetMappings:
    def test_known_char(self):
        # 0xe9 is é (U+00E9) in iso8859_1
        results = list(bit.get_mappings(0xe9, ['iso8859_1']))
        assert len(results) == 1
        glyph, codecs = results[0]
        assert glyph == '\xe9'
        assert 'iso8859_1' in codecs

    def test_multiple_encodings_same_glyph(self):
        # 0x41 is 'A' in both cp437 and iso8859_1
        results = dict(
            bit.get_mappings(0x41, ['cp437', 'iso8859_1']))
        assert 'A' in results
        assert 'cp437' in results['A']
        assert 'iso8859_1' in results['A']

    def test_undefined_byte(self):
        # 0x81 is undefined in cp1252
        results = dict(bit.get_mappings(0x81, ['cp1252']))
        assert bit.UNDEFINED in results
        assert 'cp1252' in results[bit.UNDEFINED]

    def test_different_glyphs_per_encoding(self):
        # 0x80 maps differently in cp437 vs iso8859_1
        results = dict(
            bit.get_mappings(0x80, ['cp437', 'iso8859_1']))
        assert len(results) >= 1


class TestFormatter:
    def setup_method(self):
        self.f = bit.Formatter()

    def test_item(self):
        assert self.f.item('80') == '0x80'

    def test_row_char(self):
        row = self.f.row('A', 65, 'cp437')
        assert 'A' in row
        assert 'cp437' in row

    def test_row_undefined(self):
        row = self.f.row(bit.UNDEFINED, None, 'cp037')
        assert '(undefined)' in row

    def test_endsection(self):
        assert self.f.endsection() == '-' * 72

    def test_footer_is_none(self):
        assert self.f.footer() is None

    def test_enditem_is_none(self):
        assert self.f.enditem() is None

    def test_header(self):
        h = self.f.header(['cp437', 'iso8859_1'])
        assert 'cp437' in h
        assert 'iso8859_1' in h


class TestHtmlFormatter:
    def setup_method(self):
        self.f = bit.HtmlFormatter()

    def test_item_contains_anchor(self):
        item = self.f.item('80')
        assert '<a' in item
        assert '0x80' in item

    def test_row_char_is_table_row(self):
        row = self.f.row('A', 65, 'cp437')
        assert '<tr>' in row
        assert 'cp437' in row

    def test_row_undefined(self):
        row = self.f.row(bit.UNDEFINED, None, 'cp037')
        assert '(undefined)' in row

    def test_enditem(self):
        assert '</table>' in self.f.enditem()

    def test_footer(self):
        assert '</html>' in self.f.footer()

    def test_header_contains_doctype(self):
        h = self.f.header(['cp437', 'iso8859_1'])
        assert '<!DOCTYPE html>' in h

    def test_fork_me_banner(self):
        f = bit.HtmlFormatter(with_fork_me=True)
        h = f.header(['cp437'])
        assert 'Fork me' in h

    def test_no_fork_me_by_default(self):
        h = self.f.header(['cp437'])
        assert 'Fork me' not in h


class TestTable:
    def test_text_output(self, capsys):
        encs = ['cp437', 'iso8859_1']
        bit.table(bit.Formatter(), encs)
        out = capsys.readouterr().out
        assert '0x00' in out
        assert '0x80' in out

    def test_html_output(self, capsys):
        encs = ['cp437']
        bit.table(bit.HtmlFormatter(), encs)
        out = capsys.readouterr().out
        assert '<!DOCTYPE html>' in out
        assert '</html>' in out


class TestRenderings:
    def test_output_for_accented(self, capsys):
        encs = bit.get_encodings()
        bit.renderings(encs, 'café')
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_output_for_ascii(self, capsys):
        encs = bit.get_encodings()
        bit.renderings(encs, 'hello')
        out = capsys.readouterr().out
        assert len(out) > 0


class TestMain:
    def test_main_with_string(self, capsys, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['8bit', 'café'])
        bit.main()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_main_table_html(self, capsys, monkeypatch):
        monkeypatch.setattr(
            sys, 'argv', ['8bit', '--table', 'html'])
        bit.main()
        out = capsys.readouterr().out
        assert '<!DOCTYPE html>' in out

    def test_main_wrap_with_html_raises(self, monkeypatch):
        monkeypatch.setattr(
            sys, 'argv', ['8bit', '--table', 'html', '--wrap'])
        with pytest.raises(ValueError):
            bit.main()


class TestReadmeConsistency:
    """
    Verify the README example and documented behaviour
    stay consistent with the code.

    The README shows: 8bit ï»¿
    ï»¿ = U+00EF U+00BB U+00BF; its latin-1 encoding
    b'\\xef\\xbb\\xbf' is valid UTF-8 for U+FEFF (BOM).
    """

    # The "mystery string" from the README example
    BOM_STRING = 'ï»¿'

    def _renderings_lines(self, capsys):
        encs = bit.get_encodings()
        bit.renderings(encs, self.BOM_STRING)
        return capsys.readouterr().out.strip().splitlines()

    def test_output_format_is_repr_colon_list(self, capsys):
        """Each output line must look like '<bytes>': [<codecs>]"""
        for line in self._renderings_lines(capsys):
            assert re.match(r"^'.*': \[.+\]$", line), (
                f"Unexpected format: {line!r}")

    def test_utf8_bom_shown_on_last_line(self, capsys):
        """README last line: '\\ufeff': ['utf-8']"""
        lines = self._renderings_lines(capsys)
        last = lines[-1]
        assert "\\ufeff" in last
        assert "utf-8" in last

    def test_latin1_group_present(self, capsys):
        """README shows latin_1 in the \\xef\\xbb\\xbf group"""
        out = '\n'.join(self._renderings_lines(capsys))
        assert 'latin_1' in out

    def test_ebcdic_group_present(self, capsys):
        """README shows cp037 in the EBCDIC group"""
        out = '\n'.join(self._renderings_lines(capsys))
        assert 'cp037' in out

    def test_html_has_clickable_section_anchors(self, capsys):
        """
        README: section headlines like 0x80 are clickable links.
        Items use bare-hex hrefs (#80) but carry both
        <a name="80"> and <a name="0x80"> for legacy links.
        The header description also references #0x80.
        """
        bit.table(bit.HtmlFormatter(), ['latin_1'])
        out = capsys.readouterr().out
        # Header description uses the 0x-prefixed form as an example
        assert '<a href="#0x80">0x80</a>' in out
        # Item section links use bare hex
        assert '<a href="#80">' in out
        # Legacy anchor form is present on every item
        assert '<a name="0x80">' in out

    def test_table_html_fork_me(self, capsys, monkeypatch):
        """html-with-fork-me adds the Fork Me banner"""
        monkeypatch.setattr(
            sys, 'argv', ['8bit', '--table', 'html-with-fork-me'])
        bit.main()
        out = capsys.readouterr().out
        assert '<!DOCTYPE html>' in out
        assert 'Fork me' in out

    def test_table_text_accepted(self, capsys, monkeypatch):
        """--table text is a documented choice"""
        monkeypatch.setattr(
            sys, 'argv', ['8bit', '--table', 'text'])
        bit.main()
        assert '0x80' in capsys.readouterr().out

    def test_wrap_accepted_with_text(self, capsys, monkeypatch):
        """--wrap is accepted alongside --table text"""
        monkeypatch.setattr(
            sys, 'argv', ['8bit', '--table', 'text', '--wrap'])
        bit.main()
        assert '0x80' in capsys.readouterr().out

    def test_undocumented_table_choice_rejected(self, monkeypatch):
        """--table rejects choices not in the documented set"""
        monkeypatch.setattr(
            sys, 'argv', ['8bit', '--table', 'pdf'])
        with pytest.raises(SystemExit):
            bit.main()
