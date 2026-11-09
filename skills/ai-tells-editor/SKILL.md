---
name: ai-tells-editor
description: Edits a draft, with or without the notes, outline, or brief it was written from, and is the only skill in this plugin that changes text. It rewrites each flagged sentence in the voice, cuts repeats, announcers, and summaries, and keeps every point and example in the notes. A script then proves the edit didn't add a fact, and any number, name, or quote the source lacks becomes a bracketed placeholder. It lists every sentence that isn't in the notes so the writer decides, then reruns the audit and reports what's left. Use it whenever the user has a draft plus the notes, outline, bullet points, or brief behind it and wants the draft edited, tightened, trimmed, or cut down against them, wants to check that every note point is still there, or wants to find what a model or contractor added that isn't in the notes, even if they don't mention this skill. Use it too when the user wants a draft with no notes edited, tightened, or fixed, or wants the fixes from an ai-tells-auditor report applied. To check a draft without changing it, use ai-tells-auditor.
argument-hint: "<draft> [notes] [voice]"
---

# Edit a draft to the standard

Arguments given: `$ARGUMENTS`

This skill is the plugin's one place that changes text. It rewrites a draft to the rules in `${CLAUDE_SKILL_DIR}/../ai-tells-auditor/references/standard.md` and then proves the edit didn't add a fact. Read the standard first, since this file has only the steps.

## 1. Get the draft, the source, the voice, and the report

- **Draft.** Take the file from the arguments or the request. For text pasted into the chat, save it as `<name>.md` in a scratch directory so the scripts can read it.
- **Source.** Use the notes, outline, or brief the draft came from if the user has them. Without them the draft is its own source, as the standard's "The source" section says, and the edit can't add a fact the draft doesn't already have.
- **Voice.** When the user names a voice, find it the way the standard's "The voice" section says. With none named, keep the draft's own voice.
- **Audit report.** The auditor hands one over as a file when it runs this skill. With no report, run `audit.sh` and the judgment pass the way the standard's "AI tells" section says, and use those findings as the report. When some findings are marked `[fix]`, fix those and leave the rest alone. With no marks, fix every finding.

Copy the draft to `<name>.orig.md` before you change anything, and keep that copy. Then edit `<name>.md` in place.

## 2. Tag every claim

Run this step when there are notes. Without notes, every claim traces to the draft itself, so skip to step 3.

Write `<name>.claims.md`: one line per claim in the draft, grouped under the draft's headings. Number the notes' points in order, then tag each claim:

- `[note N]`: the claim states note point N.
- `[example of note N]`: a case, example, or detail of point N.
- `[not in notes]`: anything else.

```
## Nightly builds
- The build runs nightly on two hosts [note 3]
- Last week's run caught a broken migration before release [example of note 3]
- Most teams build too rarely [not in notes]
```

## 3. Edit

<!-- vale off -->
- **Repeats.** When a point is stated more than once, keep the plainest statement in the place the source puts it and cut the others.
- **Announcers and summaries.** Cut sentences that only say what comes next or what was just said ("There are three options.", "Both problems waste time.").
- **Examples stay.** An example of a point isn't a repeat of it. Cut an example only if it repeats another example of the same point.
- **`[not in notes]` claims stay.** Leave them in and list them for the writer (step 5).
<!-- vale on -->
- **Findings.** Fix each finding by rewriting its sentence in the voice. Keep the words that link it to the sentences around it. The standard's "AI tells" and "Linked sentences" sections say how.
- **Every paragraph.** When no finding is marked `[fix]`, read each paragraph against the whole standard, not only the flagged sentences, and rejoin any run of short, unlinked sentences wherever it is. When some are marked, change only the sentences those findings need.
- **Voice.** When no finding is marked `[fix]` and the user named a voice, bring sentence lengths, paragraph lengths, and layout to the profile's Numbers, and fix each `## Voice` gap across the whole paragraph rather than one sentence at a time. With no voice named, the standard's "The voice" section says what to keep.
- **Facts the source lacks.** When a finding or a gap left by the edit needs a fact the source doesn't give, such as a vague amount or a claim with no source, follow the placeholder rule in the standard's "The source" section, such as `[by how much]`. Or keep the claim as the source has it and ask the writer about it in the report.
- **Scope.** Inside a paragraph you can merge, split, and reorder sentences, and you can merge or split paragraphs. Split only where the standard's "Linked sentences" section allows. Keep the section order and the headings, and keep code, links, quotes, and terms the way the standard's "The source" section says.
- **Lost setup.** If a cut leaves a section or paragraph opening on a detail with nothing to explain it, put the cut sentence back and list it in the report.

## 4. Check the edit

```bash
${CLAUDE_SKILL_DIR}/scripts/check_edit.py <name>.orig.md <name>.md [notes]
```

With the notes as the third argument, the script checks facts against the notes alone. Its docstring explains every line it prints.

The first line must end in `new facts 0`. Each `FACT` line quotes a number, name, quoted string, or code span that the source doesn't have, with the sentence it's in. Replace each one with a placeholder that says what's missing, or put back the source's wording, and run the script again until it reports `new facts 0`. A `GREW` line is a warning. Check that the section grew by linking words and not by a new claim.

Then read every `new:` line, and every `reworded:` line whose sentence gained a clause its `from:` sentence lacks. Each one that adds a claim goes in the report, with notes or without. A `CHECK` line quotes a capitalized word at the start of a sentence that the source lacks. When that word is a name, treat it as a `FACT`.

Then rerun the audit on the edited draft:

```bash
${CLAUDE_SKILL_DIR}/../ai-tells-auditor/scripts/audit.sh <name>.md
```

Fix any hit the edit missed or brought in, and run `check_edit.py` again after each change. A hit stays when fixing it would break the standard: a `ConsequenceClause` that states a real cause, or a vague phrase whose fix needs a fact the source lacks. List each remaining hit in the report with its reason.

With a named voice and no finding marked `[fix]`, measure the edited draft too:

```bash
${CLAUDE_SKILL_DIR}/../ai-tells-writer/scripts/voice_stats.py --json <name>.md
```

Compare its numbers with the profile's Numbers section and bring any that miss back toward the profile.

## 5. Report

For pasted text, show the whole edited text in the reply first, since the user has no file to open. Then give the writer:

1. Words before and after, from `check_edit.py`, and the path of the `<name>.orig.md` copy you left.
2. Every cut, quoted, with its reason, such as a repeat or an announcer.
3. Every sentence you put back in step 3.
4. Every placeholder, with the fact it waits for, and every claim you kept as the source had it but want the writer to check.
5. With notes, each note point with the sentence in the edited draft that states it. If a point isn't stated, say so. That's a gap in the draft, not something to write in.
6. Every sentence still in the draft that adds a claim, quoted, so the writer can keep or cut each one. That covers the `[not in notes]` claims from step 2 and each added claim step 4 found. Without notes, label them `[not in the draft]`.
7. The audit hits left after the rerun, each with the reason it stays.
8. With a named voice, the edited draft's numbers from `voice_stats.py` next to the profile's.
