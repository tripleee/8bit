#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
from textwrap import TextWrapper
from optparse import OptionParser


parser = OptionParser()
parser.add_option('-w', '--wrap', dest='wrap', action='store_true',
    help='Wrap output for limited column width')
(options, args) = parser.parse_args()


def encodings():
    '''http://stackoverflow.com/a/1728414/874188'''
    import pkgutil
    import encodings

    exclude=set(['aliases',
        # Exclude binary encodings, ascii encodings, reserved encodings, etc
        'bz2_codec', 'punycode', 'hex_codec', 'uu_codec', 'unicode_internal',
        'quopri_codec', 'raw_unicode_escape', 'unicode_escape', 'base64_codec',
        'zlib_codec', 'charmap', 'ascii', 'string_escape', 'rot_13',
        'undefined', 'idna',
        # Exclude multi-byte encodings: UTF-xx
        'mbcs', 'utf_7', 'utf_8', 'utf_8_sig',
        'utf_16', 'utf_16_be', 'utf_16_le',
        'utf_32', 'utf_32_be', 'utf_32_le',
        # Chinese
        'big5hkscs', 'gbk', 'gb2312', 'hz', 'big5', 'gb18030', 'cp950',
        # Japanese
        'euc_jp', 'euc_jisx0213', 'euc_jis_2004',
        'iso2022_jp', 'iso2022_jp_ext', 'iso2022_jp_1',
        'iso2022_jp_2', 'iso2022_jp_3', 'iso2022_jp_2004',
        'shift_jis', 'shift_jis_2004', 'shift_jisx0213', 'cp932',
        # Korean
        'euc_kr', 'iso2022_kr', 'johab', 'cp949'])

    found=set(name for im, name, ispkg in
        pkgutil.iter_modules(encodings.__path__))
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

codecs = encodings()
result = dict()

for ch in xrange(128,256,1):
    print("0x%02x" % ch)
    char = chr(ch)
    result[ch] = defaultdict(list)
    for enc in codecs:
        try:
            code = char.decode(enc)
            result[ch][code].append(enc)
        except UnicodeDecodeError, err:
            if 'character maps to <undefined>' in err:
                result[ch]['undefined'].append(enc)
            else:
                raise
    for glyph in sorted(result[ch].keys()):
        if glyph == 'undefined':
            continue
        print(wrapper(['  %s%s (%r): ' % (glyph, u'\u200e', glyph),
            ', '.join(sorted(result[ch][glyph]))]).encode('utf-8'))
    if 'undefined' in result[ch]:
        print(wrapper(['  (undefined): ',
            ', '.join(sorted(result[ch]['undefined']))]).encode('utf-8'))
    print('')
