---
name: explaining-markets-model-card
description: >
  Write or update the model card for an Explaining Markets competition
  submission (explainingmarkets.ai). Inspects the agent's code, classifies it
  into the competition's six standardized categories, and writes MODEL_CARD.md
  in the fixed format the portal and leaderboard expect, at the disclosure level
  the participant chooses. Use whenever someone mentions a model card, prize
  eligibility, describing or documenting their submission or agent, or the
  portal's Public Profile tab for Explaining Markets, and when an existing
  MODEL_CARD.md needs refreshing after the method changed.
license: MIT
compatibility: >
  Works in any agent that can read files. The bundled validator needs Python
  3.8+ (standard library only); without Python, a manual checklist is provided.
---

# Explaining Markets model card

Every submission to the Explaining Markets competition needs a model card to be prize-eligible (Official Rules §3). The card is public: it gets its own page, and its opening lines appear when someone hovers over the submission on the leaderboard. Cards follow one fixed format so that submissions can be compared side by side and read by software. Your job is to write that card from the participant's code, asking them as little as possible, and to get the facts right, because the participant is accountable for the card's accuracy and cards can be audited.

You write a file. You never publish anything; the participant pastes the card into the portal themselves.

## The flow

Work through these in order. In the usual case the participant answers one question (two if the repo holds several submissions) and then reviews the result.

### 1. Read the code

Find the path a live event takes: webhook or entry point → inputs fetched → model or models → the number posted to the competition API as `predicted_percentile`. Classify what is on that path, not what is lying around the repo. `references/taxonomy.md` sets out the evidence order (deployed path and its configuration first; experiments, notebooks, and dead code last) and you will need it again in step 4, so read it now.

Read `.env.example` and the code that reads the environment, never `.env` or other secret files. You need variable names, not values.

If the project already has a `MODEL_CARD.md` (or `MODEL_CARD.<name>.md` files), this is an update: go to "Updating a card" below.

If the repo is not a submission (nothing in it produces and submits a prediction; for example a data-exploration or scoring toolkit), or there is no code to read, say so in one sentence and ask the participant to describe their system in a few sentences: what goes in, what models or methods, how the final number is produced. Then skip step 2 and continue from step 3, using their description as the evidence.

Sometimes the deployed path is only partly visible: key functions are stubs, the model file is missing, the serving code lives elsewhere. Classify from what you can see, do not fill gaps with guesses, and put what you could not see in the review message in step 6. Leave out of the card any behavior you could not observe (failure handling, for example) rather than inventing it.

### 2. Work out which submission this is

A submission is one leaderboard entry with its own API key, signing secret, and public name. Most repos hold exactly one. Some deploy several from the same code. Signs of that:

- a setting or environment variable that selects a variant (a model name, a strategy enum) at deploy time;
- several sets of competition credentials, such as `EM_API_KEY_A` and `EM_API_KEY_B`, or suffixed webhook secrets;
- several deploy targets, app names, or entry points that each post predictions.

If you find one submission, say nothing and move on. If the participant already named the one they mean, use it. Otherwise, when you find more than one, ask which the card is for, listing them by the names the code uses, and mention that each submission needs its own card. Wait for the answer.

### 3. Ask how much to disclose

Ask this once, now, in these words, and wait for the answer. If your environment has a way to present choices, use it; otherwise ask in plain text.

> How much detail should your public model card show?
>
> 1. **Protect my IP** (default). Describes your approach in broad categories only: no prompts, exact model versions, features, or settings.
> 2. **Showcase my work.** Adds specifics, such as exact models, settings, and how the pipeline fits together, to show the engineering behind your system.
>
> Either way the card is public once you publish it, and the comparison table at the top is the same.

Option 1 is `minimal`; option 2 is `showcase`. If the participant already told you which they want, do not ask again. If nobody is there to answer (a non-interactive run), use `minimal` and say that you did.

Do not ask anything else before drafting. Questions cost the participant more than they cost you; anything you could not determine goes into the review message in step 6, where one reply can fix it.

### 4. Classify and draft

Fill in the six-row table using `references/taxonomy.md`. The labels, their order, and the `; ` separator are a contract that software depends on, so copy labels exactly. The table is the same at both disclosure levels and always stays at the level of families and categories.

Then write the lede and the sections, following `references/card-format.md`, which explains the skeleton, what each section is for, what each disclosure level includes and leaves out, and what the portal does to Markdown. Start from `assets/template.md`. The two files in `references/examples/` show a finished card at each level; match their length and tone. They are examples of form only. Take every fact from the participant's project, even if it looks like the system in an example.

The card is a public description of the system and nothing else. It never mentions the repository, you, this skill, or what could or could not be verified; those go to the participant in step 6. If you cannot see something, leave it out of the card rather than hedging about it there.

Write for a reader who knows finance and machine learning but has never seen this code. Plain sentences, present tense, no marketing. Describe what the system does, not how good it is: no performance claims, backtest numbers, or comparisons with other entries.

If you noticed something that looks like it breaks the competition's `knowledge_cutoff` rule (using information from after the event's cutoff, other than what the competition API supplies), do not paper over it in the card. Tell the participant what you saw.

### 5. Validate

Write the card to `MODEL_CARD.md` at the root of the participant's project. If the repo holds several submissions, name it after the identifier the code uses for that one, for example `MODEL_CARD.gpt5nano.md`. Then run the validator that sits next to this file:

```
python3 scripts/validate_card.py /path/to/MODEL_CARD.md
```

Resolve `scripts/validate_card.py` relative to this skill's folder. Fix every `ERROR` and run it again until it prints `OK`. Treat each `WARN` as a question: in a `minimal` card a warning usually marks a detail that should come out. If Python is not available, use the manual checklist at the end of `references/card-format.md`.

### 6. Hand over

Reply with a short message, not a report. Include:

1. Where the file is, and the six classifications in one compact list so the participant can check them at a glance.
2. **Please check**: the few things you assumed because code cannot show them. Typical ones: that no model was trained or tuned on historical data outside this repo; that no information is used beyond what you found; that the deployed configuration matches the repo. Include any field you had to leave `Unknown`, with what would settle it. If they correct you, update the card and re-validate.
3. For a showcase card: that you left the verbatim prompt out, and that they can ask you to add it.
4. How to publish: in the portal, open the submission → **Public Profile** tab → paste the contents of the file into **Model card** → **Preview** → **Publish model card**. It goes public immediately, needs the editor or admin role, and can be edited or removed later.
5. One line on upkeep: the rules require the card to stay accurate, so re-run this skill if the method changes materially.

## Updating a card

When a card already exists (with several, work out which one the participant means from what they said, and ask only if you cannot tell):

1. Read its marker line to get the disclosure level. Keep that level unless the participant asks to change it, so there is no disclosure question.
2. Re-read the code as in steps 1 and 2, without asking anything, and compare it with what the card says.
3. Change only what is no longer true. It is the participant's card: keep their wording wherever it is still accurate, even where you would have phrased it differently. Remove their text only if it is now false or discloses something their disclosure level leaves out, and say so in the handover.
4. Validate, then hand over as in step 6, leading with a short list of what changed and why. If nothing material changed, say so and leave the file alone.

A card written by hand in some other format counts as documentation (evidence level 4), not as a card to update. Write a fresh one and tell the participant you used theirs as a source.

## Files in this skill

- `references/taxonomy.md`: the six fields, every allowed value, definitions, ordering, evidence rules. Read before classifying.
- `references/card-format.md`: skeleton, section purposes, disclosure levels, portal rendering limits, manual checklist. Read before drafting.
- `references/examples/minimal.md`, `references/examples/showcase.md`: finished cards.
- `assets/template.md`: the empty skeleton.
- `assets/taxonomy.json`: the labels in machine-readable form; the validator reads it.
- `scripts/validate_card.py`: the validator. `--json` prints the parsed fields.
