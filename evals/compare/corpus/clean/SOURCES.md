<!-- vale off -->
# Clean corpus sources

Human prose written before LLM chat tools existed. `compare_linters.py` counts every alert on these files as noise.

None of these files were used to tune the rules. The rules were tuned on the 2019 Rust Book, so it's left out here.

| File | Source | License |
| --- | --- | --- |
| `go-blog-errors-are-values.md` | Rob Pike, "Errors are values", The Go Blog, 2015 | CC BY 4.0 |
| `go-blog-defer-panic-and-recover.md` | Andrew Gerrand, "Defer, Panic, and Recover", The Go Blog, 2010 | CC BY 4.0 |
| `go-blog-strings.md` | Rob Pike, "Strings, bytes, runes and characters in Go", The Go Blog, 2013 | CC BY 4.0 |
| `go-blog-laws-of-reflection.md` | Rob Pike, "The Laws of Reflection", The Go Blog, 2011 | CC BY 4.0 |
| `twain-cooper.md` | Mark Twain, "Fenimore Cooper's Literary Offences", 1895, Project Gutenberg #3172 | Public domain |

The Go posts come from `golang/website/_content/blog/` and the Twain essay from Project Gutenberg. Changes from the originals:

- Paragraphs are joined onto one line, so `Custom.SplitSentence` (it flags a sentence broken across lines) doesn't fire on every hard wrap.
- Front matter is replaced by the title as a heading, and the Go site's template lines (`{{...}}`, `.code`, `.play`) are dropped.
- The Gutenberg header, license, and credits are removed.
