#!/usr/bin/env python3
"""Compare an edited Markdown file with the original it came from.

    check_edit.py ORIGINAL EDITED

Prints what the edit did, sentence by sentence:
  cut        sentences in the original that are gone
  reworded   edited sentences paired with the original sentence they replace
  NEW        edited sentences with no original sentence behind them
and the word count of each section (a heading starts a section), flagging any
section that grew. Bracketed placeholders such as [source] don't count as words.

Exit codes: 0 no section grew, 1 a section grew, 2 bad arguments or unreadable file.
"""

import difflib
import re
import sys

PLACEHOLDER = re.compile(r'\[[^\]]*\](?!\()')


def blocks(text):
    """(section, line) pairs for prose lines, skipping fenced code and front matter."""
    lines, out, section, fence = text.splitlines(), [], '(top)', None
    if lines and lines[0].strip() in ('---', '+++'):
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == lines[0].strip()), 0)
        lines = lines[end + 1:]
    for line in lines:
        mark = re.match(r'\s*(```|~~~)', line)
        if fence:
            if mark and mark.group(1) == fence:
                fence = None
            continue
        if mark:
            fence = mark.group(1)
            continue
        head = re.match(r'#{1,6}\s+(.*)', line)
        if head:
            section = head.group(1).strip()
            continue
        if line.strip():
            out.append((section, line))
    return out


def norm(s):
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)  # link text only
    s = re.sub(r'[*_`]', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def sentences(text):
    out = []
    for _, line in blocks(text):
        line = re.sub(r'^\s*(?:>\s*)*(?:[-*+]|\d+[.)])\s+', '', line)
        out += [norm(p) for p in re.split(r'(?<=[.!?])["\')\]]?\s+(?=\S)', line) if norm(p)]
    return out


def section_words(text):
    words = {}
    for section, line in blocks(text):
        words[section] = words.get(section, 0) + len(PLACEHOLDER.sub(' ', line).split())
    return words


def overlap(a, b):
    wa, wb = set(re.findall(r'\w+', a.lower())), set(re.findall(r'\w+', b.lower()))
    return len(wa & wb) / max(1, min(len(wa), len(wb)))


def compare(orig, edited):
    a, b = sentences(orig), sentences(edited)
    cut, reworded, new, kept = [], [], [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == 'equal':
            kept += i2 - i1
            continue
        olds, used = a[i1:i2], set()
        for s in b[j1:j2]:
            # A piece of an original sentence (a split, or a cut clause) counts as reworded.
            best = max(((overlap(s, o), k) for k, o in enumerate(olds)), default=(0, None))
            if best[0] >= 0.5:
                reworded.append((olds[best[1]], s))
                used.add(best[1])
            else:
                new.append(s)
        cut += [o for k, o in enumerate(olds) if k not in used]
    before, after = section_words(orig), section_words(edited)
    grew = [(s, before.get(s, 0), n) for s, n in after.items() if n > before.get(s, 0)]
    return dict(kept=kept, cut=cut, reworded=reworded, new=new, grew=grew,
                words=(sum(before.values()), sum(after.values())))


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        orig, edited = (open(p, encoding='utf-8').read() for p in argv[1:])
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 2
    r = compare(orig, edited)
    print('words {0} -> {1}; sentences kept {2}, cut {3}, reworded {4}, NEW {5}'.format(
        *r['words'], r['kept'], len(r['cut']), len(r['reworded']), len(r['new'])))
    for s in r['cut']:
        print('cut:      ' + s)
    for o, s in r['reworded']:
        print('reworded: ' + s + '\n    from: ' + o)
    for s in r['new']:
        print('NEW:      ' + s)
    for s, n0, n1 in r['grew']:
        print('GREW:     section "{0}" {1} -> {2} words'.format(s, n0, n1))
    return 1 if r['grew'] else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
