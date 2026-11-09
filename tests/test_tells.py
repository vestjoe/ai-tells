"""
Checks for the Custom Vale style (this repo's own rules). Run with `python3 tests/test_tells.py` or `pytest`.

Needs vale on PATH, or VALE=/path/to/vale.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import namedtuple

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, 'vale.ini')
VALE = os.environ.get('VALE') or shutil.which('vale')

Alert = namedtuple('Alert', 'rule severity line col match')


def run(path, config=CONFIG):
    """vale's result for path. Exit 0 or 1 is a lint result; anything else is a broken style or config."""
    if not VALE:
        raise RuntimeError('vale not found; install it or set VALE=/path/to/vale')
    out = subprocess.run([VALE, '--config', config, '--output=JSON', path], capture_output=True, text=True)
    if out.returncode not in (0, 1):
        raise RuntimeError(out.stderr or out.stdout)
    return out


def lint(text):
    """Every Alert vale reports for text, as a Markdown file, in file order."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'doc.md')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)
        data = json.loads(run(path).stdout or '{}')
    return [Alert(a['Check'].split('.', 1)[1], a['Severity'], a['Line'], a['Span'][0], a['Match'])
            for alerts in data.values() for a in alerts]


def rules(text):
    return [a.rule for a in lint(text)]


def test_our_rules_are_named_custom():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'doc.md')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('Great question! We leverage robust tooling.\n')
        checks = {a['Check'] for alerts in json.loads(run(path).stdout).values() for a in alerts}
    assert checks and all(c.startswith('Custom.') for c in checks), checks


def test_catches_each_category():
    cases = {
        'FillerPraise': 'Great question! Here is the plan.',
        'FillerService': 'Run the script. I hope this helps.',
        'FillerCertainly': 'Certainly! The run passed.',
        'NotXButY': "It's not just about speed, but about trust.",
        'IsntAbout': "This isn't about speed. It's about trust.",
        'ColonReveal': 'The result? A faster build.',
        'RhetoricalAnswer': 'Why does it fail? Because the path is wrong.',
        'ProfoundCloser': 'We shipped it, and that changes everything.',
        'SummaryOpener': 'In summary, the build passed.',
        'Transition': 'Moreover, the test passed.',
        'ThisOpener': 'This means the build passed.',
        'Expletive': 'There are three steps.',
        'Preamble': "Let's dive in to the numbers.",
        'TellsReader': 'Volume fell, which shows the control works.',
        'Testament': 'It is a testament to the team.',
        'Importance': 'Coverage is crucial here.',
        'InflatedVerb': 'We leverage the cache.',
        'InflatedNoun': 'The security landscape moved.',
        'StockAdjective': 'A robust parser.',
        'Hedge': 'This is arguably the cause.',
        'VagueAttribution': 'Studies show the fix works.',
        'EmDash': 'The fix — a one-line change — landed.',
        'Passive': 'The file was written by the job.',
        'IngStack': 'We shipped it, adding tests for parsing, fixing the cache, and improving logs.',
        'EmailFiller': 'I hope this email finds you well. The faucet leaks.',
    }
    for rule, text in cases.items():
        assert rule in rules(text), (rule, rules(text))


def test_email_filler():
    for text in ['I hope you’re doing well.', 'I wanted to reach out about the lease.',
                 'Could a plumber come by at your earliest convenience?', 'I truly appreciate it.',
                 'That would be incredibly helpful.', 'Thank you so much for your time and consideration.',
                 'Please do not hesitate to call.']:
        assert 'EmailFiller' in rules(text), (text, rules(text))
    for text in ['The email finds its way to the inbox.', 'We reached the outer gate.', 'Thanks for fixing it.']:
        assert 'EmailFiller' not in rules(text), (text, rules(text))


def test_clean_prose_passes_the_full_config():
    out = subprocess.run([AUDIT, '--min=warning', os.path.join(HERE, 'sample_clean.md')], capture_output=True,
                         text=True)
    assert out.returncode == 0, out.stdout


def test_curly_apostrophes_match():
    assert 'IsntAbout' in rules('This isn’t about speed. It’s about trust.')
    assert 'ColonReveal' in rules('Here’s the thing: it works.')


def test_openers_at_any_sentence_start():
    assert 'SummaryOpener' in rules('Overall, the run passed.')
    assert 'SummaryOpener' in rules('The run passed. Ultimately, it shipped.')
    assert 'SummaryOpener' in rules('## Overall, the results\n')
    assert 'SummaryOpener' in rules('- *In summary*, it works.\n')
    assert 'Transition' in rules('- Moreover, the list item.')
    assert 'Transition' in rules('**Moreover**, the test passed.\n')
    assert 'Transition' in rules('1. Step\n\n    Moreover, the continuation.\n')


def test_openers_need_a_sentence_start():
    assert 'SummaryOpener' not in rules('The vector, as a whole,\nultimately, holds different types.\n')
    assert 'Transition' not in rules('We paid in addition to the fee.\n')


def test_tutorial_lets_is_a_suggestion():
    found = {a.rule: a.severity for a in lint("Let's explore the API. Let's take a look at it.")}
    assert found == {'LetsPreamble': 'suggestion'}, found
    assert 'Preamble' in rules('Let’s dive in.')


def test_shows_up_is_not_editorializing():
    assert 'TellsReader' not in rules('The plan has a cost. It shows up in the benchmarks.')


def test_literal_and_noun_uses_are_not_flagged():
    # False positives found on the 2019 Rust Book and the vale-ai-tells false-positive file.
    cases = [
        'The underscore, `_`, is a catchall value.',
        "The company's leverage in the negotiation was substantial.",
        'The financial leverage ratio was calculated quarterly.',
        'The climbing harness attaches at the shoulders.',
        'The embark terminal at the port was closed for repairs.',
        'Unlock the door before the alarm trips.',
        'The phone unlocks with a fingerprint.',
        'Unlocking the door needs a key.',
        'The plan has a cost. It shows up in the benchmarks.',
        'Sailors steer by the North Star.',
        'A map of the user journey documents the checkout flow.',
        'Crates.io is where people in the Rust ecosystem post their code.',
        'The vector, as a whole,\nultimately, holds different types.',
    ]
    fixed = {'InflatedVerb', 'InflatedNoun', 'TellsReader', 'SummaryOpener'}
    for text in cases:
        assert not fixed & set(rules(text)), (text, rules(text))


def test_figurative_uses_are_still_flagged():
    cases = {
        'InflatedVerb': ['We leverage the cache.', 'Teams must leverage robust tooling.', 'We harness logs.',
                         'This underscores the need for tests.', 'Leveraging AI helps.', 'Harness the power of logs.',
                         'We embark on a migration.', 'It unlocks new value.',
                         'Organizations harness distributed computing.'],
        'InflatedNoun': ['Latency is our north star.', 'Pick a north star metric.', 'A vibrant ecosystem grew.',
                         'The journey to production.'],
        'TellsReader': ['Volume fell, which shows the control works.'],
        'SummaryOpener': ['Ultimately, the run passed.', 'The run passed. Ultimately, it shipped.'],
    }
    for rule, texts in cases.items():
        for text in texts:
            assert rule in rules(text), (rule, text, rules(text))


def test_gated_noun_points_at_the_noun():
    found = [(a.col, a.match) for a in lint('We began our journey.') if a.rule == 'InflatedNoun']
    assert found == [(14, 'journey')], found


def test_document_signals():
    assert 'EmDashDensity' in rules('One — two — three.\n')
    triads = ' '.join('Use red, green, and blue.' for _ in range(5))
    assert 'RuleOfThree' in rules(triads)
    uniform = ' '.join('The build reads the file and writes a page.' for _ in range(14))
    assert 'UniformSentences' in rules(uniform)
    varied = ('Run it. The build reads the merged file, applies every override for the cut, and writes one page '
              'per recipe line. Then check. ') * 5
    assert 'UniformSentences' not in rules(varied)


def test_em_dash_density_points_at_the_paragraph():
    found = [a.line for a in lint('Plain.\n\n\n\nPlain again.\n\nA — b — c.\n') if a.rule == 'EmDashDensity']
    assert found == [7], found


def test_lists_of_three_in_code_do_not_count():
    code = '```\n' + 'red, green, and blue\n' * 5 + '```\n'
    assert 'RuleOfThree' not in rules('Plain text here.\n\n' + code)


def test_sentence_split_across_lines_is_flagged():
    cases = [
        'This sentence is\nbroken across lines.\n',
        'Rewording it, then\nre-wrapping it, costs time.\n',
        '- A list item that is\n  broken across lines.\n',
        '> A quote that is\n> broken across lines.\n',
        'Text.[^1]\n\n[^1]: A footnote that is\n    broken across lines.\n',
    ]
    for text in cases:
        assert 'SplitSentence' in rules(text), (text, rules(text))


def test_split_sentence_points_at_the_break():
    found = [(a.line, a.col, a.match) for a in lint('Plain line.\nIt’s wrapped — here\nand continues.\n')
             if a.rule == 'SplitSentence']
    assert found == [(2, 16, 'here')], found


def test_breaks_after_a_sentence_or_outside_prose_pass():
    cases = {
        'one sentence per line': 'One sentence.\nAnother sentence.\n',
        'other sentence ends': 'A question?\nYes. Wow!\nA label:\nthe value.\n',
        'closing marks': '*An emphasised sentence.*\n"A quoted sentence."\n(A bracketed one.)\nEnd.\n',
        'separate paragraphs': 'First paragraph\n\nSecond paragraph.\n',
        'list items': '- item one\n- item two\n1. step one\n2. step two\n',
        'heading': '# A heading\nText.\n',
        'table': '| a | b |\n| - | - |\n| 1 | 2 |\n',
        'fenced code': '```\ncode line\nmore code\n```\n',
        'indented code': 'Text.\n\n    code = 1\n    more = 2\n\nEnd.\n',
        'front matter': '---\ntitle: x\ntags: y\n---\nBody.\n',
        'html comment': '<!-- a comment\nthat wraps -->\nText.\n',
        'html block': '<div>\n<p>x</p>\n</div>\n',
        'hard break': 'Two trailing spaces  \nmake a line break.\nA backslash\\\ndoes too.\n',
        'reference definitions': '[a]: https://example.com\n[b]: https://example.org\n',
        'note marker': '> [!NOTE]\n> The note text.\n',
        'heading in a quote': '> ## A heading\n> Text.\n',
        'footnote after a sentence': 'It ended.[^1]\nNext sentence.\n',
    }
    for name, text in cases.items():
        assert 'SplitSentence' not in rules(text), (name, rules(text))


def test_clean_prose_has_no_findings():
    with open(os.path.join(HERE, 'sample_clean.md'), encoding='utf-8') as fh:
        found = lint(fh.read())
    assert found == [], found


def test_sample_with_tells_has_findings_in_every_category():
    with open(os.path.join(HERE, 'sample_tells.md'), encoding='utf-8') as fh:
        found = set(rules(fh.read()))
    for rule in ('FillerPraise', 'Preamble', 'NotXButY', 'Testament', 'InflatedVerb', 'StockAdjective', 'Transition',
                 'VagueAttribution', 'EmDash', 'Passive'):
        assert rule in found, (rule, sorted(found))


def test_ignores_code_links_and_comments():
    text = ('```\nleverage robust\n```\n'
            'Use `delve` here. See [docs](https://example.com/robust-landscape).\n'
            '<!-- seamless -->\n')
    assert lint(text) == [], lint(text)


def test_vale_comments_suppress_rules():
    assert rules('<!-- vale off -->\nA robust line.\n<!-- vale on -->\n') == []
    assert rules('<!-- vale Custom.StockAdjective = NO -->\nA robust line.\n'
                 '<!-- vale Custom.StockAdjective = YES -->\n') == []


def test_line_and_column_are_true_to_the_file():
    text = 'First line is plain.\n```\nleverage\n```\nWe leverage it.\n'
    found = [(a.line, a.col) for a in lint(text) if a.rule == 'InflatedVerb']
    assert found == [(5, 4)], found


def test_markdown_that_is_not_prose_is_ignored():
    cases = {
        'front matter list': '---\ntags: [leverage, robust]\n---\nBody text.\n',
        'indented code': 'Text.\n\n    leverage = robust\n\nMore text.\n',
        'double backtick code': 'Use ``a `robust` b`` here.\n',
        'html attributes': '<img alt="x" src="leverage.png">\n',
        'reference definition': 'See [docs][robust].\n\n[robust]: ./robust.md "Robust"\n',
        'indented fence': '- item\n  ```\n  leverage\n  ```\n',
    }
    for name, text in cases.items():
        assert rules(text) == [], (name, rules(text))


def test_front_matter_strings_are_prose():
    # A title or description is text a reader sees, so Vale checks string fields (lists are skipped).
    assert rules('---\ntitle: A robust guide\ntags: [leverage]\n---\nBody text.\n') == ['StockAdjective']
    assert rules('+++\ntitle = "A robust guide"\n+++\nBody text.\n') == ['StockAdjective']


def test_markdown_prose_is_still_checked():
    assert 'StockAdjective' in rules('- item\n\n    A robust continuation of the item.\n')
    assert 'StockAdjective' in rules('Text.[^1]\n\n[^1]: A robust footnote.\n')
    assert 'StockAdjective' in rules('---\n\nA robust line after a rule.\n')
    found = [(a.line, a.col) for a in lint('A **very** robust parser.\n') if a.rule == 'StockAdjective']
    assert found == [(1, 12)], found
    assert rules('Run 2 * 3 and keep snake_case_name.\n') == []


def test_exit_code_is_1_only_for_errors():
    sample = os.path.join(HERE, 'sample_tells.md')
    clean = os.path.join(HERE, 'sample_clean.md')
    assert run(sample).returncode == 1
    assert run(clean).returncode == 0


AUDIT = os.path.join(HERE, '..', 'skills', 'ai-tells-auditor', 'scripts', 'audit.sh')


def test_audit_script_runs_the_full_config():
    # Runs the skill's own .vale.ini (Custom plus the packs). Fetches the packs on first run.
    out = subprocess.run([AUDIT, os.path.join(HERE, 'sample_tells.md')], capture_output=True, text=True,
                         env=dict(os.environ, VALE=VALE or ''))
    assert out.returncode == 1, out.stderr
    assert 'Custom.FillerPraise' in out.stdout and 'ai-tells.' in out.stdout, out.stdout
    assert out.stdout.rstrip().splitlines()[-1].startswith('TOTAL: '), out.stdout


def test_audit_script_reports_a_missing_path():
    out = subprocess.run([AUDIT, os.path.join(HERE, 'no-such-file.md')], capture_output=True, text=True)
    assert out.returncode == 2 and 'No such file' in out.stderr, (out.returncode, out.stderr)


CHECK_EDIT = os.path.join(HERE, '..', 'skills', 'ai-tells-editor', 'scripts', 'check_edit.py')


def check_edit(orig, edited, notes=None):
    with tempfile.TemporaryDirectory() as d:
        names = ('orig.md', 'edited.md') + (('notes.md',) if notes is not None else ())
        paths = [os.path.join(d, n) for n in names]
        for p, text in zip(paths, (orig, edited, notes)):
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(text)
        return subprocess.run([sys.executable, CHECK_EDIT] + paths, capture_output=True, text=True)


def test_check_edit_lists_rewrites_without_failing():
    orig = '# Plan\n\nIn this section we cover the plan. The build runs nightly on two hosts. It leverages a robust cache.\n'
    edited = '# Plan\n\nThe build runs nightly on two hosts, and it uses a cache so each run starts warm.\n'
    out = check_edit(orig, edited)
    assert out.returncode == 0, out.stdout
    assert 'new facts 0' in out.stdout, out.stdout


def test_check_edit_flags_an_invented_number_name_and_quote():
    orig = 'The build runs nightly. Costs fell.\n'
    edited = 'The build runs nightly on 4 hosts. Costs fell, as Dana Ortiz said, "by half".\n'
    out = check_edit(orig, edited)
    assert out.returncode == 1, out.stdout
    for token in ('"4"', '"Dana"', '"Ortiz"', '"by half"'):
        assert 'FACT:     ' + token in out.stdout, (token, out.stdout)


def test_check_edit_checks_facts_against_the_notes_not_the_draft():
    notes = '- build runs nightly\n- two hosts\n'
    draft = 'The build runs nightly on two hosts, about 40 minutes each.\n'
    edited = 'The build runs nightly on two hosts, about 40 minutes each.\n'
    assert check_edit(draft, edited).returncode == 0
    out = check_edit(draft, edited, notes)
    assert out.returncode == 1 and 'FACT:     "40"' in out.stdout, out.stdout


def test_check_edit_ignores_placeholders_number_formats_and_sentence_starts():
    orig = 'The team ran 1,000 tests. Once that passed, they shipped.\n'
    edited = 'Once the team ran 1000 tests and [how many] passed, they shipped.\n'
    out = check_edit(orig, edited)
    assert out.returncode == 0 and 'new facts 0' in out.stdout, out.stdout


def test_check_edit_flags_changed_code():
    orig = 'Run this.\n\n```\nmake build\n```\n\nUse `--fast` when needed.\n'
    edited = 'Run this.\n\n```\nmake release\n```\n\nUse `--quick` when needed.\n'
    out = check_edit(orig, edited)
    assert out.returncode == 1 and out.stdout.count('FACT:') == 2, out.stdout


def test_check_edit_warns_but_passes_when_a_section_grows():
    out = check_edit('# A\n\nShort.\n', '# A\n\nShort, because the cache is warm.\n')
    assert out.returncode == 0 and 'GREW:     section "A" 1 -> 6 words' in out.stdout, out.stdout


def test_check_edit_checks_headings():
    out = check_edit('# Head\n\nText.\n', '# Head Dana 9\n\nText.\n')
    assert out.returncode == 1 and 'FACT:     "Dana"' in out.stdout and 'FACT:     "9"' in out.stdout, out.stdout
    out = check_edit('## Step 2 Acme\n\nIt ran.\n', '## Setup\n\nIt ran at Acme in step 2.\n')
    assert out.returncode == 0 and 'new facts 0' in out.stdout, out.stdout


def test_check_edit_flags_inline_code_containing_a_period_and_space():
    out = check_edit('Use it.\n', 'Use `a. b` here.\n')
    assert out.returncode == 1 and 'FACT:     "a. b"' in out.stdout, out.stdout


def test_check_edit_flags_a_fence_with_a_line_deleted():
    orig = 'Run:\n\n```\nmake clean\nmake build\n```\n'
    out = check_edit(orig, 'Run:\n\n```\nmake build\n```\n')
    assert out.returncode == 1 and 'FACT:     "make build"' in out.stdout, out.stdout
    assert check_edit(orig, orig).returncode == 0


def test_check_edit_flags_a_name_after_a_leading_quote():
    out = check_edit('Costs fell.\n', '"Costs fell," Dana said.\n')
    assert out.returncode == 1 and 'FACT:     "Dana"' in out.stdout, out.stdout


def test_check_edit_ignores_digits_in_placeholders_and_flags_unsourced_quotes():
    assert check_edit('It ran.\n', 'It ran [3 items].\n').returncode == 0
    out = check_edit('It ran.\n', 'It ran, "very well".\n')
    assert out.returncode == 1 and 'FACT:     "very well"' in out.stdout, out.stdout


def test_check_edit_treats_1000_and_1_000_as_one_number():
    assert check_edit('It had 1000 rows.\n', 'It had 1,000 rows.\n').returncode == 0
    assert check_edit('It had 1,000 rows.\n', 'It had 1000 rows.\n').returncode == 0


def test_check_edit_lists_a_new_sentence_start_without_failing():
    out = check_edit('The build runs nightly.\n', 'Dana says the build runs nightly. The build is fast.\n')
    assert out.returncode == 0 and 'new facts 0' in out.stdout, out.stdout
    assert 'CHECK:    "Dana"' in out.stdout and '"The"' not in out.stdout, out.stdout
    assert 'CHECK' not in check_edit('Dana runs it.\n', 'Dana runs it nightly.\n').stdout


def test_version_is_bumped_when_the_skill_changes():
    # Installed plugins update only when plugin.json's version changes. Skipped outside git or before the first tag.
    root = os.path.join(HERE, '..')
    git = lambda *a: subprocess.run(['git', '-C', root] + list(a), capture_output=True, text=True)
    tag = git('describe', '--tags', '--abbrev=0', '--match', 'v*').stdout.strip()
    if not tag:
        return
    with open(os.path.join(root, '.claude-plugin', 'plugin.json'), encoding='utf-8') as fh:
        version = json.load(fh)['version']
    changed = git('diff', '--quiet', tag, '--', 'skills/').returncode != 0
    assert not (changed and version == tag[1:]), (
        'skills/ changed since {0} but plugin.json is still {1}; bump the version'.format(tag, version))


def test_comparison_labels_resolve():
    # Each label in the Vale comparison corpus must quote text that appears exactly once in its file.
    sys.path.insert(0, os.path.join(HERE, '..', 'evals', 'compare'))
    import compare_linters
    try:
        labels = compare_linters.load_labels(os.path.join(HERE, '..', 'evals', 'compare', 'corpus', 'labels.json'))
    except SystemExit as exc:
        raise AssertionError(str(exc))
    assert len(labels) >= 90, len(labels)


VOICE_STATS = os.path.join(HERE, '..', 'skills', 'ai-tells-writer', 'scripts', 'voice_stats.py')


def voice_stats(text, *flags, name='sample.md'):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, name)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)
        return subprocess.run([sys.executable, VOICE_STATS] + list(flags) + [path], capture_output=True, text=True)


def test_voice_stats_counts_sentences_and_skips_code():
    text = ('# Setup\n\nWe build it nightly. Don\u2019t skip the check. Is it ready?\n\n'
            '```\nrm -rf build. make all. echo done.\n```\n\n- one item\n- two items\n')
    out = voice_stats(text, '--json')
    assert out.returncode == 0, out.stderr
    s = json.loads(out.stdout)
    assert s['sentences'] == 3, s            # three prose sentences; code and list items skipped
    assert s['question_share'] == 0.33, s
    assert s['contractions_per_100_words'] > 0, s   # curly apostrophe counts
    assert s['person_per_1000_words']['we'] > 0, s


def test_voice_stats_handles_an_empty_file():
    out = voice_stats('', '--json')
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout)['words'] == 0


def test_voice_stats_reports_a_missing_file():
    out = subprocess.run([sys.executable, VOICE_STATS, os.path.join(HERE, 'no-such-file.md')],
                         capture_output=True, text=True)
    assert out.returncode == 2, out.returncode


CHECK_VOICE = os.path.join(HERE, '..', 'skills', 'ai-tells-writer', 'scripts', 'check_voice.py')


def check_voice(profile, sample, *flags):
    with tempfile.TemporaryDirectory() as d:
        paths = [os.path.join(d, n) for n in ('profile.md', 'sample.md')]
        for p, text in zip(paths, (profile, sample)):
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(text)
        return subprocess.run([sys.executable, CHECK_VOICE] + list(flags) + paths, capture_output=True, text=True)


def test_check_voice_finds_a_copied_run_despite_case_and_punctuation():
    sample = 'Always write the rollback steps before the change window opens, and test them twice.\n'
    profile = '# Habits\n\nExample: always write the rollback steps, before the change window opens.\n'
    out = check_voice(profile, sample)
    assert out.returncode == 1, out.stdout
    assert 'COPIED: "always write the rollback steps before the change window opens"' in out.stdout, out.stdout
    assert out.stdout.rstrip().endswith('TOTAL: 1'), out.stdout


def test_check_voice_passes_short_shared_phrases():
    out = check_voice('Write the rollback steps first.\n', 'Always write the rollback steps before the window.\n')
    assert out.returncode == 0 and 'TOTAL: 0' in out.stdout, out.stdout


def test_check_voice_matches_curly_apostrophes():
    sample = 'Don\u2019t start the test until the team has signed the rules of the exercise.\n'
    profile = "Don't start the test until the team has signed the rules.\n"
    assert check_voice(profile, sample).returncode == 1


WRITER = os.path.join(HERE, '..', 'skills', 'ai-tells-writer')
PROFILE_SECTIONS = ['Summary', 'Numbers', 'Habits to keep', 'Habits to avoid', 'Person']


def test_plain_voice_has_the_profile_sections_in_order():
    with open(os.path.join(WRITER, 'voices', 'plain.md'), encoding='utf-8') as fh:
        heads = [l[3:].strip() for l in fh if l.startswith('## ')]
    assert heads == PROFILE_SECTIONS, heads


def test_plain_voice_copies_nothing_from_the_samples():
    out = subprocess.run([sys.executable, CHECK_VOICE, os.path.join(WRITER, 'voices', 'plain.md'),
                          os.path.join(HERE, 'sample_clean.md'), os.path.join(HERE, 'sample_tells.md')],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout


def test_writer_prose_passes_the_auditor():
    for rel in ('voices/plain.md', 'references/build-voice.md'):
        out = subprocess.run([AUDIT, '--min=warning', os.path.join(WRITER, rel)], capture_output=True, text=True,
                             env=dict(os.environ, VALE=VALE or ''))
        findings = [l for l in out.stdout.splitlines() if l[:1].isdigit()]   # finding lines start LINE:START-END
        assert out.returncode == 0 and not findings, (rel, findings)


SKILLS = os.path.join(HERE, '..', 'skills')
STANDARD = os.path.join(SKILLS, 'ai-tells-auditor', 'references', 'standard.md')


def test_standard_has_its_sections_and_passes_the_auditor():
    with open(STANDARD, encoding='utf-8') as fh:
        heads = [l[3:].strip() for l in fh if l.startswith('## ')]
    assert heads == ['The source', 'The voice', 'AI tells', 'Linked sentences'], heads
    out = subprocess.run([AUDIT, '--min=warning', STANDARD], capture_output=True, text=True, env=dict(os.environ, VALE=VALE or ''))
    assert out.returncode == 0 and not [l for l in out.stdout.splitlines() if l[:1].isdigit()], out.stdout


def frontmatter(path):
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    head = text.split('---', 2)[1]
    fields = dict(l.split(':', 1) for l in head.strip().splitlines() if ':' in l)
    return {k.strip(): v.strip() for k, v in fields.items()}, text


def test_every_skill_fits_claude_code_limits():
    for name in os.listdir(SKILLS):
        fields, text = frontmatter(os.path.join(SKILLS, name, 'SKILL.md'))
        assert fields['name'] == name, name
        assert len(fields['description']) < 1536, (name, len(fields['description']))
        assert len(text.splitlines()) < 500, name


def skill_text(name):
    return frontmatter(os.path.join(SKILLS, name, 'SKILL.md'))


LINK_RULE = "Don't split a connected sentence"


def test_auditor_reports_and_hands_fixes_to_the_editor():
    fields, text = skill_text('ai-tells-auditor')
    assert 'references/standard.md' in text
    assert '## Voice' in text and 'voice_stats.py' in text
    assert 'ai-tells-editor' in text
    assert 'Fix, when asked' not in text and LINK_RULE not in text


def test_editor_rewrites_against_the_standard():
    fields, text = skill_text('ai-tells-editor')
    assert 'standard.md' in text and 'new facts 0' in text
    assert "Don't reword" not in text and 'NEW 0' not in text and LINK_RULE not in text
    assert '[notes]' in fields['argument-hint'], fields
    assert 'python3 ${CLAUDE_SKILL_DIR}' not in text and '${CLAUDE_SKILL_DIR}/scripts/check_edit.py' in text


def test_writer_points_at_its_own_files():
    fields, text = frontmatter(os.path.join(WRITER, 'SKILL.md'))
    assert fields['allowed-tools'] == ('Bash(${CLAUDE_SKILL_DIR}/scripts/*) '
        'Bash(${CLAUDE_SKILL_DIR}/../ai-tells-auditor/scripts/*) Bash(${CLAUDE_SKILL_DIR}/../ai-tells-editor/scripts/*)'), fields
    assert '${CLAUDE_SKILL_DIR}/references/build-voice.md' in text
    assert '~/.claude/voices/' in text and 'standard.md' in text
    assert '.audit.md' in text and '.final.md' in text


def test_voice_stats_reads_a_word_export():
    # textutil output: one paragraph per line, tab-bullet items, headings and commands as bare lines.
    text = ('Chapter 1\nPlanning the Engagement\nWe start every test with a plan. The plan names the goal.\n'
            '\t\u2022\tRead the scope document\n\t\u2022\tConfirm the contacts\n'
            'nmap -sV -p 1-1000 10.0.0.0/24 -oA scan\n'
            'The team called this \u201cliving off the land.\u201d It means using what is already there.\n')
    s = json.loads(voice_stats(text, '--json').stdout)
    assert s['sentences'] == 4, s            # 2 + 2; list items, headings, and the command line skipped
    assert s['paragraph_median'] == 2, s


def test_voice_stats_leaves_layout_out():
    # Bullets are how a document is laid out, not how its writer writes. They don't count, and no list share is reported.
    text = 'We plan first. The plan names the goal.\n- Scope\n- Contacts\n- Dates\n'
    s = json.loads(voice_stats(text, '--json', name='notes.md').stdout)
    assert 'list_item_share' not in s, s
    assert s['sentences'] == 2, s
    assert s['sentence_median'] == 4, s


def test_voice_stats_reads_each_line_of_a_txt_file_as_a_paragraph():
    # Real textutil exports mix blank lines with paragraphs on adjacent lines.
    text = ('Heading\n\nFirst paragraph has one sentence.\nSecond paragraph has one sentence.\n\n'
            'Third paragraph. It has two sentences.\n')
    s = json.loads(voice_stats(text, '--json', name='book.txt').stdout)
    assert s['paragraph_median'] == 1, s
    s = json.loads(voice_stats(text, '--json', name='notes.md').stdout)
    assert s['paragraph_median'] == 2, s     # Markdown: blank lines separate paragraphs


def test_voice_stats_does_not_count_possessives_as_contractions():
    s = json.loads(voice_stats('The client\u2019s scope and the tester\u2019s plan. It\u2019s ready.\n', '--json').stdout)
    assert s['contractions_per_100_words'] == 11.11, s   # it's only: 1 in 9 words


def test_voice_stats_splits_and_finds_questions_inside_curly_quotes():
    s = json.loads(voice_stats('\u201cIs it ready?\u201d she asked. \u201cWhy?\u201d\n', '--json').stdout)
    assert s['sentences'] == 3 and s['question_share'] == 0.67, s


def test_check_voice_also_checks_fenced_text():
    sample = 'We always write the rollback steps before the change window opens and test them.\n'
    profile = '```text\nWe always write the rollback steps before the change window opens and test them.\n```\n'
    assert check_voice(profile, sample).returncode == 1


def test_build_steps_run_scripts_the_way_allowed_tools_approves():
    with open(os.path.join(WRITER, 'references', 'build-voice.md'), encoding='utf-8') as fh:
        text = fh.read()
    assert 'python3 ${CLAUDE_SKILL_DIR}' not in text
    assert '${CLAUDE_SKILL_DIR}/scripts/voice_stats.py' in text and '${CLAUDE_SKILL_DIR}/scripts/check_voice.py' in text


def test_rules_live_only_in_the_standard():
    for name in os.listdir(SKILLS):
        _, text = skill_text(name)
        assert LINK_RULE not in text and 'never add a number' not in text.lower(), name
        assert 'standard.md' in text, name


CAUSE_RULE = 'A link that states a cause or a result is a claim'


def test_the_cause_rule_lives_only_in_the_standard():
    with open(STANDARD, encoding='utf-8') as fh:
        assert CAUSE_RULE in fh.read()
    for name in os.listdir(SKILLS):
        _, text = skill_text(name)
        assert CAUSE_RULE not in text and "notes don't give is a new fact" not in text, name


def test_auditor_stops_at_the_report_when_another_skill_runs_it():
    _, text = skill_text('ai-tells-auditor')
    assert 'When another skill runs this one for the report only' in text
    _, text = skill_text('ai-tells-writer')
    assert 'Run it for the report only' in text


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print('PASS', t.__name__)
        except AssertionError as exc:
            failed += 1
            print('FAIL', t.__name__, exc)
    print('\n{0} failed'.format(failed) if failed else '\nAll passed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
