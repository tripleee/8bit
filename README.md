8bit
====

Generate a mapping from legacy 8-bit encodings to Unicode.

HTML output: https://tripleee.github.io/8bit/
(QWERTesy of https://github.io/)

See the HTML page for an explanation of the output format
and additional usage instructions.


Command-line use
----------------

You can pass in a "mystery string" and have it decoded in various ways.

```
bash$ 8bit ï»¿
'W\x8b\xab': ['cp037', 'cp273', 'cp500', 'cp1026', 'cp1140']
'\x8b\xaf\xa8': ['cp437', 'cp850', 'cp857', 'cp858']
'\xef\xbb\xbf': ['cp1252', 'cp1254', 'cp1258', 'iso8859_9', 'iso8859_15', 'latin_1', 'palmos']
'\xdd\xfd\xb9': ['hp_roman8']
'\x95\xdf\xc0': ['mac_croatian']
'\x95\xc8\xc0': ['mac_iceland', 'mac_roman', 'mac_romanian', 'mac_turkish']
'\ufeff': ['utf-8']
```

There is also a `--table` option which lets you generate the web page
or a textual rendering of the same information.


License
-------

MIT License
