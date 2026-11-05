"""
Set up a with-model comparison: this skill vs. Vale's plugin (vale-cli/agent-tools), on evals/evals.json.

    git clone https://github.com/vale-cli/agent-tools /path/to/agent-tools
    python3 evals/compare/model/prepare_runs.py --vale-tools /path/to/agent-tools [--vale-config skill|setup]
        [--runs 3] [--out ai-tells-auditor-workspace/compare-1]

Writes, per eval, arm and run:

    <out>/eval-<id>-<name>/<arm>/run-<n>/
        project/   a git repo holding the eval's input files (and, for the Vale arm, a .vale.ini)
        outputs/   where the executor saves reply.md and log.md
        brief.md   the full prompt to hand an executor subagent

Arms:
    ai-tells-auditor  this repo's skill, read from skills/ai-tells-auditor/SKILL.md
    vale-plugin       Vale's five skills and its edit hook, with .vale.ini set by --vale-config:
                        skill  this skill's own .vale.ini (Custom rules, packs, tuning). Tests whether
                               the SKILL.md and judgment pass add anything over Vale's skills.
                        setup  what /vale:setup writes by default (Vale, Microsoft).

Then spawn one executor subagent per brief.md, and run grade.py.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SKILL = os.path.join(ROOT, 'skills', 'ai-tells-auditor')
STYLES = os.path.join(SKILL, 'styles')

SETUP_INI = 'StylesPath = {0}\nMinAlertLevel = suggestion\n\n[*.md]\nBasedOnStyles = Vale, Microsoft\n'

COMMON = """You are standing in for Claude Code, working for a user in their repository. Behave exactly as you would
for a real user; this is a test, but the user doesn't know that and nothing below should change how you answer.

Working directory: {project}
Run every command from there. Don't read or change anything outside {project} and {outputs}, except the
skill and plugin files named below.

{tools}

When you're done:
1. Save your final reply to the user, exactly as you would send it, to {outputs}/reply.md.
2. Save a short log of what you did (commands run, files read, files changed) to {outputs}/log.md.

The user's message follows between the markers.

<<<USER
{prompt}
USER>>>
"""

SKILL_TOOLS = """Installed skills (the only ones; ignore any other copy of ai-tells-auditor you may see, including
through the Skill tool, and don't use any other skill):

- ai-tells-auditor: {description}
  Location: {skill}/SKILL.md. Read it when it applies and follow it; its own files are in {skill}."""

VALE_TOOLS = """Installed plugin: vale (github.com/vale-cli/agent-tools, commit {commit}). These are its skills, and
the only ones installed; ignore any ai-tells-auditor skill you may see, including through the Skill tool:

{skills}

Read a skill's SKILL.md when it applies and follow it. The project already has a .vale.ini, so Vale is set up.

The plugin also installs a PostToolUse hook on Edit and Write. Since hooks don't run here, run it yourself after
every Edit or Write to a file in the project, and treat anything it prints as feedback from the hook:

    printf '{{"tool_input":{{"file_path":"%s"}}}}' "<absolute path of the file>" | sh {tools}/hooks/vale-edit.sh

The project is a git repository with no remote, so you can branch and commit but can't push or open a pull
request; say what you would have opened instead."""


def frontmatter(path):
    with open(path, encoding='utf-8') as fh:
        m = re.match(r'---\n(.*?)\n---\n', fh.read(), re.S)
    fields = dict(re.findall(r'^(\w+): (.*)$', m.group(1), re.M))
    return fields['name'], fields['description']


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:40]


def git(cwd, *args):
    subprocess.run(['git', '-C', cwd] + list(args), check=True, capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME='eval', GIT_AUTHOR_EMAIL='eval@example.com',
                            GIT_COMMITTER_NAME='eval', GIT_COMMITTER_EMAIL='eval@example.com'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--vale-tools', required=True, help='a checkout of github.com/vale-cli/agent-tools')
    ap.add_argument('--vale-config', choices=['skill', 'setup'], default='skill')
    ap.add_argument('--runs', type=int, default=3)
    ap.add_argument('--out', default=os.path.join(ROOT, 'ai-tells-auditor-workspace', 'compare-1'))
    ap.add_argument('--evals', default=os.path.join(ROOT, 'evals', 'evals.json'))
    args = ap.parse_args()
    args.out = os.path.abspath(args.out)

    tools = os.path.abspath(args.vale_tools)
    if not os.path.isfile(os.path.join(tools, 'hooks', 'vale-edit.sh')):
        sys.exit('not an agent-tools checkout: ' + tools)
    if not os.path.isdir(os.path.join(STYLES, 'ai-tells')):
        sys.exit('packs not synced; run skills/ai-tells-auditor/scripts/audit.sh once first')
    if os.path.exists(args.out):
        sys.exit('already exists: ' + args.out)
    commit = subprocess.run(['git', '-C', tools, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()

    _, skill_desc = frontmatter(os.path.join(SKILL, 'SKILL.md'))
    vale_skills = []
    for d in sorted(os.listdir(os.path.join(tools, 'skills'))):
        path = os.path.join(tools, 'skills', d, 'SKILL.md')
        if os.path.isfile(path):
            name, desc = frontmatter(path)
            vale_skills.append('- vale:{0}: {1}\n  Location: {2}'.format(name, desc, path))

    with open(os.path.join(SKILL, '.vale.ini'), encoding='utf-8') as fh:
        skill_ini = re.sub(r'^StylesPath = .*$', 'StylesPath = ' + STYLES, fh.read(), count=1, flags=re.M)
    vale_ini = skill_ini if args.vale_config == 'skill' else SETUP_INI.format(STYLES)

    with open(args.evals, encoding='utf-8') as fh:
        evals = json.load(fh)['evals']

    briefs = []
    for ev in evals:
        what = os.path.splitext(os.path.basename(ev['files'][0]))[0] if ev['files'] else 'pasted-text'
        name = 'eval-{0}-{1}'.format(ev['id'], slug(what))
        eval_dir = os.path.join(args.out, name)
        os.makedirs(eval_dir)
        with open(os.path.join(eval_dir, 'eval_metadata.json'), 'w', encoding='utf-8') as fh:
            json.dump({'eval_id': ev['id'], 'eval_name': name, 'prompt': ev['prompt'], 'files': ev['files'],
                       'assertions': ev['assertions']}, fh, indent=2)
        for arm in ('ai-tells-auditor', 'vale-plugin'):
            for n in range(1, args.runs + 1):
                run = os.path.join(eval_dir, arm, 'run-{0}'.format(n))
                project, outputs = os.path.join(run, 'project'), os.path.join(run, 'outputs')
                os.makedirs(outputs)
                os.makedirs(project)
                for f in ev['files']:
                    os.makedirs(os.path.join(project, os.path.dirname(f)), exist_ok=True)
                    shutil.copy(os.path.join(ROOT, f), os.path.join(project, f))
                if arm == 'vale-plugin':
                    with open(os.path.join(project, '.vale.ini'), 'w', encoding='utf-8') as fh:
                        fh.write(vale_ini)
                    tool_text = VALE_TOOLS.format(commit=commit, skills='\n'.join(vale_skills), tools=tools)
                else:
                    tool_text = SKILL_TOOLS.format(description=skill_desc, skill=SKILL)
                git(project, 'init', '-q', '-b', 'main')
                git(project, 'add', '-A')
                git(project, 'commit', '-q', '--allow-empty', '-m', 'initial')
                brief = COMMON.format(project=project, outputs=outputs, tools=tool_text, prompt=ev['prompt'])
                with open(os.path.join(run, 'brief.md'), 'w', encoding='utf-8') as fh:
                    fh.write(brief)
                briefs.append(os.path.relpath(os.path.join(run, 'brief.md'), ROOT))

    with open(os.path.join(args.out, 'setup.json'), 'w', encoding='utf-8') as fh:
        json.dump({'vale_tools_commit': commit, 'vale_config': args.vale_config, 'runs': args.runs,
                   'briefs': briefs}, fh, indent=2)
    print('\n'.join(briefs))
    return 0


if __name__ == '__main__':
    sys.exit(main())
