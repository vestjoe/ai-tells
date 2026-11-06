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


CHECK_EDIT = os.path.join(HERE, '..', 'skills', 'ai-tells-auditor', 'scripts', 'check_edit.py')


def check_edit(orig, edited):
    with tempfile.TemporaryDirectory() as d:
        paths = [os.path.join(d, n) for n in ('orig.md', 'edited.md')]
        for p, text in zip(paths, (orig, edited)):
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(text)
        return subprocess.run([sys.executable, CHECK_EDIT] + paths, capture_output=True, text=True)


def test_check_edit_sorts_cut_reworded_and_new():
    orig = ('# Plan\n\nIn this section we cover the plan. The build runs nightly on two hosts. '
            'It leverages a robust cache. In short, the build runs nightly.\n\n```\nnot prose.\n```\n')
    edited = ('# Plan\n\nThe build runs nightly on two hosts. It uses a cache. '
              'Costs fell [by how much].\n\n```\nnot prose.\n```\n')
    out = check_edit(orig, edited)
    assert out.returncode == 0, out.stdout
    assert 'kept 1, cut 2, reworded 1, NEW 1' in out.stdout, out.stdout
    assert 'NEW:      Costs fell [by how much].' in out.stdout, out.stdout


def test_check_edit_flags_a_section_that_grew():
    out = check_edit('# A\n\nShort.\n\n# B\n\nAlso short.\n', '# A\n\nShort.\n\n# B\n\nAlso short, and now it says more.\n')
    assert out.returncode == 1 and 'GREW:     section "B" 2 -> 7 words' in out.stdout, out.stdout


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
