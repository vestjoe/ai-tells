---
name: ai-tells-auditor
description: Audits prose for AI tells and autopilot writing (stock phrases, inflated words, set-up-and-reveal framing, filler openers and closers, hedges, em dashes, uniform rhythm), plus the content problems a linter can't see, such as invented specifics, unsourced claims, and false balance. Runs a pinned Vale config, then a judgment pass, and reports ranked findings with fixes, then applies the fixes the user picks. Use it whenever the user wants a draft, README, chapter, blog post, email, doc, PR description, or pasted text checked, reviewed, or "de-AI'd", asks whether something "sounds like ChatGPT/AI", "reads robotic", or "is too wordy", or mentions Vale or prose linting, even if they don't name this skill and even for short pasted text. When the user has the notes, outline, or brief a draft came from and wants the draft edited against them, use ai-tells-editor instead.
argument-hint: "<file, folder, or pasted text>"
---

# AI tells auditor

Find the places where a document reads as written on autopilot, by a person or a model, and say how to fix each one.

1. **Vale** checks wording: stock phrases, inflated verbs and nouns, filler, hedges, passives, em dashes, sentence rhythm. It's fast, repeatable, and gives exact line and column numbers.
2. **A judgment pass** checks what Vale can't: invented facts, claims about people with no source, false balance, repeated section formulas, generic text. The checklist is in `references/review-prompt.md`.

Report first. If the user typed a file, folder, or text after the command, audit that; if they typed nothing, ask what to audit. Edit the document only when the user asks for fixes, in this request or after seeing the report. A writer often wants to choose which findings to act on, and many hits are fine in context.

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
- **Merge overlaps.** The `Custom` rules and the packs often flag the same span (`Custom.StockAdjective` and `ai-tells.OverusedVocabulary` on the same word). Report each span once.
- **Group repeats.** "`leverage` ×5 (lines 3, 9, 14, 22, 30)" is more useful than five entries.
- **Rank by level, then by how much the fix helps.** `error` items (service filler, praise for the question, "not just X but Y", "In summary") are rarely worth keeping. `suggestion` items (passives, hedges, one em dash) are often fine. Raise them only where the text reads flat or they cluster.
- **Treat a hit as a prompt, not a verdict.** "Robust" can be a real property of an estimator. "Studies show" is fine with a citation after it. "Implement" is the precise word in a spec. Reread the sentence, and drop the hit if the sentence says something specific.
- **Note document-level signals.** `RuleOfThree`, `UniformSentences`, and `EmDashDensity` describe a pattern across the text, not one word. Report each as one pattern for the whole text.
<!-- vale on -->

## 4. The judgment pass

Read `references/review-prompt.md` and apply its twelve checks to the document. The checks cover content, structure, framing, and tone. Follow its rules: report only what you can quote, say when you're unsure, and don't pad the list. If the user supplied source material, check the document's claims against it.

## 5. Report

Use this structure. Leave out any section with nothing in it.

```markdown
## Summary
One or two sentences: how much autopilot the text shows and the biggest problem.

## Content and structure (judgment pass)
For each: item name, exact quote, the problem in one sentence, the fix or the question the writer must answer, and confidence.

## Wording (Vale)
Ranked and merged as in section 3. For each: line, quote, rule, suggested rewrite.

## Kept on purpose
Hits you judged fine in context, each with a one-line reason, so the writer knows you saw them.
```

Then, for a file, offer to apply the fixes, all of them or the ones the user picks.

For pasted text that's short enough to send as-is (an email, a message, a bio, a paragraph), add a rewrite after the report. The user usually wants to send it soon, and a ready version is more useful than an offer. Mark every fact the original doesn't give with a bracketed placeholder, such as `[how long it's been leaking]` or `[$ amount]`, so nothing invented reads as true. If the text is long, offer instead.

## 6. Fix, when asked

If the writer has the notes, outline, or brief the draft came from and wants it edited against them, that's the ai-tells-editor skill's job (`/ai-tells-auditor:ai-tells-editor`). Use it instead.

<!-- vale off -->
- Rewrite the sentence, not the word. Swapping "leverage" for "utilize" trades one tell for another.
- Keep the meaning and the facts. Never add a number, name, source, or claim to make a sentence concrete. If a fix needs a fact you don't have, leave a question for the writer.
- Keep the writer's voice, technical terms, and anything inside code, links, and quotes.
- After editing, run `audit.sh` again and report what's left and why you kept it.
<!-- vale on -->

To turn a rule off for a passage the writer wants to keep, Vale reads HTML comments in Markdown:

```markdown
<!-- vale Custom.StockAdjective = NO -->
A robust estimator.
<!-- vale Custom.StockAdjective = YES -->
```

`<!-- vale off -->` and `<!-- vale on -->` turn every rule off. Add these only when the user asks, since they change the document.

## What's in the config

`.vale.ini` turns on this repo's `Custom` style plus five pinned packs: vale-ai-tells (AI-writing patterns), proselint (clichés, redundancy), write-good (weasel words), and Microsoft and Google (sentence length, adverbs, jargon). It turns off pack rules that repeat another rule or whose hits don't need fixing, with a reason for each. Read it if a user asks why a rule did or didn't fire.
