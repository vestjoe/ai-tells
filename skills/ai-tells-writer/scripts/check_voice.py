#!/usr/bin/env python3
"""Find text a voice profile copied from the samples it was built from.

    check_voice.py [--min=N] PROFILE SAMPLE...

Prints each run of N or more words (default 8) that appears in both the
profile and a sample, as COPIED: "<run>" (<sample>), then TOTAL: <count>.
Case, punctuation, and curly versus straight apostrophes are ignored.
Fenced code is checked too.

Exit codes: 0 nothing copied, 1 copied runs found, 2 bad arguments or unreadable file.
"""

import re
import sys

TOKEN = re.compile(r"[a-z0-9']+")


def words(text):
    text = text.replace('’', "'").replace('‘', "'").lower()
    return [w.strip("'") for w in TOKEN.findall(text) if w.strip("'")]


def shared_runs(profile, sample, n=8):
    """Maximal runs of n or more consecutive words found in both texts, in profile order."""
    p = words(profile)
    s = words(sample)
    windows = {tuple(s[i:i + n]) for i in range(len(s) - n + 1)}
    runs, i = [], 0
    while i <= len(p) - n:
        if tuple(p[i:i + n]) in windows:
            j = i + 1
            while j <= len(p) - n and tuple(p[j:j + n]) in windows:
                j += 1
            runs.append(' '.join(p[i:j - 1 + n]))
            i = j - 1 + n
        else:
            i += 1
    return runs


def read(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def main(argv):
    n, paths = 8, []
    for a in argv:
        m = re.fullmatch(r'--min=(\d+)', a)
        if m:
            n = int(m.group(1))
        elif a.startswith('-'):
            paths = []
            break
        else:
            paths.append(a)
    if len(paths) < 2 or n < 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        profile = read(paths[0])
        samples = [(p, read(p)) for p in paths[1:]]
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 2
    total = 0
    for path, text in samples:
        for run in shared_runs(profile, text, n):
            print('COPIED: "{0}" ({1})'.format(run, path))
            total += 1
    print('TOTAL: {0}'.format(total))
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
