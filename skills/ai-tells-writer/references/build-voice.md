# Build a voice profile from writing samples

A voice profile tells the writer how a person writes. It has numbers measured from their samples, the habits to keep with new examples, and the habits to avoid. `${CLAUDE_SKILL_DIR}/voices/plain.md` shows the format.

Samples are often private: a book, client reports, emails. Keep them and the profile out of every repository. The profile describes the writing in your own words and never quotes it.

You need the samples (files or a folder) and a name for the voice, such as `my-voice`. Ask for either if it's missing.

## 1. Extract the samples

Make a scratch directory outside any repository, such as the session scratchpad. Convert each sample to plain text there:

```bash
textutil -convert txt -output <scratch>/sample1.txt "<sample1.docx>"   # macOS
pandoc -t plain -o <scratch>/sample2.txt "<sample2.docx>"              # anywhere
```

Markdown and plain text files can be used as they are. Drop the parts that aren't the writer's prose: tables of contents, indexes, copyright pages, code listings, tables, and long quotations from other people.

## 2. Measure

```bash
${CLAUDE_SKILL_DIR}/scripts/voice_stats.py <scratch>/*.txt
```

Copy the numbers into the profile's `Numbers` section and round them to a range the writer can aim for. A median sentence of 17.4 words becomes a target of 15 to 19 words.

## 3. Find the habits to avoid

```bash
${CLAUDE_SKILL_DIR}/../ai-tells-auditor/scripts/audit.sh --min=warning <scratch>/*.txt
```

Count the hits per rule. Each warning or error rule with many hits across the samples goes under `Habits to avoid`, with the rule name and what to write instead. Leave suggestion-level habits alone (passives, hedges, an occasional em dash): the auditor treats them as often fine, and they may be part of how the person sounds.

## 4. Find the habits to keep

Read enough of the samples to hear the writer: at least a few thousand words from different parts. Note how they:

- open a section and explain a term
- give an example or an instruction
- choose words, including the ones they never use

Write each habit as an instruction, with one or two example sentences. Write the examples yourself, on a made-up topic. Don't take them from the samples. Don't paraphrase a sample sentence either.

When the samples come from more than one author, describe one writer. Keep what they share and what the person asked for, and drop the habits that would make the voice sound like two people.

Leave person (I, we, you) out of the habits. The writer chooses it per piece, and the profile's `Person` section says so.

## 5. Check for copying

```bash
${CLAUDE_SKILL_DIR}/scripts/check_voice.py <profile> <scratch>/*.txt
```

It must print `TOTAL: 0`. If it finds a copied run, rewrite that line of the profile and run it again.

## 6. Save

Save the profile as `~/.claude/voices/<name>.md`. Never save it inside a repository. Tell the person the path, the numbers, the habits to keep and avoid in one line each, and that the scratch copies of the samples can be deleted.
