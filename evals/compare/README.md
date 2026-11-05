# Comparing this skill with Vale's skills

Vale publishes its own Claude Code plugin ([vale-cli/agent-tools](https://github.com/vale-cli/agent-tools)): five skills (`setup`, `fix`, `triage`, `vocab`, `ci`) and a hook that lints each prose file Claude writes. It has no rules of its own. It runs whatever `.vale.ini` the project has, and `/vale:setup` writes `BasedOnStyles = Vale, Microsoft` by default.

The two tests below check whether this repo adds anything over that plugin.

## 1. Linter test (no model, about 10 seconds)

```bash
skills/ai-tells-auditor/scripts/audit.sh tests/sample_clean.md   # once, to sync the packs
python3 evals/compare/compare_linters.py            # tables
python3 evals/compare/compare_linters.py --detail   # plus a row per label
```

It runs five Vale configs over two corpora:

- `corpus/tells/` plus the two drafts in `evals/files/`: 91 AI tells, labeled by hand in `corpus/labels.json`. The categories come from Wikipedia's "Signs of AI writing" list and include some no config targets: knowledge-cutoff notes, placeholders, and false balance.
- `corpus/clean/`: 12,000 words of human prose from before LLMs. Every alert here is noise. `corpus/clean/SOURCES.md` lists the sources and how they were changed.

| Config | What it is |
| --- | --- |
| `vale-setup` | What `/vale:setup` writes: `Vale, Microsoft` |
| `vale-setup+ai-tells` | That, plus the vale-ai-tells pack, nothing tuned |
| `all-packs-untuned` | This skill's five packs and `Vale`, nothing turned off |
| `skill-without-Custom` | This skill's `.vale.ini` minus the `Custom` style |
| `this-skill` | This skill's `.vale.ini`, unchanged |

All five configs read the packs from `skills/ai-tells-auditor/styles/` and use the same pinned versions.

The columns:

- **Recall** is the share of labels that at least one alert overlaps. Mechanics rules don't count: pronouns, contractions, `!`, dash spacing, and spelling. `INCIDENTAL` in the script lists them. They overlap a tell only by accident, and fixing them leaves the tell in place.
- **Recall, unseen files** leaves out the three files the Custom rules may have been tuned on, which are listed under `seen_files` in `labels.json`. This is the fairer number.
- **Recall, errors only** matters because Vale's hook and `/vale:fix` act on error-level alerts only, by default.
- **Noise** is alerts per 1,000 words of the clean corpus, at every level.

Don't add labels to match what a config catches. Add new text instead, labeled before you run anything. To test on your own human writing, pass `--clean <folder of .md files>`.

## 2. With-model test

This test runs the prompts in `evals/evals.json` once with this skill and once with Vale's plugin, then grades both against the same assertions.

```bash
git clone https://github.com/vale-cli/agent-tools /some/path/agent-tools
python3 evals/compare/model/prepare_runs.py --vale-tools /some/path/agent-tools --runs 3 \
  --out ai-tells-auditor-workspace/run-1 [--vale-config skill|setup]
```

`--vale-config` sets the Vale arm's `.vale.ini`:

- `skill` (the default) gives Vale's plugin this skill's own config. Rules and tuning are then equal, so the only differences left are this skill's SKILL.md and its second pass. This answers "could I use Vale's skills and add my rules?"
- `setup` gives it what `/vale:setup` writes.

The script writes a `brief.md` for every run. Give each brief to its own subagent, in parallel:

```
Your whole task is written in <path>/brief.md. Read that file and carry it out exactly as it says.
```

Save each subagent's `total_tokens` and `duration_ms` to `timing.json` beside its `brief.md` as it finishes. Then grade:

```bash
python3 evals/compare/model/grade.py blind ai-tells-auditor-workspace/run-1
# One grader subagent reads skill-creator's agents/grader.md and writes grading.json into each blind/<id>/.
python3 evals/compare/model/grade.py collect ai-tells-auditor-workspace/run-1
cd <skill-creator dir> && python3 -m scripts.aggregate_benchmark <abs path>/ai-tells-auditor-workspace/run-1 --skill-name ai-tells-auditor
```

Limits of the with-model test:

- **The evals were written for this skill.** Some assertions check things only its SKILL.md asks for, such as a "kept on purpose" list or a rewrite of pasted text. A fair reading separates assertions about what the user asked for from assertions about this skill's own conventions.
- **Each eval runs in a subagent.** A fresh Claude Code session would be closer to real use. The brief lists the installed skills, and the Vale arm runs the hook by hand after each edit.
- **The grading is blind to names, not to style.** `grade.py blind` redacts skill names, but a reply that opens "a branch per file" still gives its arm away.
- **Three evals is a small sample.** Run at least three runs per arm before drawing conclusions.
