#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import encodings
from pkgutil import iter_modules
from collections import defaultdict
from textwrap import TextWrapper
from platform import python_version, uname
from time import strftime
import re


# Force undefined to sort last
UNDEFINED = '\U0001fffffundefined'


class Formatter:
    def __init__(self, wrapper=None):
        self.wrapper = wrapper

    def emit(self, message):
        if message is not None:
            print(message)

    def header(self, codeclist):
        encs = ', '.join(codeclist)
        if self.wrapper is not None:
            return self.wrapper(['Supported encodings:', encs])
        else:
            return 'Supported encodings: %s' % encs

    def item(self, char):
        return '0x%s' % char

    def row(self, char, code, encs):
        if char == UNDEFINED:
            header = '(undefined)'
        else:
            header = '  %s (U+%04x): ' % (char, code)
        if self.wrapper is not None:
            return self.wrapper([header, encs])
        else:
            return '%s%s' % (header, encs)

    def enditem(self):
        return None

    def endsection(self):
        return '-' * 72

    def footer(self):
        return None


class HtmlFormatter(Formatter):
    def __init__(self, with_fork_me=False):
        self.fork_me = with_fork_me

    def header(self, codeclist):
        encs = self.encodingtable(codeclist)

        # Simulate uname(1) -a output
        sysinfo = ' '.join(
            [getattr(u, attr) for u in (uname(),)
             for attr in ['system', 'node', 'release', 'version', 'machine']])

        return('''<!DOCTYPE html>
<html lang="en" class="">
  <head>
    <meta charset='utf-8'>
    <meta http-equiv="Content-Encoding" content="utf-8">
    <meta http-equiv="Content-Language" content="en">
    <title>Table of Legacy 8-bit Encodings</title>
    <style>
      th { white-space: nowrap; text-align: left; vertical-align: top; }
      td { vertical-align: text-top; }
    </style>
  </head>
  <body>''' +
  ('''\
  <a href="https://github.com/tripleee/8bit"
  style="position: absolute; top: 0; right: 0; border: 0;">
  <svg width="100" height="100" viewBox="0 0 100 100">
    <polygon fill="#151513" fill-opacity="0.5" points="0,0 100,0 100,100" />
    <g>
      <text x="50" y="70" fill="#fff" font-size="11" font-family="Arial"
            text-anchor="middle" transform="rotate(45 74,74)">
        Fork me on Github
      </text>
    </g>
  </svg>
  </a>''' if self.fork_me else '') +
  '''\
     <h1>Table of Legacy 8-bit Encodings</h1>

      <p>This table was generated from
      <a href="https://github.com/tripleee/8bit/">
        https://github.com/tripleee/8bit/</a>
      and contains a map of the character codes 0x00-0x31 and 0x80-0xFF
      in the various 8-bit encodings known by the Python version
      which generated this page.</p>

      <p>Section headlines like <a href="#0x80">0x80</a>
      are clickable links so you can link to or bookmark
      an individual character code.</p>

      <p>This page was generated on %s by Python %s<br/>
      <tt>%s</tt>.</p>

      <p><table><tr><th>Supported encodings:</th><td>\n%s</td></tr></table></p>
      <hr>
''' % (strftime('%c'), python_version(), sysinfo, encs))

    def encodingtable(self, encs):
        # map regular expression to Wikipedia link
        template = {
            r'^cp037$': 'Code_page_37',
            r'^cp(273|500|1140)$': r'Code_page_37#\1',
            r'^cp(437|7\d{2}|8(?!7[45])\d{2}|1006)$': r'Code_page_\1',
            r'^cp(125\d)$': r'Windows-\1',
            r'^iso8859_(\d{1,2})$': r'ISO/IEC_8859-\1',
            r'^hp_roman8': r'HP_Roman#Roman-8',
            r'^koi8_([rtu])$': r'KOI8->>\1',
            r'^kz1048$': 'Windows-1251#Kazakh_variant',
            r'^latin_1': 'ISO/IEC_8859-1',
            r'^mac_(armenian|roman)$': r'Mac_OS_>>\1',
            r'^mac_(arabic|farsi|greek)$': r'Mac>>\1_encoding',
            r'^mac_latin2$': 'Mac_OS_Central_European_encoding',
            r'^mac_(croatian|cyrillic|romanian|turkish)$':
                r'Mac_OS_>>\1_encoding',
            r'^mac_iceland$': 'Mac_OS_Icelandic_encoding',
            # r'^mac_latin2$': 'Macintosh_Latin_encoding',
            r'^palmos$': 'https://dflund.se/~triad/krad/recode/palm.html',
            r'tis_620$': 'Thai_Industrial_Standard_620-2533'
            }
        result = []
        for enc in encs:
            for pat, sub in template.items():
                if re.match(pat, enc):
                    replacement = re.sub(pat, sub, enc)
                    if sub.startswith("https://"):
                        result.append(f'<a href="{replacement}">{enc}</a>')
                    else:
                        replacement = re.sub(
                            r'>>(.)', lambda x: x.group(1).upper(), replacement)
                        result.append(
                            '<a href="https://en.wikipedia.org/wiki/'
                            f'{replacement}">{enc}</a>')
                    break
            else:
                result.append(enc)
        return ',\n'.join(result)

    def item(self, char):
        # Keep <a name="0xFF"> as a synonym for legacy links in this syntax
        return '<h3><a name="%s">&bullet;</a>' \
            '<a name="0x%s">&nbsp;</a>' \
            '<a href="#%s">0x%s</a>' \
            '</h3>\n<p><table>' % (char, char, char, char)

    def row(self, char, code, encs):
        if char == UNDEFINED:
            header = '</th><th>(undefined)'
        else:
            header = '&#%i;</th><th>(%s)' % (
                0x2420 if code == 0x20 else
                0x2421 if code == 0x7f else
                code + 0x2400 if code <= 32 else code, self.rep(code))
        return '<tr><th>&zwnj;</th><th>%s</th><td>%s</td>' % (
            header, encs)

    def enditem(self):
        return '</table></p>'

    def rep(self, code):
        return '<a href="http://www.fileformat.info/' \
            'info/unicode/char/%04X/">U+%04X</a>' % (code, code)

    def endsection(self):
        return '\n<hr/>\n'

    def footer(self):
        return '</body></html>'


def get_encodings():
    '''http://stackoverflow.com/a/1728414/874188'''

    exclude=set(['aliases',
        # Exclude binary encodings, ascii encodings, reserved encodings, etc
        'bz2_codec', 'punycode', 'hex_codec', 'uu_codec', 'unicode_internal',
        'quopri_codec', 'raw_unicode_escape', 'unicode_escape', 'base64_codec',
        'zlib_codec', 'charmap', 'ascii', 'string_escape', 'rot_13',
        'undefined', 'idna', 'oem',
        # Wacky Windows special case in 3.14
        '_win_cp_codecs',
        # Exclude multi-byte encodings: UTF-xx
        'mbcs', 'utf_7', 'utf_8', 'utf_8_sig',
        'utf_16', 'utf_16_be', 'utf_16_le',
        'utf_32', 'utf_32_be', 'utf_32_le',
        'cp65001',
        # Chinese
        'big5hkscs', 'gbk', 'gb2312', 'hz', 'big5', 'gb18030', 'cp950',
        # Japanese
        'euc_jp', 'euc_jisx0213', 'euc_jis_2004',
        'iso2022_jp', 'iso2022_jp_ext', 'iso2022_jp_1',
        'iso2022_jp_2', 'iso2022_jp_3', 'iso2022_jp_2004',
        'shift_jis', 'shift_jis_2004', 'shift_jisx0213', 'cp932',
        # Korean
        'euc_kr', 'iso2022_kr', 'johab', 'cp949'])

    found=set(name for im, name, ispkg in iter_modules(encodings.__path__))
    exclude = exclude.union(set(encodings.aliases.aliases.keys()))
    found.difference_update(exclude)
    # Sort by padded numeric suffix, so that 13 comes before 110 and after 2 etc
    return sorted(
        found, key=lambda x: re.sub(
            r'(?<=\D)(\d+)$', lambda y: "%04i" % int(y.group(1)), x))


def wraplines (lines):
    t = TextWrapper(initial_indent=lines[0],
        subsequent_indent=' ' * len(lines[0]))
    return '\n'.join(t.wrap(*lines[1:]))


def get_mappings(ch, codecs):
    result = dict()
    char = bytes([ch])
    result[ch] = defaultdict(list)
    for enc in codecs:
        try:
            code = char.decode(enc)
            result[ch][code].append(enc)
        except UnicodeDecodeError as err:
            if 'character maps to <undefined>' in str(err):
                result[ch][UNDEFINED].append(enc)
            else:
                raise
    for glyph in sorted(result[ch].keys()):
        yield glyph, result[ch][glyph]


def printrange(start, end, codecs):
    for ch in range(start, end):
        formatter.emit(formatter.item('%02x' % ch))
        for glyph, encs in get_mappings(ch, codecs):
            formatter.emit(formatter.row(
                glyph, None if glyph == UNDEFINED else ord(glyph),
                ', '.join(encs)))
        formatter.emit(formatter.enditem())


def table(formatter):
    """
    Render a table of all the character codes we support using the
    provided formatter.
    """
    formatter.emit(formatter.header(codecs))
    printrange(0, 32, codecs)
    formatter.emit(formatter.endsection())
    printrange(128, 256, codecs)
    formatter.emit(formatter.footer())


def renderings(codecs, string):
    """
    Print a string in all the encodings which can interpret it.
    """
    seen = defaultdict(list)
    for codec in codecs:
        try:
            seen[string.encode(codec)].append(codec)
        except UnicodeEncodeError:
            pass
    for result, codecs in seen.items():
        print(f"{repr(result)[1:]}: {codecs}")
    try:
        u = string.encode('latin-1').decode('utf-8')
        if u not in seen:
            print(f"{repr(u)}: ['utf-8']")
    except UnicodeEncodeError:
        pass


if __name__ == "__main__":
    from argparse import ArgumentParser, REMAINDER

    parser = ArgumentParser(
        prog='8bit',
        description='8-bit character encoding mapping and information')
    parser.add_argument(
        '-t', '--table', dest='table',
        choices=['html', 'html-with-fork-me', 'text'],
        help='Generate tabular output (specify "html" or text)')
    parser.add_argument('-w', '--wrap', dest='wrap', action='store_true',
        help='Wrap text table output for limited column width')
    parser.add_argument('strings', metavar='s', nargs=REMAINDER,
        help='Strings to map to various encodings')
    args = parser.parse_args()

    codecs = get_encodings()

    if args.table:
        if args.wrap and args.table in ('html', 'html-with-fork-me'):
            raise ValueError('Cannot specify --wrap with --table html')

        formatter = HtmlFormatter(
            with_fork_me=args.table == 'html-with-fork-me'
        ) if args.table in ('html', 'html-with-fork-me') else Formatter(
                wrapper=wraplines if args.wrap else None)
        table(formatter)

    elif args.strings:
        renderings(codecs, ' '.join(args.strings))
    else:
        renderings(codecs, '')

        ######## TODO: with no options, print usage message
        ######## TODO: -- end of options
        ######## TODO: --list-refs tab-separated list of encodings with references
