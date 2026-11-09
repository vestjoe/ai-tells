---
name: ai-tells-editor
description: Edits a draft against the notes, outline, or brief it was written from. Cuts repeats, announcers, and summaries; keeps every point and example in the notes; adds no words, facts, or sentences; checks the edit with a script; and lists every sentence that isn't in the notes so the writer decides. Use it whenever the user has a draft plus the notes, outline, bullet points, or brief behind it and wants the draft edited, tightened, trimmed, or cut down against them, wants to check that every note point survived, or wants to find what a model or contractor added that isn't in the notes, even if they don't name this skill. For a draft with no notes, use ai-tells-auditor instead.
argument-hint: "<draft> <notes>"
---

# Edit a draft against the writer's notes

Arguments given: `$ARGUMENTS`

You need two files: the draft and the notes it came from. Take them from the arguments or the user's request, draft first. If either is missing, ask for it. Don't start without the notes: an edit with no notes to check against is an audit, which is the ai-tells-auditor skill's job.

The writer's notes are the source of truth. The draft came from them, and the edit makes the draft say what the notes say, once each, in the order the notes put it. The edit removes text. It never adds a fact.

Work on a copy. Keep the original next to it as `<name>.orig.md`.

## 1. Tag every claim

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

## 2. Cut

<!-- vale off -->
- **Repeats.** When a note point is stated more than once, keep the plainest statement in the place the notes put it and cut the others.
- **Announcers and summaries.** Cut sentences that only say what comes next or what was just said ("There are three options.", "Both problems waste time.").
- **Links stay.** Words that tie a sentence to the one before it aren't announcers: "To answer that", "Once you see the threat as a person", a "because" or "so" clause that gives the reason. Cutting them leaves sentences side by side with no thread between them.
- **Examples stay.** An example of a point isn't a repeat of it. Cut an example only if it repeats another example of the same point.
- **`[not in notes]` claims stay.** Don't cut them. List them for the writer (step 4).
- Cut whole sentences or clauses. Don't reword what's left.
<!-- vale on -->

## 3. Repair, without writing

- **A section that lost its setup.** If a cut leaves a section or paragraph opening on a detail with nothing to explain it, put the cut sentence back. Don't only mention it in the report. Restore it, then list it there.
- **Joined sentences stay joined.** Don't split a sentence whose halves follow from each other, such as a step and its result. Split at ", and" only when a sentence runs past 40 words and its halves are unrelated claims.
- **Anything else the cut broke.** Ask the writer. Don't write a new sentence to fill a gap.

## 4. Check and report

```bash
python3 <skill-dir>/scripts/check_edit.py <name>.orig.md <name>.md
```

`<skill-dir>` is the folder this file is in.

It must report `NEW 0` and no `GREW` lines. If it finds a new sentence, you wrote something. Undo it. Then give the writer:

1. Words before and after, from `check_edit.py`.
2. Every cut, quoted, with its reason: repeat of note N, announcer, or summary.
3. Every sentence you put back in step 3.
4. Each note point with the sentence in the edited draft that states it. If a point isn't stated, say so. That's a gap in the draft, not something to write in.
5. Every `[not in notes]` sentence that's still in the draft, quoted, so the writer can keep or cut each one.
