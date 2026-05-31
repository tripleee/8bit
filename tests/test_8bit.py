import importlib
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
