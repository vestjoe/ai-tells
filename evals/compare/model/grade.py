"""
Blind grading for a workspace made by prepare_runs.py.

    python3 evals/compare/model/grade.py blind <workspace>     # after the executors finish
    # ...one grader subagent per <workspace>/blind/<id>/, each writing grading.json there...
    python3 evals/compare/model/grade.py collect <workspace>   # copy grades back, then aggregate

`blind` copies each run's reply, log, and file diff into <workspace>/blind/<random id>/ with the arm's name and
paths redacted, plus checks.json with the facts a script can settle (was each input file changed, are its code
blocks byte-identical). The id-to-run map stays in <workspace>/blind_map.json, which graders mustn't read.
A reply can still give its arm away by how it works ("opened a branch per file"), so this is blind to names,
not to style.
"""

import json
import os
import random
import re
import shutil
import subprocess
import sys

REDACT = [r'ai-tells-auditor', r'ai-tells', r'vale:(setup|fix|triage|vocab|ci)', r'agent-tools', r'vale-edit\.sh',
          r'vale-plugin']


def runs(ws):
    for ev in sorted(os.listdir(ws)):
        meta = os.path.join(ws, ev, 'eval_metadata.json')
        if not os.path.isfile(meta):
            continue
        for arm in sorted(os.listdir(os.path.join(ws, ev))):
            arm_dir = os.path.join(ws, ev, arm)
            if not os.path.isdir(arm_dir):
                continue
            for run in sorted(os.listdir(arm_dir)):
                if run.startswith('run-'):
                    yield meta, arm, os.path.join(arm_dir, run)


def fences(text):
    return re.findall(r'^```.*?^```', text, re.S | re.M)


def redact(text, run):
    text = text.replace(run, '<run>')
    for pat in REDACT:
        text = re.sub(pat, '[skill]', text, flags=re.I)
    return text


def read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read()
    except FileNotFoundError:
        return ''


def blind(ws):
    items = list(runs(ws))
    ids = random.sample(range(1000, 10000), len(items))
    mapping = {}
    out = os.path.join(ws, 'blind')
    os.makedirs(out)
    for (meta_path, arm, run), i in zip(items, ids):
        with open(meta_path, encoding='utf-8') as fh:
            meta = json.load(fh)
        project = os.path.join(run, 'project')
        checks = {}
        for f in meta['files']:
            before = subprocess.run(['git', '-C', project, 'show', 'main:' + f], capture_output=True,
                                    text=True).stdout
            after = read(os.path.join(project, f))
            checks[f] = {'changed': before != after, 'code_blocks_identical': fences(before) == fences(after),
                         'branches': subprocess.run(['git', '-C', project, 'branch', '--format=%(refname:short)'],
                                                    capture_output=True, text=True).stdout.split()}
        diff = subprocess.run(['git', '-C', project, 'diff', 'main', '--'] + meta['files'], capture_output=True,
                              text=True).stdout if meta['files'] else ''
        d = os.path.join(out, str(i))
        os.makedirs(d)
        for name, text in [('reply.md', read(os.path.join(run, 'outputs', 'reply.md'))),
                           ('log.md', read(os.path.join(run, 'outputs', 'log.md'))),
                           ('diff.patch', diff)]:
            with open(os.path.join(d, name), 'w', encoding='utf-8') as fh:
                fh.write(redact(text, run))
        for f in meta['files']:
            dest = os.path.join(d, 'final', f)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy(os.path.join(project, f), dest)
        with open(os.path.join(d, 'task.json'), 'w', encoding='utf-8') as fh:
            json.dump({'prompt': meta['prompt'], 'input_files': meta['files'], 'checks': checks,
                       'expectations': meta['assertions']}, fh, indent=2)
        mapping[str(i)] = os.path.relpath(run, ws)
    with open(os.path.join(ws, 'blind_map.json'), 'w', encoding='utf-8') as fh:
        json.dump(mapping, fh, indent=2)
    print('\n'.join(os.path.join(out, k) for k in sorted(mapping)))


def collect(ws):
    with open(os.path.join(ws, 'blind_map.json'), encoding='utf-8') as fh:
        mapping = json.load(fh)
    missing = []
    for i, rel in mapping.items():
        src = os.path.join(ws, 'blind', i, 'grading.json')
        if not os.path.isfile(src):
            missing.append(i)
            continue
        shutil.copy(src, os.path.join(ws, rel, 'grading.json'))
    if missing:
        sys.exit('no grading.json yet for: ' + ', '.join(missing))
    print('Copied {0} grades. Aggregate with skill-creator:\n  cd <skill-creator dir> && python3 -m '
          'scripts.aggregate_benchmark {1} --skill-name ai-tells-auditor'.format(len(mapping), os.path.abspath(ws)))


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('blind', 'collect'):
        sys.exit(__doc__)
    (blind if sys.argv[1] == 'blind' else collect)(sys.argv[2])
