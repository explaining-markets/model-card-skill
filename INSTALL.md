# Installing the skill (instructions for the AI agent)

You are an AI coding agent and your user asked you to install the Explaining Markets model card skill. A skill is a folder of instructions; installing it means copying one folder into the place you look for skills. It takes three commands. There is nothing to build and nothing runs during installation.

## 1. Pick the destination

| You are | Install to |
| --- | --- |
| Claude Code | `~/.claude/skills/explaining-markets-model-card` |
| Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode, Goose, Amp, or anything else | `~/.agents/skills/explaining-markets-model-card` |

If you know your own documentation names a different user-level skills folder, use that one instead.

## 2. Copy the folder

Substitute the destination's parent folder for `DEST` (`~/.claude/skills` or `~/.agents/skills`):

```sh
TMP="$(mktemp -d)"
git clone --depth 1 https://github.com/explaining-markets/model-card-skill.git "$TMP/model-card-skill"
mkdir -p DEST
rm -rf DEST/explaining-markets-model-card
cp -R "$TMP/model-card-skill/skills/explaining-markets-model-card" DEST/
rm -rf "$TMP"
```

If the user pointed you at a local copy of this repository instead of the GitHub URL, skip the clone and copy `skills/explaining-markets-model-card` from that folder.

The `rm -rf` of the old copy makes this the update procedure as well: run it again to get the latest version. If `git` is unavailable, download `https://github.com/explaining-markets/model-card-skill/archive/refs/heads/main.zip`, unzip it, and copy the same folder.

Check that `DEST/explaining-markets-model-card/SKILL.md` exists.

## 3. Use it now

Skills are often only discovered when a session starts, so do not wait for it to show up in your skill list. If the user also asked for a model card, open `DEST/explaining-markets-model-card/SKILL.md` now and follow it, reading the other files it points to from that same folder.

If the user only asked you to install it, tell them it is installed, that it will be available by name (`explaining-markets-model-card`) in new sessions, and that they can ask for "a model card for my Explaining Markets submission" at any time.

## Uninstall

Delete the `explaining-markets-model-card` folder from the destination above.
