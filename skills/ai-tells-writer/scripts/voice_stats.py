#!/usr/bin/env python3
"""Measure writing samples for a voice profile.

    voice_stats.py [--json] FILE...

Reads every file as one sample and prints:
  words, sentences             totals
  sentence_median, _p90        words per sentence
  paragraph_median             sentences per paragraph
  question_share               share of sentences that are questions (0-1)
  contractions_per_100_words   don't, it's, we'll ...
  person_per_1000_words        I, we, and you, per 1,000 words

Front matter, fenced code, and short lines with no end punctuation (headings,
commands) are skipped. So are list items: bullets are how a document is laid
out, not how its writer writes, and they would drag the sentence numbers down.
In a .md file, blank lines separate paragraphs. In any other file, such as a
.txt export of a .docx, each line is one paragraph.

Exit codes: 0 done, 2 bad arguments or unreadable file.
"""

import json
import re
import statistics
import sys

LIST_ITEM = re.compile(r'\s*([-*+•◦▪–]|\d+[.)])\s+')
CLOSERS = '"\')]”»'
SENTENCE_END = re.compile(r'(?<=[.?!])[' + re.escape(CLOSERS) + r']*\s+')
WORD = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?")
# 's is a possessive unless the word before it is one of these.
CONTRACTION = re.compile(r"\b(\w+'(t|re|ve|ll|d|m)|(it|that|what|there|here|let|he|she|who|where|how)'s)\b", re.I)
HEADING_WORDS = 12   # a short line with no end punctuation is a heading, caption, or command, not prose
PERSON = {
    'i': {'i', "i'm", "i've", "i'll", "i'd", 'me', 'my', 'mine'},
    'we': {'we', "we're", "we've", "we'll", "we'd", 'us', 'our', 'ours'},
    'you': {'you', "you're", "you've", "you'll", "you'd", 'your', 'yours'},
}


def blocks(text, line_per_para=False):
    """(kind, text) for each paragraph or list item in one file.

    Skips front matter, fenced code, and short lines with no end punctuation
    (headings, captions, commands). With line_per_para, or in a file with no
    blank lines, each line is one paragraph, as in a textutil export of a .docx.
    """
    lines = text.lstrip('﻿').replace('’', "'").replace('‘', "'").splitlines()
    if lines and lines[0].strip() in ('---', '+++'):
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == lines[0].strip()), 0)
        lines = lines[end + 1:]
    line_per_para = line_per_para or (len(lines) > 1 and all(l.strip() for l in lines))
    out, para, fence = [], [], None

    def flush():
        if para:
            body = ' '.join(para)
            if len(body.split()) > HEADING_WORDS or body.rstrip()[-1:] in '.?!:' + CLOSERS:
                out.append(('para', body))
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
        if line_per_para:
            flush()
    flush()
    return out


def sentences(block_text):
    return [s.strip() for s in SENTENCE_END.split(block_text) if WORD.search(s)]


def percentile(values, p):
    if not values:
        return 0
    values = sorted(values)
    return values[min(len(values) - 1, int(round(p * (len(values) - 1))))]


def stats(*files):
    """Numbers for one or more files, each a (text, line_per_para) pair split into blocks on its own."""
    paras = [body for text, line_mode in files for kind, body in blocks(text, line_mode) if kind == 'para']
    sents, per_para = [], []
    for body in paras:
        ss = sentences(body)
        sents.extend(ss)
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
        'question_share': round(sum(s.rstrip(CLOSERS).endswith('?') for s in sents) / len(sents), 2) if sents else 0,
        'contractions_per_100_words': per(sum(len(CONTRACTION.findall(s)) for s in sents), 100),
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
                texts.append((fh.read(), not p.lower().endswith(('.md', '.markdown'))))
        except OSError as exc:
            print(exc, file=sys.stderr)
            return 2
    result = stats(*texts)
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
