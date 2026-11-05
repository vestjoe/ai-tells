"""
Compare Vale configs on a hand-labeled corpus of AI tells and a corpus of human prose.

    python3 evals/compare/compare_linters.py            # summary tables
    python3 evals/compare/compare_linters.py --detail   # plus which config caught each label
    python3 evals/compare/compare_linters.py --json out.json

For each config it reports:
- recall: the share of labeled tells that at least one alert overlaps (mechanics rules in INCIDENTAL don't count);
- the same at error level only, which is all that Vale's edit hook and /vale:fix act on by default;
- noise: alerts per 1,000 words on the clean corpus, where every alert is unwanted.

Needs vale on PATH (or VALE=/path/to/vale) and the packs synced into skills/ai-tells-auditor/styles
(running skills/ai-tells-auditor/scripts/audit.sh once does that).
"""

import argparse
import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SKILL_INI = os.path.join(ROOT, 'skills', 'ai-tells-auditor', '.vale.ini')
STYLES = os.path.join(ROOT, 'skills', 'ai-tells-auditor', 'styles')
VALE = os.environ.get('VALE') or shutil.which('vale')


def skill_ini(with_custom=True):
    with open(SKILL_INI, encoding='utf-8') as fh:
        text = fh.read()
    text = re.sub(r'^StylesPath = .*$', 'StylesPath = ' + STYLES, text, count=1, flags=re.M)
    if not with_custom:
        text, n = re.subn(r'^(BasedOnStyles = )Custom, ', r'\1', text, flags=re.M)
        assert n == 1, 'expected "BasedOnStyles = Custom, ..." in ' + SKILL_INI
    return text


def plain_ini(styles):
    return 'StylesPath = {0}\nMinAlertLevel = suggestion\n\n[*.md]\nBasedOnStyles = {1}\n'.format(STYLES, styles)


# Packs come from the skill's styles folder, so every config uses the same pinned pack versions.
CONFIGS = [
    ('vale-setup', 'What /vale:setup writes by default: Vale, Microsoft.', lambda: plain_ini('Vale, Microsoft')),
    ('vale-setup+ai-tells', 'The default plus the vale-ai-tells pack, nothing tuned.',
     lambda: plain_ini('Vale, Microsoft, ai-tells')),
    ('all-packs-untuned', "The skill's five packs plus Vale's own style, nothing turned off.",
     lambda: plain_ini('Vale, ai-tells, proselint, write-good, Microsoft, Google')),
    ('skill-without-Custom', "The skill's .vale.ini with the Custom style removed.", lambda: skill_ini(False)),
    ('this-skill', "The skill's .vale.ini as shipped.", lambda: skill_ini(True)),
]

LEVELS = {'suggestion': 0, 'warning': 1, 'error': 2}

# Rules about mechanics: pronouns, contractions, punctuation marks, spacing, spelling, "to be". They overlap a tell
# only by accident ("I" in "I wanted to reach out", the "!" in "Happy formatting!"), and fixing the alert leaves the
# tell in place, so they don't count toward recall. They still count as noise on the clean corpus.
INCIDENTAL = {
    'Vale.Spelling', 'Microsoft.Contractions', 'Google.Contractions', 'Microsoft.We', 'Google.We',
    'Microsoft.FirstPerson', 'Google.FirstPerson', 'Microsoft.ExclamationPoints', 'Google.Exclamation',
    'Microsoft.QuestionMarks', 'Microsoft.Dashes', 'Google.EmDash', 'Microsoft.Adverbs', 'write-good.E-Prime',
}


def load_labels(path):
    with open(path, encoding='utf-8') as fh:
        data = json.load(fh)
    labels, seen = data['labels'], set(data.get('seen_files', []))
    out = []
    for lab in labels:
        f = os.path.join(ROOT, lab['file'])
        with open(f, encoding='utf-8') as fh:
            lines = fh.read().split('\n')
        hits = [(i + 1, line.index(lab['quote'])) for i, line in enumerate(lines) if lab['quote'] in line]
        count = sum(line.count(lab['quote']) for line in lines)
        if count != 1:
            sys.exit('label quote must appear exactly once in {0}: {1!r} (found {2})'.format(lab['file'], lab['quote'],
                                                                                          count))
        line, start = hits[0]
        out.append(dict(lab, path=f, line=line, start=start + 1, end=start + len(lab['quote']), seen=lab['file'] in seen))
    return out


def lint(ini_text, paths):
    """Every alert for paths: dicts with path, line, start, end, check, severity."""
    with tempfile.TemporaryDirectory() as d:
        ini = os.path.join(d, 'vale.ini')
        with open(ini, 'w', encoding='utf-8') as fh:
            fh.write(ini_text)
        out = subprocess.run([VALE, '--config', ini, '--output=JSON', '--no-exit'] + paths, capture_output=True,
                             text=True)
    if out.returncode != 0:
        sys.exit(out.stderr or out.stdout)
    data = json.loads(out.stdout or '{}')
    return [dict(path=os.path.abspath(p), line=a['Line'], start=a['Span'][0], end=a['Span'][1], check=a['Check'],
                 severity=a['Severity']) for p, alerts in data.items() for a in alerts]


def words(path):
    with open(path, encoding='utf-8') as fh:
        return len(fh.read().split())


def overlaps(alert, lab):
    return alert['path'] == lab['path'] and alert['line'] == lab['line'] and alert['start'] <= lab['end'] and \
        alert['end'] >= lab['start']


def score(alerts, labels, clean_paths, clean_words, min_level):
    alerts = [a for a in alerts if LEVELS[a['severity']] >= LEVELS[min_level]]
    clean = set(clean_paths)
    tells = [a for a in alerts if a['path'] not in clean]
    noise = [a for a in alerts if a['path'] in clean]
    counted = [a for a in tells if a['check'] not in INCIDENTAL]
    caught = [lab for lab in labels if any(overlaps(a, lab) for a in counted)]
    on_label = [a for a in counted if any(overlaps(a, lab) for lab in labels)]
    unseen = [lab for lab in labels if not lab['seen']]
    return {
        'recall': len(caught) / len(labels),
        'recall_unseen': sum(1 for lab in caught if not lab['seen']) / len(unseen) if unseen else None,
        'caught_unseen': sum(1 for lab in caught if not lab['seen']),
        'caught': len(caught),
        'caught_labels': [(lab['file'], lab['quote']) for lab in caught],
        'tells_alerts': len(tells),
        'tells_alerts_off_label': len(tells) - len(on_label),
        'clean_alerts': len(noise),
        'clean_per_1k_words': 1000.0 * len(noise) / clean_words,
        'clean_top_rules': collections.Counter(a['check'] for a in noise).most_common(5),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--labels', default=os.path.join(HERE, 'corpus', 'labels.json'))
    ap.add_argument('--clean', default=os.path.join(HERE, 'corpus', 'clean'),
                    help='folder of human-written .md files; every alert on them counts as noise')
    ap.add_argument('--detail', action='store_true', help='show which configs caught each label')
    ap.add_argument('--json', metavar='PATH', help='also write the full results as JSON')
    args = ap.parse_args()

    if not VALE:
        sys.exit('vale not found; install it or set VALE=/path/to/vale')
    if not os.path.isdir(os.path.join(STYLES, 'ai-tells')):
        sys.exit('packs not synced; run skills/ai-tells-auditor/scripts/audit.sh once first')

    labels = load_labels(args.labels)
    tell_paths = sorted({lab['path'] for lab in labels})
    clean_paths = sorted(os.path.join(args.clean, f) for f in os.listdir(args.clean)
                         if f.endswith('.md') and f != 'SOURCES.md')
    clean_paths = [os.path.abspath(p) for p in clean_paths]
    clean_words = sum(words(p) for p in clean_paths)

    results = {}
    for name, about, make in CONFIGS:
        alerts = lint(make(), tell_paths + clean_paths)
        results[name] = {'about': about, 'all': score(alerts, labels, clean_paths, clean_words, 'suggestion'),
                         'error': score(alerts, labels, clean_paths, clean_words, 'error')}

    unseen = sum(1 for lab in labels if not lab['seen'])
    print('Corpus: {0} labeled tells in {1} files ({2} in files the rules have not seen); {3} clean files, '
          '{4:,} words.\n'.format(len(labels), len(tell_paths), unseen, len(clean_paths), clean_words))
    print('| Config | Recall | Recall, unseen files | Recall, errors only | Alerts on tell files (not on a label) '
          '| Noise per 1k clean words |')
    print('| --- | --- | --- | --- | --- | --- |')
    for name, _, _ in CONFIGS:
        r, e = results[name]['all'], results[name]['error']
        print('| {0} | {1:.0%} ({2}) | {3:.0%} ({4}) | {5:.0%} ({6}) | {7} ({8}) | {9:.1f} |'.format(
            name, r['recall'], r['caught'], r['recall_unseen'] or 0, r['caught_unseen'], e['recall'], e['caught'],
            r['tells_alerts'], r['tells_alerts_off_label'], r['clean_per_1k_words']))
    print('\nConfigs:\n')
    for name, about, _ in CONFIGS:
        print('- {0}: {1}'.format(name, about))

    print('\nRecall by category (all levels):\n')
    cats = sorted({lab['category'] for lab in labels})
    print('| Category | Labels | ' + ' | '.join(n for n, _, _ in CONFIGS) + ' |')
    print('| --- | --- |' + ' --- |' * len(CONFIGS))
    for c in cats:
        mine = [(lab['file'], lab['quote']) for lab in labels if lab['category'] == c]
        cells = [str(sum(1 for m in mine if m in results[n]['all']['caught_labels'])) for n, _, _ in CONFIGS]
        print('| {0} | {1} | {2} |'.format(c, len(mine), ' | '.join(cells)))

    print('\nTop noise rules on the clean corpus:\n')
    for name, _, _ in CONFIGS:
        top = ', '.join('{0} {1}'.format(k, n) for k, n in results[name]['all']['clean_top_rules']) or 'none'
        print('- {0}: {1}'.format(name, top))

    if args.detail:
        print('\nPer label (x = caught at any level):\n')
        print('| File | Quote | ' + ' | '.join(n for n, _, _ in CONFIGS) + ' |')
        print('| --- | --- |' + ' --- |' * len(CONFIGS))
        for lab in labels:
            key = (lab['file'], lab['quote'])
            cells = ['x' if key in results[n]['all']['caught_labels'] else '' for n, _, _ in CONFIGS]
            print('| {0} | {1} | {2} |'.format(os.path.basename(lab['file']), lab['quote'].replace('|', '\\|'),
                                               ' | '.join(cells)))

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as fh:
            json.dump({'labels': len(labels), 'clean_words': clean_words, 'configs': results}, fh, indent=2)
    return 0


if __name__ == '__main__':
    sys.exit(main())
