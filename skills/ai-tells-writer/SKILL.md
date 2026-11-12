---
name: ai-tells-writer
description: Drafts prose from notes, an outline, bullet points, or a brief, in a chosen voice, then finishes the draft by running ai-tells-auditor and ai-tells-editor on it once each. It keeps every note point in order and invents no facts. Where a fact is missing, it leaves a bracketed placeholder, and it lists every sentence that doesn't come from a note. Also builds a voice profile from a person's writing samples, such as a book, posts, or reports, so later drafts sound like them. Use it whenever the user wants notes turned into a draft, a first draft written in the user's own voice or a named voice, or a voice built or updated from samples, even if they don't mention this skill. To check a draft someone else wrote for AI tells, use ai-tells-auditor. To edit an existing draft, with or without its notes, use ai-tells-editor.
argument-hint: "<notes> [voice]"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/*) Bash(${CLAUDE_SKILL_DIR}/../ai-tells-auditor/scripts/*) Bash(${CLAUDE_SKILL_DIR}/../ai-tells-editor/scripts/*)
---

# Draft from notes in a voice

Arguments given: `$ARGUMENTS`

The notes are the source of truth. The draft says what the notes say, in the order they say it, in the chosen voice. Read `${CLAUDE_SKILL_DIR}/../ai-tells-auditor/references/standard.md` before drafting. It holds the rules on the source, the voice, AI tells, and linked sentences that this skill drafts to, and the auditor and editor use the same file.

If the user wants a voice built or updated from writing samples, read `${CLAUDE_SKILL_DIR}/references/build-voice.md` and follow it. It saves the profile to `~/.claude/voices/<name>.md`. The rest of this file is for drafting.

## 1. Get the notes and the voice

Take the notes file, or pasted notes, from the arguments or the request. If there are no notes, ask for them.

With no voice named, use `plain`. Find a named voice the way the standard's "The voice" section says. Read the whole profile before writing.

## 2. Number the note points and plan the paragraphs

List the notes' points in order, numbered. A point is one claim, step, or example. Keep sub-points under their parent.

Then group the points into paragraphs, one idea per paragraph, and write down how each point leads to the next. Notes are fragments with the links left out. The draft's job is to supply those links, choosing each one the way the standard's "Linked sentences" section says.

## 3. Choose the person

Use `I`, `we`, or `you` to fit the piece:

- The notes say `we` or speak for a team: `we`.
- The notes are steps or advice for the reader: `you`.
- The notes are one person's view or story: `I`.

If the notes don't settle it, ask before drafting.

## 4. Write the draft

- Cover every note point. Keep the paragraphs in the notes' order, but inside a paragraph put the points in whatever order makes the reasoning read straight through. Use the notes' headings if they have any.
- Make each sentence follow from the one before it. Don't turn each note into its own sentence and set them side by side. Join a point to the one it explains, answers, or limits, in the same sentence or the next, and say how they connect. A sentence that could be moved anywhere in the paragraph isn't connected yet.
- Write in the voice, as the standard's "The voice" section says.
- Keep to the facts in the notes, and write a placeholder where one is missing, as the standard's "The source" section says.
- Add the words that link the points, such as a topic sentence or a line that says how one point leads to the next. Every paragraph needs them. Pick each link the way the standard's "Linked sentences" section says.
- Write it once. Don't review or rewrite the draft. Step 6 checks and edits it.

Save the draft next to the notes as `<notes-name>.draft.md`, or where the user says. For pasted notes, save them as `notes.md` in a scratch directory first, and keep every file the chain writes there.

## 5. Tag the draft

Tag each sentence of the draft, as the editor does:

- `[note N]`: states, explains, or restates note point N.
- `[example of note N]`: an example the notes give for point N.
- `[not in notes]`: adds a claim, fact, or example the notes don't have.

## 6. Audit and edit

Copy `<notes-name>.draft.md` to `<notes-name>.final.md`, next to it. The first draft stays as it is.

Run the auditor (`/ai-tells:ai-tells-auditor`) on `<notes-name>.draft.md` with the voice, which is `plain` when the user named none. Run it for the report only, and give it the path to save the report to: `<notes-name>.audit.md`, next to the notes.

Then run the editor (`/ai-tells:ai-tells-editor`) on `<notes-name>.final.md` with the notes, the voice, and `<notes-name>.audit.md`. With no finding marked `[fix]`, the editor works through the whole report. The editor checks its edit against the notes alone and leaves its own files next to the draft: `<notes-name>.final.orig.md`, a copy of the first draft, and `<notes-name>.final.claims.md`. Run each skill once.

## 7. Report

1. The path of the finished draft, with the first draft and the audit report saved beside it. For pasted notes, show the finished draft in the reply.
2. The voice used, and the person chosen and why.
3. Each note point with the sentence in the finished draft that states it, taken from the editor's report, since it describes the edited draft. If a point isn't stated, say so.
4. Every placeholder, with what it needs.
5. Every `[not in notes]` sentence still in the finished draft, quoted, so the user can keep or cut it. Take these from the editor's report, not the tags from step 5.
6. The editor's changes, taken from its report. Give the word counts before and after and quote each cut with its reason. Then list the audit hits it left, and with a named voice, its voice numbers next to the profile's.
