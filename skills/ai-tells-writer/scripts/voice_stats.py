#!/usr/bin/env python3
"""Measure writing samples for a voice profile.

    voice_stats.py [--json] FILE...

Reads every file as one sample and prints:
  words, sentences             totals
  sentence_median, _p90        words per sentence
  paragraph_median             sentences per paragraph
  question_share               share of sentences that are questions (0-1)
  contractions_per_100_words   don't, it's, we'll ...
  list_item_share              list items as a share of all blocks (0-1)
  person_per_1000_words        I, we, and you, per 1,000 words

Front matter and fenced code are skipped. Each list item counts as one block
and one sentence.

Exit codes: 0 done, 2 bad arguments or unreadable file.
"""

import json
import re
import statistics
import sys

LIST_ITEM = re.compile(r'\s*([-*+]|\d+[.)])\s+')
SENTENCE_END = re.compile(r'(?<=[.?!])["\')\]]*\s+')
WORD = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?")
CONTRACTION = re.compile(r"\b\w+'(s|t|re|ve|ll|d|m)\b", re.I)
PERSON = {
    'i': {'i', "i'm", "i've", "i'll", "i'd", 'me', 'my', 'mine'},
    'we': {'we', "we're", "we've", "we'll", "we'd", 'us', 'our', 'ours'},
    'you': {'you', "you're", "you've", "you'll", "you'd", 'your', 'yours'},
}


def blocks(text):
    """(kind, text) for each paragraph or list item, skipping front matter and fenced code."""
    lines = text.replace('’', "'").replace('‘', "'").splitlines()
    if lines and lines[0].strip() in ('---', '+++'):
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == lines[0].strip()), 0)
        lines = lines[end + 1:]
    out, para, fence = [], [], None

    def flush():
        if para:
            out.append(('para', ' '.join(para)))
            para.clear()

    for line in lines:
        mark = re.match(r'\s*(```|~~~)', line)
        if fence:
            if mark and mark.group(1) == fence:
                fence = None
            continue
        if mark:
            flush()
            fence = mark.group(1)
            continue
        if not line.strip() or re.match(r'#{1,6}\s', line) or line.lstrip().startswith('|'):
            flush()
            continue
        item = LIST_ITEM.match(line)
        if item:
            flush()
            out.append(('item', line[item.end():].strip()))
            continue
        para.append(line.strip())
    flush()
    return out


def sentences(block_text):
    return [s.strip() for s in SENTENCE_END.split(block_text) if WORD.search(s)]


def percentile(values, p):
    if not values:
        return 0
    values = sorted(values)
    return values[min(len(values) - 1, int(round(p * (len(values) - 1))))]


def stats(text):
    bl = blocks(text)
    sents, per_para = [], []
    for kind, body in bl:
        ss = [body] if kind == 'item' else sentences(body)
        sents.extend(ss)
        if kind == 'para':
            per_para.append(len(ss))
    lengths = [len(WORD.findall(s)) for s in sents]
    words = [w.lower() for s in sents for w in WORD.findall(s)]
    n = len(words)
    per = lambda count, scale: round(count * scale / n, 2) if n else 0
    return {
        'words': n,
        'sentences': len(sents),
        'sentence_median': round(statistics.median(lengths), 2) if lengths else 0,
        'sentence_p90': percentile(lengths, 0.9),
        'paragraph_median': round(statistics.median(per_para), 2) if per_para else 0,
        'question_share': round(sum(s.rstrip('"\')]').endswith('?') for s in sents) / len(sents), 2) if sents else 0,
        'contractions_per_100_words': per(sum(len(CONTRACTION.findall(s)) for s in sents), 100),
        'list_item_share': round(sum(k == 'item' for k, _ in bl) / len(bl), 2) if bl else 0,
        'person_per_1000_words': {k: per(sum(w in forms for w in words), 1000) for k, forms in PERSON.items()},
    }


def main(argv):
    as_json = '--json' in argv
    paths = [a for a in argv if a != '--json']
    if not paths or any(p.startswith('-') for p in paths):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    texts = []
    for p in paths:
        try:
            with open(p, encoding='utf-8') as fh:
                texts.append(fh.read())
        except OSError as exc:
            print(exc, file=sys.stderr)
            return 2
    result = stats('\n\n'.join(texts))
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        for k, v in result.items():
            if isinstance(v, dict):
                v = ', '.join('{0}={1}'.format(a, b) for a, b in v.items())
            print('{0}: {1}'.format(k, v))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
