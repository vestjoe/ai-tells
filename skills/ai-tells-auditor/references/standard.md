# The standard

The writer drafts to this standard and the editor edits to it. The auditor reports where a draft misses it. Each skill reads this one file rather than a copy of the rules, so the rules can't drift apart.

## The source

The source is the truth, and the draft says only what the source says. With notes, the source is the notes alone, so a fact the writer invented doesn't pass because it's in the first draft. Without notes, the source is the original draft.

- Use only the facts, numbers, names, sources, and examples in the source. A made-up detail reads as true, and the reader can't tell it from the real ones.
- Never add a number, name, date, quote, source, or example to make a sentence concrete. Where a sentence needs a fact the source doesn't give, write a bracketed placeholder that says what's missing, such as `[how many hosts]` or `[source]`, so the writer can fill it in.
- A sentence that adds a claim but no new fact can stay. List it as `[not in notes]` so the writer decides whether to keep it.
- Keep code, links, quotes, and technical terms as the source has them. They're facts too, and a reworded quote is a misquote.

The editor's `check_edit.py` holds an edit to this. It flags any number, name, quoted string, or code span in the edit that isn't in the source, and any fenced code block that differs from the source's.

## The voice

Find the voice by name, in this order:

1. `~/.claude/voices/<name>.md` (private profiles, kept outside any repository)
2. `${CLAUDE_SKILL_DIR}/../ai-tells-writer/voices/<name>.md` (voices that come with the plugin)

If a named voice isn't in either folder, say so and give the user the list of voices in both folders to pick from. Don't fall back to `plain` on your own.

A voice's numbers and layout apply, and so do both of its habit lists. Match its sentence and paragraph lengths. Use the habits it keeps and avoid the ones it lists to avoid.

With no voice named, the writer uses `plain`. Given an existing draft with no voice named, the auditor and editor treat the draft's own voice as the voice: its sentence lengths and its tone. They check only the tells and the links and skip the `voice_stats.py` comparison, since there's no profile to compare against. An edit keeps that voice. Flattening it into generic prose is a failure even when every check passes.

<!-- vale Microsoft.HeadingAcronyms = NO -->
## AI tells
<!-- vale Microsoft.HeadingAcronyms = YES -->

Run `${CLAUDE_SKILL_DIR}/../ai-tells-auditor/scripts/audit.sh` on the draft for the word-level tells Vale finds. Then read the draft against `${CLAUDE_SKILL_DIR}/../ai-tells-auditor/references/review-prompt.md` for what Vale can't see, such as invented specifics or false balance.

- Leave a `ConsequenceClause` hit that states a real cause. It's how prose links ideas, as in this sentence:

  <!-- vale off -->
  > The server is in the server zone, so the attacker moves to it.
  <!-- vale on -->

- Rewrite the sentence, not the word. Swapping "leverage" for "utilize" trades one tell for another.

## Linked sentences

Each sentence follows from the one before it. The words that tie them together are how the reader follows the argument, and without them the reader gets sentences side by side with no thread between them.

- Keep the linking words: because, so, which means, once, to answer that. A "because" or "so" clause that gives the reason is a link. Don't mistake it for an announcer and cut it.
- A link that states a cause or a result is a claim. Use one only where the source states that relation, like the server sentence in the "AI tells" section when the source says why the attacker moves. Otherwise join the sentences with `and` or a comma, or let their order carry the link.
- Fix a flagged phrase inside its own sentence. Don't split a connected sentence into short ones to clear a hit.
- Don't break up a sentence whose halves follow from each other, such as a step and its result. Split at ", and" only when a sentence runs past 40 words and its halves are unrelated claims.
- Treat a run of short, unlinked sentences as a failure. It's harder to read than the phrase it replaced.
