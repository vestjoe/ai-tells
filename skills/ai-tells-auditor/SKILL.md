---
name: ai-tells-auditor
description: Audits prose for AI tells and autopilot writing and reports ranked findings with fixes. It never edits the text. Fixes go through ai-tells-editor, which it runs in the same answer when the user wants them. Runs a pinned Vale config plus a judgment pass for stock phrases, inflated words, set-up-and-reveal framing, filler, hedges, em dashes, uniform rhythm, invented specifics, unsourced claims, and false balance, and checks the draft against a voice profile when one is named. Use it whenever the user asks whether text, including a short email or message pasted into the chat, "sounds robotic", "sounds like AI/ChatGPT", or is "too wordy"; wants a draft, README, chapter, post, email, doc, or PR description checked, reviewed, or "de-AI'd"; or asks to run Vale or sort out which Vale findings matter. Use it before answering from your own read, even for a two-line message, since its checks catch tells a quick read misses. When the user has the notes, outline, or brief a draft came from and wants the draft edited against them, use ai-tells-editor instead.
argument-hint: "<file, folder, or pasted text>"
---

# AI tells auditor

Find the places where a document reads as written on autopilot, by a person or a model, and say how to fix each one.

1. **Vale** checks wording: stock phrases, inflated verbs and nouns, filler, hedges, passives, em dashes, sentence rhythm. It's fast, repeatable, and gives exact line and column numbers.
2. **A judgment pass** checks what Vale can't: invented facts, claims about people with no source, false balance, repeated section formulas, generic text. The checklist is in `references/review-prompt.md`.
3. **A voice check** compares the draft with a voice profile, when the user names one or the draft came from ai-tells-writer.

Read `references/standard.md` first. It holds the rules the writer drafts to and the editor edits to, and this skill reports where a draft misses them.

Report first, and don't edit. If the user typed a file, folder, or text after the command, audit that; if they typed nothing, ask what to audit. This skill never changes the text, even when the user asks for fixes. The editor makes every change, and it fixes against the same standard this report checks (see section 7).

## 1. Get the text

- **Files or folders:** use the paths as given. The config covers `.md` and `.txt`.
- **Pasted text:** pipe it to the script on stdin. It's linted as Markdown.
- **Other formats** (`.docx`, `.html`, `.rst`, a Google Doc): extract the prose to a Markdown file in a scratch directory, lint that, and map line numbers back to quotes when you report.

## 2. Run Vale

```bash
<skill-dir>/scripts/audit.sh path/to/draft.md            # one line per finding
<skill-dir>/scripts/audit.sh --min=warning docs/         # skip suggestions on a large tree
cat <<'EOF' | <skill-dir>/scripts/audit.sh               # pasted text
...
EOF
```

`<skill-dir>` is the folder this file is in. The script uses this skill's own `.vale.ini`, so a project's Vale config doesn't change the result. On first run it fetches the pinned third-party packs with `vale sync`, which needs network access.

Each finding is one line:

```
LINE:START-END [level] Rule match="text" replace_with="..." msg="..."
```

Exit codes: `0` no errors, `1` at least one error-level finding (normal for a draft), `2` Vale failed or a path doesn't exist, `3` Vale isn't installed. On `3`, tell the user how to install it (`brew install vale`, or https://vale.sh/docs/install) and ask before installing anything yourself.

## 3. Make sense of the hits

Raw Vale output repeats itself and flags text that's fine. Turn it into a short list a writer can act on:

<!-- vale off -->
- **Merge overlaps.** The `Custom` rules and the packs often flag the same span (`Custom.StockAdjective` and `ai-tells.OverusedVocabulary` on the same word). Report each span once, in one section of the report. When the judgment pass already covers a span, leave it out of the Vale list.
- **Group repeats.** "`leverage` ×5 (lines 3, 9, 14, 22, 30)" is more useful than five entries.
- **Rank by level, then by how much the fix helps.** `error` items (service filler, praise for the question, "not just X but Y", "In summary") are rarely worth keeping. `suggestion` items (passives, hedges, one em dash) are often fine. Raise them only where the text reads flat or they cluster.
- **Treat a hit as a prompt, not a verdict.** "Robust" can be a real property of an estimator. "Studies show" is fine with a citation after it. "Implement" is the precise word in a spec. Reread the sentence, and drop the hit if the sentence says something specific. The standard's "AI tells" section names the hits to leave.
- **Note document-level signals.** `RuleOfThree`, `UniformSentences`, and `EmDashDensity` describe a pattern across the text, not one word. Report each as one pattern for the whole text.
<!-- vale on -->

## 4. The judgment pass

Read `references/review-prompt.md` and apply its twelve checks to the document. The checks cover content, structure, framing, and tone. Follow its rules: report only what you can quote, say when you're unsure, and don't pad the list. If the user supplied source material, check the document's claims against it. Also read the draft against the standard's "Linked sentences" section, and report each run of short, unlinked sentences with a quote.

## 5. Check the voice

Run this step only when the user names a voice or the draft came from ai-tells-writer. Find the profile the way the standard's "The voice" section says. With no voice named, the draft's own voice is the voice, and the standard says to skip this comparison.

Measure the draft. For pasted text, save it to a file in a scratch directory first.

```bash
<skill-dir>/../ai-tells-writer/scripts/voice_stats.py --json path/to/draft.md
```

Compare the output with the profile's Numbers section: `sentence_median` and `sentence_p90` with its sentence length, `paragraph_median` with its paragraph length, and `question_share`, `contractions_per_100_words`, and `person_per_1000_words` with its lines on questions, contractions, and person. The script leaves lists and headings out, so read the draft's layout against the profile's Lists and Headings lines yourself. Then read the draft for each habit the profile lists to avoid. Report each gap under `## Voice` with the number or quote and the profile line it misses.

## 6. Report

Use this structure. Leave out any section with nothing in it.

```markdown
## Summary
One or two sentences: how much autopilot the text shows and the biggest problem.

## Content and structure (judgment pass)
For each: item name, exact quote, the problem in one sentence, the fix or the question the writer must answer, and confidence.

## Wording (Vale)
Ranked and merged as in section 3. For each: line, quote, rule, suggested rewrite.

## Voice
Only when section 5 ran. For each gap: the draft's number or a quote, and the profile line it misses.

## Kept on purpose
Hits you judged fine in context, each with a one-line reason, so the writer knows you saw them.
```

Every suggested rewrite follows the standard's "The source" section. Where the fix needs a fact the draft doesn't give, such as a date, a number, or a name, write the placeholder or the question for the writer instead.

To turn a rule off for a passage the writer wants to keep, Vale reads HTML comments in Markdown:

```markdown
<!-- vale Custom.StockAdjective = NO -->
A robust estimator.
<!-- vale Custom.StockAdjective = YES -->
```

`<!-- vale off -->` and `<!-- vale on -->` turn every rule off. Mention these in the report when the writer wants to keep a flagged passage. Adding them changes the document, so that's the editor's job.

## 7. Hand off fixes

When another skill runs this one for the report only, save the report to the path it gives and stop. Don't run the editor.

When the user wants the fixes, run the editor skill (`/ai-tells-auditor:ai-tells-editor`) in the same answer. Do the same, without being asked, for pasted text short enough to send as-is (an email, a message, a bio, a paragraph): the user wants to send it soon, and a fixed version is more useful than an offer. If the user hasn't asked for fixes and the text is a file or long, end the report with an offer to run the editor on all the findings or on the ones the user picks.

When the user picks findings, mark each picked one in the report with `[fix]` and tell the editor to fix only those. Save the report to a file in a scratch directory, and give the editor the draft, the report, the notes or brief if the user has them, and the voice if one was named. The editor makes every change to the standard and checks its own edit.

## What's in the config

`.vale.ini` turns on this repo's `Custom` style plus five pinned packs: vale-ai-tells (AI-writing patterns), proselint (clichés, redundancy), write-good (weasel words), and Microsoft and Google (sentence length, adverbs, jargon). It turns off pack rules that repeat another rule or whose hits don't need fixing, with a reason for each. Read it if a user asks why a rule did or didn't fire.
