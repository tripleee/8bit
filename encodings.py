#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import encodings
from pkgutil import iter_modules
from collections import defaultdict
from textwrap import TextWrapper
from optparse import OptionParser
from platform import python_version, uname
from time import strftime


######## XXX FIXME: replace with argparse
parser = OptionParser()
parser.add_option('-w', '--wrap', dest='wrap', action='store_true',
    help='Wrap output for limited column width')
parser.add_option('-H', '--html', dest='html', action='store_true',
    help='Generate HTML output')
(options, args) = parser.parse_args()


if options.wrap and options.html:
    raise KeyError('Cannot specify --wrap and --html at the same time')

# Force undefined to sort last
UNDEFINED = '\U0001fffffundefined'


class Formatter:
    def __init__(self, wrapper=None):
        self.wrapper = wrapper

    def emit(self, message):
        if message is not None:
            print(message)

    def header(self):
        return None

    def item(self, char):
        return '0x%s' % char

    def row(self, char, encodings):
        if char == UNDEFINED:
            header = '(undefined)'
        else:
            header = '  %s (U+%04x): ' % (char, ord(char))
        if self.wrapper is not None:
            return self.wrapper([header, encodings])
        else:
            return '%s: %s' % (header, encodings)

    def enditem(self):
        return None

    def endsection(self):
        return '-' * 72

    def footer(self):
        return None


class HtmlFormatter(Formatter):
    def header(self):
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
  <body>
     <h1>Table of Legacy 8-bit Encodings</h1>
      <p>This table was generated from
      <a href="https://github.com/tripleee/8bit/">
        https://github.com/tripleee/8bit/</a>
      and contains a map of the character codes 0x00-0x31 and 0x80-0xFF
      in the various 8-bit encodings known by the Python version
      which generated this page.</p>
      <p>Section headlines are clickable links so you can link to
      or bookmark an individual character code.</p>
      <p>This page was generated on %s by Python %s<br/>
      <tt>%s</tt>.</p>
      <hr>
''' % (strftime('%c'), python_version(), sysinfo))

    def item(self, char):
        # Keep <a name="0xFF"> as a synonym for legacy links in this syntax
        return '<h3><a name="%s">&bullet;</a>' \
            '<a name="0x%s">&nbsp;</a>' \
            '<a href="#%s">0x%s</a>' \
            '</h3>\n<p><table>' % (char, char, char, char)

    def row(self, char, encodings):
        if char == UNDEFINED:
            header = '</th><th>(undefined)'
        else:
            # hack
            header = '&#%i;</th><th>(%s)' % (ord(char), self.rep(ord(char)))
        return '<tr><th>&zwnj;</th><th>%s</th><td>%s</td>' % (
            header, encodings)

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
    return found


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
        yield glyph, sorted(result[ch][glyph])

def printrange(start, end, codecs):
    for ch in range(start, end):
        formatter.emit(formatter.item('%02x' % ch))
        for glyph, encodings in get_mappings(ch, codecs):
            formatter.emit(formatter.row(glyph, ', '.join(encodings)))
        formatter.emit(formatter.enditem())


formatter = HtmlFormatter() if options.html else Formatter(
    wrapper=wraplines if options.wrap else None)
codecs = get_encodings()

formatter.emit(formatter.header())
printrange(0, 32, codecs)
formatter.emit(formatter.endsection())
printrange(128, 256, codecs)
formatter.emit(formatter.footer())
