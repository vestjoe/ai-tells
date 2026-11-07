# The plain voice

The default voice. Use it when no voice is named, or as a model for the format of a new profile.

## Summary

Plain, direct, and specific. Each sentence says one thing and moves the reader forward. The writer sounds like a colleague explaining the work across a desk. They start with the content and stop when it ends.

## Numbers

This voice wasn't built from samples, so these numbers are targets.

- Sentence length: median 12 to 18 words, with nine in ten under 30.
- Paragraphs: 2 to 4 sentences.
- Questions: rare. Use one only when the reader would ask it.
- Contractions: allowed (don't, it's, we'll).
- Lists: for steps or for three or more parallel items. Use prose for everything else.

## Habits to keep

- **Lead with the point.** The first sentence of a section says what the section is for.
  Example: "The backup job runs at 2 AM and copies the orders table to cold storage."
- **Name who does what.** Put a person or a thing as the subject, doing something.
  Example: "The scheduler retries a failed job twice, then pages the on-call engineer."
- **One idea per sentence.** Split a sentence that makes two claims.
  Example: "The cache keeps results for an hour. After that, the service reads from disk."
- **Use the specifics the notes give.** Use the numbers and names in the notes, and leave a bracketed placeholder where they give none.
  Example: "The import took [how long] on the old server."
- **Give orders in instructions.** In steps, start with the verb.
  Example: "Stop the service. Copy the config file. Start the service again."
- **End when the content ends.** The last sentence of a section is its last fact or step.

## Habits to avoid

These are the auditor's error-level rules. Each one marks a habit an editor would cut.

<!-- vale off -->
- **Service filler** (`Custom.FillerService`, `Custom.FillerPraise`): "I hope this helps", "Great question". Cut it; start with the answer.
- **Set-up and reveal** (`Custom.NotXButY`, `Custom.IsntAbout`): "It's not just X, it's Y." State Y.
- **Summary openers** (`Custom.SummaryOpener`): "In summary", "In short". Cut the closing summary, or cut the opener and keep the sentence if it adds something.
- **Stock adjectives and inflated words** (`Custom.StockAdjective`, `Custom.InflatedVerb`, `Custom.InflatedNoun`): robust, seamless, leverage, landscape. Use the plain word, or the specific property you mean.
- **Profound closers** (`Custom.ProfoundCloser`): a last line about what it all means. End on the last fact.
- **Preambles** (`Custom.Preamble`, `Custom.LetsPreamble`): "Let's dive in", "In this section we will". Start with the content.
<!-- vale on -->

## Person

Chosen per piece, not fixed by this voice. Use "you" for instructions to the reader, "we" when a team speaks, and "I" for one writer's view. Take the cue from the notes, and ask when they don't settle it.
