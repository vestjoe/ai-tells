#!/usr/bin/env python3
"""Compare an edited Markdown file with the original it came from.

    check_edit.py ORIGINAL EDITED [NOTES]

Prints what the edit did, sentence by sentence:
  cut        sentences in the original that are gone
  reworded   edited sentences paired with the original sentence they replace
  new        edited sentences with no original sentence behind them (informational)
  FACT       a number, name, quoted string, or code span in the edit that is not in
             the source, or a fenced code block that differs from the source
  GREW       a section (a heading starts one) with more words than before (a warning)
  CHECK      a capitalized word at the start of a sentence that the source doesn't have
             anywhere, in any case; it may be a new name (a warning: it doesn't change
             the exit code or the new facts count)
The source is NOTES when given, else ORIGINAL. Bracketed placeholders such as [source]
and link URLs are ignored. A capitalized word at the start of a sentence isn't a FACT,
since most are ordinary words; CHECK lists the ones the source lacks.

Known gaps:
  Numbers written as words aren't matched with digits, so "two" in the source doesn't
  cover "2" in the edit, and "2" in the source doesn't cover "two".
  An abbreviation ending in a period ends a sentence, so in "e.g. Foo" the word Foo
  counts as a sentence start and is never a FACT (CHECK can still list it).

Exit codes: 0 no new facts, 1 at least one new fact, 2 bad arguments or unreadable file.
"""

import difflib
import re
import sys

PLACEHOLDER = re.compile(r'\[[^\]]*\](?!\()')
FENCE = re.compile(r'^[ \t]*(```|~~~)[^\n]*\n(.*?)^[ \t]*\1[ \t]*$', re.S | re.M)
CODE = re.compile(r'`([^`\n]+)`')
QUOTE = re.compile(r'"([^"\n]+)"|\u201c([^\u201d\n]+)\u201d')
NUMBER = re.compile(r'\d[\d,.:%/-]*')
WORD = re.compile(r'[A-Za-z][A-Za-z0-9]*')


def blocks(text, headings=False):
    """(section, line) pairs for prose lines, skipping fenced code and front matter.
    With headings=True a heading's text is yielded too."""
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
            if headings:
                out.append((section, section))
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


def squash(s):
    return re.sub(r'\s+', ' ', s).strip()


def words_of(text):
    return {w.lower() for w in WORD.findall(re.sub(r"['\u2019]s\b", '', text))}


def blank(s, pattern, keep=None):
    """Replace each match with spaces of equal length; call keep(match) to collect it."""
    def sub(m):
        if keep:
            keep(m)
        return ' ' * len(m.group())
    return pattern.sub(sub, s)


def fact_tokens(sentence):
    """(kind, shown, key) for each fact in one sentence."""
    out = []
    first = WORD.search(sentence)  # the sentence start, decided before anything is masked
    start = first.start() if first else -1
    s = blank(sentence, CODE, lambda m: out.append(('code', m.group(1), m.group(1))))
    s = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', lambda m: ' ' + m.group(1) + ' ' * (len(m.group()) - len(m.group(1)) - 1), s)
    s = blank(s, PLACEHOLDER)
    s = blank(s, re.compile(r'https?://\S+'))
    def quote(m):
        q = squash(m.group(1) or m.group(2))
        out.append(('quote', q, q))
    s = blank(s, QUOTE, quote)
    for m in NUMBER.finditer(s):
        num = m.group().replace(',', '').rstrip('.:/-')
        if num:
            out.append(('number', num, num))
    for m in WORD.finditer(s):
        w = m.group()
        if m.start() != start and len(w) > 1 and w[0].isupper():
            out.append(('name', w, w.lower()))
    return out


def prose_sentences(text):
    """Raw sentences of the prose and heading lines, keeping Markdown so code spans survive."""
    out = []
    for _, line in blocks(text, headings=True):
        line = re.sub(r'^\s*(?:>\s*)*(?:[-*+]|\d+[.)])\s+', '', line)
        masked = blank(blank(line, CODE), QUOTE)  # no sentence break inside code or a quote
        pos = 0
        for m in re.finditer(r'(?<=[.!?])["\')\]]?\s+(?=\S)', masked):
            out.append(line[pos:m.start()])
            pos = m.end()
        out.append(line[pos:])
    return [p for p in out if p.strip()]


def fences(text):
    return [m.group(2).strip('\n') for m in FENCE.finditer(text)]


def facts(text):
    """Normalized fact tokens in text: numbers, quoted strings, code spans, names."""
    return {key for sent in prose_sentences(text) for _, _, key in fact_tokens(sent)}


def new_facts(source, edited):
    """(token, sentence) for each fact in edited that source lacks."""
    known, source_words, out = facts(source), words_of(source), []
    source_fences = set(fences(source))
    for sent in prose_sentences(edited):
        seen = set()
        for kind, shown, key in fact_tokens(sent):
            have = key in source_words if kind == 'name' else key in known
            if not have and (kind, key) not in seen:
                seen.add((kind, key))
                out.append((shown, norm(sent)))
    for body in fences(edited):
        if body not in source_fences:
            out.append((body.split('\n')[0].strip(), '(fenced code block)'))
    return out


def new_starts(source, edited):
    """(word, sentence) for each capitalized sentence-start word that source lacks."""
    source_words, out, seen = words_of(source), [], set()
    for sent in prose_sentences(edited):
        s = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', lambda m: ' ' + m.group(1) + ' ' * (len(m.group()) - len(m.group(1)) - 1), sent)
        s = blank(blank(blank(blank(s, CODE), PLACEHOLDER), re.compile(r'https?://\S+')), QUOTE)
        first = WORD.search(s)
        if not first:
            continue
        w = first.group()
        if len(w) > 1 and w[0].isupper() and w.lower() not in source_words and w.lower() not in seen:
            seen.add(w.lower())
            out.append((w, norm(sent)))
    return out


def main(argv):
    if len(argv) not in (3, 4):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        orig, edited, *notes = (open(p, encoding='utf-8').read() for p in argv[1:])
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 2
    r = compare(orig, edited)
    found = new_facts(notes[0] if notes else orig, edited)
    print('words {0} -> {1}; sentences kept {2}, cut {3}, reworded {4}, new {5}; new facts {6}'.format(
        *r['words'], r['kept'], len(r['cut']), len(r['reworded']), len(r['new']), len(found)))
    for s in r['cut']:
        print('cut:      ' + s)
    for o, s in r['reworded']:
        print('reworded: ' + s + '\n    from: ' + o)
    for s in r['new']:
        print('new:      ' + s)
    for token, s in found:
        print('FACT:     "{0}" in: {1}'.format(token, s))
    for s, n0, n1 in r['grew']:
        print('GREW:     section "{0}" {1} -> {2} words'.format(s, n0, n1))
    for w, s in new_starts(notes[0] if notes else orig, edited):
        print('CHECK:    "{0}" starts a sentence and is not in the source: {1}'.format(w, s))
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
