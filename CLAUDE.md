# ai-tells

Run `python3 tests/test_tells.py` before every push.

## Versioning

Installed plugins update only when `version` in `.claude-plugin/plugin.json` changes. Bump it in the same commit as any change under `skills/`:

- Patch (0.1.1): a fix that keeps behavior the same.
- Minor (0.2.0): a new or removed rule, a changed pack pin, or a change to what the skill does.
- No bump: README, tests, evals.

After pushing a new version, tag it: `git tag v0.2.0 && git push --tags`. `python3 tests/test_tells.py` fails if `skills/` changed since the last tag without a bump.
