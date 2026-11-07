---
name: ai-tells-writer
description: Drafts prose from notes, an outline, bullet points, or a brief, in a chosen voice. It keeps every note point in order and invents no facts. Where a fact is missing, it leaves a bracketed placeholder, and it lists every sentence that doesn't come from a note. Also builds a voice profile from a person's writing samples, such as a book, posts, or reports, so later drafts sound like them. Use it whenever the user wants notes turned into a draft, a first draft written in the user's own voice or a named voice, or a voice built or updated from samples, even if they don't mention this skill. To check a finished draft for AI tells, use ai-tells-auditor. To cut a draft against the notes it came from, use ai-tells-editor.
argument-hint: "<notes> [voice]"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/*)
---

# Draft from notes in a voice

Arguments given: `$ARGUMENTS`

The notes are the source of truth. The draft says what the notes say, in the order they say it, in the chosen voice. It doesn't add facts.

If the user wants a voice built or updated from writing samples, read `${CLAUDE_SKILL_DIR}/references/build-voice.md` and follow it. The rest of this file is for drafting.

## 1. Get the notes and the voice

Take the notes file, or pasted notes, from the arguments or the request. If there are no notes, ask for them.

Find the voice by name, in this order:

1. `~/.claude/voices/<name>.md` (private profiles, kept outside any repository)
2. `${CLAUDE_SKILL_DIR}/voices/<name>.md` (voices that come with the plugin)

With no voice named, use `plain`. If a named voice isn't in either folder, say so, list the voices in both folders, and ask which to use. Don't switch to `plain` on your own.

Read the whole profile before writing. Follow its numbers and both lists of habits.

## 2. Number the note points

List the notes' points in order, numbered. A point is one claim, step, or example. Keep sub-points under their parent.

## 3. Choose the person

Use `I`, `we`, or `you` to fit the piece:

- The notes say `we` or speak for a team: `we`.
- The notes are steps or advice for the reader: `you`.
- The notes are one person's view or story: `I`.

If the notes don't settle it, ask before drafting.

## 4. Write the draft

- Cover every note point, in the notes' order. Use the notes' headings if they have any.
- Write in the voice. Match its sentence and paragraph lengths, and use its habits to keep.
- Use only the facts, numbers, names, sources, and examples in the notes. Where a sentence needs one the notes don't give, write a bracketed placeholder that says what's missing, such as `[how many hosts]` or `[source]`.
- You may add sentences that join the points, such as a topic sentence or an explanation of a term the notes use. These state or restate a note's point and don't add a claim.
- Write it once. Don't review or rewrite the draft. The auditor checks it.

Save the draft next to the notes as `<notes-name>.draft.md`, or where the user says. For pasted notes, show the draft in the reply.

## 5. Tag and report

Tag each sentence of the draft, as the editor does:

- `[note N]`: states, explains, or restates note point N.
- `[example of note N]`: an example the notes give for point N.
- `[not in notes]`: adds a claim, fact, or example the notes don't have.

Then report:

1. The voice used, and the person chosen and why.
2. Each note point with the sentence in the draft that states it. If a point isn't stated, say so.
3. Every placeholder, with what it needs.
4. Every `[not in notes]` sentence, quoted, so the user can keep or cut it.
5. Tell the user to check the draft next with `/ai-tells-auditor:ai-tells-auditor <draft>`.
