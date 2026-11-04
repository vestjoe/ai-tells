# Review prompt

Use this prompt for the part of a review that Vale can't do. Run `vale` on the document first and fix what it reports. Then give this prompt, the document, and any source material to the reviewer, a person or an AI model.

---

<!-- The prompt quotes the patterns it describes, so Vale skips it. -->
<!-- vale off -->

You are reviewing a document for problems a linter can't find. A linter has already checked word choice, stock phrases, passives, sentence length, and punctuation, so don't report those. Look only for the problems below.

Report a problem only when you can quote the text it's in. A short, accurate list is more useful than a long one. If you aren't sure, say so in the finding instead of leaving it out or stating it as fact. Don't invent problems to fill the list, and don't add facts the document doesn't contain.

## What to look for

### Content

1. **Invented specifics.** Names, dates, figures, versions, or quotes that nothing in the document or the source material supports. For each claim, ask "says who?" If you can't point to the source, report it.
2. **Claims about what people did or decided.** Statements that a person or team did, said, chose, or delivered something, when no source says so. Example: "The copy you already delivered is unchanged", with no evidence that anything was delivered.
3. **Precision the data can't support.** A decimal percentage from a few cases, or an exact figure where the source gives a range.
4. **False balance.** Pros and cons, or two or more options, set out with no recommendation, when the reader needs to know which to pick.
5. **Every point weighted the same.** A list or set of sections with no ranking, when some points matter more than others.

### Structure

6. **The same formula in every section.** A label or phrasing the writer repeats to open or close each section, such as "**Point:**" or "Why it matters:". The linter catches common fixed phrases, but not a formula the writer made up.
7. **Headers and bullets on content too short to need them.** A heading over one sentence, or bullets that would read better as a sentence.
8. **Filler openings and closings.** Delete the first and last sentence of each section. If the section reads the same without them, report them.

### Framing

9. **A known move in new words.** The linter catches these moves only in wording it knows. Report them in any other wording:
   - a set-up that exists only to be knocked down ("not X but Y")
   - a reframe ("X is really Y")
   - a reveal ("here's the thing")
   - a closing line meant to sound profound

   Example: "This goes beyond speed; it's really about trust." Test: delete the set-up. If the point still stands, report it. A comparison the document goes on to support isn't a finding.

### Tone

10. **Apology loops and over-politeness.** Repeated apologies, thanks, or reassurance that delay the content.
11. **Generic text.** Swap in a different company, product, or subject. If the passage still works unchanged, it says nothing specific. Report it.
12. **Sentences no one would say aloud.** Read each paragraph as if speaking to a colleague. Report a sentence you'd never say that way.

## How to report

List the findings most serious first. For each one, give:

- **Item:** the number and name from "What to look for".
- **Quote:** the exact text, copied word for word, so anyone can check it against the document.
- **Problem:** one sentence on what's wrong.
- **Fix:** a concrete change, or the question the writer must answer, such as "What's the source for 40%?"
- **Confidence:** high, medium, or low.

If you find nothing for an item, leave it out. If you find nothing at all, say "No findings."

<!-- vale on -->
