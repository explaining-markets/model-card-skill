# Explaining Markets model card skill

[![CI](https://github.com/explaining-markets/model-card-skill/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/explaining-markets/model-card-skill/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/explaining-markets/model-card-skill?sort=semver)](https://github.com/explaining-markets/model-card-skill/releases)
[![License: MIT](https://img.shields.io/github/license/explaining-markets/model-card-skill)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](skills/explaining-markets-model-card/scripts/validate_card.py)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-blue)](https://agentskills.io)

A skill for AI coding agents that writes the model card for your [Explaining Markets](https://explainingmarkets.ai) submission. It reads your code, fills in the competition's standard card format, and leaves you a `MODEL_CARD.md` to paste into the portal. A submission needs a model card to be prize-eligible.

It works in Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, and other agents that support [Agent Skills](https://agentskills.io).

## Use it

Open your agent in the folder that holds your submission's code and paste this:

```text
Install the Explaining Markets model card skill from https://github.com/explaining-markets/model-card-skill by following INSTALL.md in that repo, then use it to write a model card for this project.
```

Your agent will ask permission to download the skill, then get to work. You will be asked one question:

> How much detail should your public model card show?
>
> 1. **Protect my IP** (default). Describes your approach in broad categories only: no prompts, exact model versions, features, or settings.
> 2. **Showcase my work.** Adds specifics, such as exact models, settings, and how the pipeline fits together, to show the engineering behind your system.

If your repo deploys more than one submission, it will also ask which one the card is for.

When it finishes you get `MODEL_CARD.md` and a short list of anything it had to assume. Check that list: you are responsible for the card being accurate (Official Rules §3). Then, in the portal, open your submission → **Public Profile** → paste the file's contents into **Model card** → **Preview** → **Publish model card**. The card is public as soon as you publish it. You can edit or remove it later.

Next time, the skill is already installed. Just ask: "Update the model card for my Explaining Markets submission." Do this whenever your method changes materially; the rules require the card to stay current.

## What the card looks like

Every card has the same shape: a one-or-two sentence summary, a six-row classification table, then five short sections.

```markdown
<!-- em-model-card v1 disclosure=minimal -->

A general-purpose language model reads the competition's earnings-call fact summary and predicts where the stock's next-day abnormal return will rank. It sees nothing else.

| Category | Classification |
| --- | --- |
| Approach | LLM / GenAI |
| Models | GPT-5.x |
| Information set | competition facts |
| Learning / adaptation | zero-shot / prompted |
| Agent architecture | single-pass |
| Prediction construction | direct LLM score |

## What is predicted
## Input context
## Model & harness
## Data flow
## Limitations
```

The table uses fixed labels so submissions can be compared, and it is the same whichever disclosure level you choose. Full examples: [protect my IP](skills/explaining-markets-model-card/references/examples/minimal.md), [showcase my work](skills/explaining-markets-model-card/references/examples/showcase.md). The labels and their definitions are in [taxonomy.md](skills/explaining-markets-model-card/references/taxonomy.md).

The skill never sees your secrets (it reads `.env.example`, not `.env`), never publishes anything, and sends nothing anywhere. It is a folder of Markdown instructions plus one small Python script that checks the card's format; read it all [here](skills/explaining-markets-model-card).

## Other ways to install

The prompt above is all most people need. If you prefer a package manager:

| Tool | Install | Update |
| --- | --- | --- |
| GitHub CLI (2.90+) | `gh skill install explaining-markets/model-card-skill explaining-markets-model-card --agent claude-code --scope user` | `gh skill update` |
| [skills](https://github.com/vercel-labs/skills) (Node) | `npx skills add explaining-markets/model-card-skill -g -a claude-code` | `npx skills update -g` |
| Claude Code plugin | `/plugin marketplace add explaining-markets/model-card-skill` then `/plugin install explaining-markets@explaining-markets` | `/plugin marketplace update explaining-markets` |
| By hand | Copy `skills/explaining-markets-model-card/` into `~/.claude/skills/` (Claude Code) or `~/.agents/skills/` (everything else) | Copy it again |

For the first two, replace `claude-code` with your agent: `codex`, `cursor`, `gemini-cli`, `github-copilot`, and so on.

Once installed, invoke it by name if your agent does not pick it up on its own: `/explaining-markets-model-card` in Claude Code, `$explaining-markets-model-card` in Codex.

## Check a card yourself

```sh
python3 skills/explaining-markets-model-card/scripts/validate_card.py MODEL_CARD.md
```

Python 3.8+, no dependencies. Add `--json` to get the parsed classification.

## For developers

```sh
python3 -m unittest discover -s tests -v
```

The card format is versioned (`em-model-card v1`). The labels live in [`taxonomy.json`](skills/explaining-markets-model-card/assets/taxonomy.json), which the validator reads and which other software can reuse. Changes are listed in [CHANGELOG.md](CHANGELOG.md).

MIT licensed.
