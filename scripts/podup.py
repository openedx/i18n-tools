"""
Simple proof-of-concept of finding strings with different translations across
a number of .po files.
"""

import collections
import glob
import sys

import polib


def compare_po_files(files):
    translations = collections.defaultdict(lambda: collections.defaultdict(set))

    for filename in files:
        fpo = polib.pofile(filename)
        for i, entry in enumerate(fpo):
            if entry.msgstr:
                translations[entry.msgid][entry.msgstr].add(filename)
        print("{:5d} entries in {}".format(i+1, filename))

    dups = 0
    for msgid, msgs in sorted(translations.items()):
        if len(msgs) > 1:
            print(f"{msgid} -->")
            for msg, filenames in sorted(msgs.items()):
                print("    {} ({})".format(msg, ", ".join(sorted(filenames))))
            dups += 1
    print(f"{dups} duplicates")


IGNORE_FILES = ["django.po", "djangojs.po"]

def main(argv):
    files = argv[1:]
    if not files:
        files = [f for f in glob.glob("*.po") if f not in IGNORE_FILES]
    compare_po_files(files)

main(sys.argv)
