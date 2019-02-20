#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import encodings
from pkgutil import iter_modules
from collections import defaultdict
from textwrap import TextWrapper
from optparse import OptionParser
from platform import python_version, uname
from time import strftime


parser = OptionParser()
parser.add_option('-w', '--wrap', dest='wrap', action='store_true',
    help='Wrap output for limited column width')
parser.add_option('-H', '--html', dest='html', action='store_true',
    help='Generate HTML output')
(options, args) = parser.parse_args()


if options.wrap and options.html:
    raise KeyError('Cannot specify --wrap and --html at the same time')

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


if options.wrap:
    wrapper=wraplines
else:
    wrapper=lambda x: ''.join(x)

if options.html:
    # Simulate uname(1) -a output

    sysinfo = ' '.join([getattr(u, attr) for u in (uname(),)
        for attr in ['system', 'node', 'release', 'version', 'machine']])
    print('''<!DOCTYPE html>
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
      and contains a map of the character codes 0x80-0xFF
      in the various 8-bit encodings known by the Python version
      which generated this page.</p>
      <p>Section headlines are clickable links so you can link to
      or bookmark an individual character code.</p>
      <p>This page was generated on %s by Python %s<br/>
      <tt>%s</tt>.</p>
      <hr>
''' % (strftime('%c'), python_version(), sysinfo))
    # Keep <a name="0xFF"> as a synonym for legacy links in this syntax
    title = lambda x: '<h3><a name="%s">&bullet;</a>' \
        '<a name="0x%s">&nbsp;</a>' \
        '<a href="#%s">0x%s</a>' \
        '</h3>\n<p><table>' % (x, x, x, x)
    row = lambda x: '<tr><th>%s</th><td>%s</td>\n' % (x[0], x[1])
    rep = lambda x: '<a href="http://www.fileformat.info/' \
        'info/unicode/char/%04X/">U+%04X</a>' % (ord(x), ord(x))
    enddiv = lambda: '</table>'
    done = lambda: '</body></html>'
else:
    title = lambda x: '0x%s' % x
    row = lambda x: wrapper(x)
    rep = lambda x: repr(x)
    enddiv = lambda: ''
    done = lambda: None

codecs = get_encodings()
result = dict()

for ch in range(128,256,1):
    print(title('%02x' % ch))
    char = bytes([ch])
    result[ch] = defaultdict(list)
    for enc in codecs:
        try:
            code = char.decode(enc)
            result[ch][code].append(enc)
        except UnicodeDecodeError as err:
            if 'character maps to <undefined>' in str(err):
                result[ch]['undefined'].append(enc)
            else:
                raise
    for glyph in sorted(result[ch].keys()):
        if glyph == 'undefined':
            continue
        print(row(['  %s%s (%s): ' % (glyph, u'\u200e', rep(glyph)),
            ', '.join(sorted(result[ch][glyph]))]))
    if 'undefined' in result[ch]:
        print(row(['  (undefined): ',
            ', '.join(sorted(result[ch]['undefined']))]))
    print(enddiv())
if options.html:
    print(done())
