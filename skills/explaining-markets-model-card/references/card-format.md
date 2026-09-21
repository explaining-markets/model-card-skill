# Card format (em-model-card v1)

The participant pastes the card into a Markdown box in the competition portal. It becomes a public page the moment they publish it, and the top of it appears in a small preview when someone hovers over the submission's name on the leaderboard. The format below is built around what that portal does with Markdown.

## Skeleton

Start from `assets/template.md`. In order:

1. **Marker**, line 1, exactly `<!-- em-model-card v1 disclosure=minimal -->` or `<!-- em-model-card v1 disclosure=showcase -->`. The portal does not display it; software that reads cards uses it to tell the format version and disclosure level.
2. **No `#` title.** The public page already prints the submission's name as its title, so a title in the card shows up twice.
3. **Lede.** One or two sentences, about 200 characters: what the system is and what information it sees. The hover preview shows roughly the first five lines of the card, so a short lede lets the top of the table show as well. Say it plainly; this is the only part many readers will see.
4. **The classification table**, directly after the lede with no heading above it. Header `| Category | Classification |`, then the six rows in fixed order. Labels and rules are in `references/taxonomy.md`. Cells are plain text: no backticks, bold, or links.
5. **Sections**, as `##` headings with exactly these names, in this order:
   - `## What is predicted`
   - `## Input context`
   - `## Model & harness`
   - `## Representative prompt` (showcase only, and only if the participant asks for it)
   - `## Data flow`
   - `## Limitations`

   No other `##` sections. Use `###` or `####` inside a section if it needs structure. Every section needs content; two or three sentences is enough.

## What each section is for

- **What is predicted**: the target (the stock's next-trading-day abnormal return, as a 0-1 percentile across the quarter's events), plus anything else the system produces on the way, and what is actually submitted.
- **Input context**: what the system sees at prediction time and, if a model was fitted, what it was fitted on. Saying what it does not see is as useful as saying what it does.
- **Model & harness**: what kind of model or models, how they are run, how a prediction is assembled, and what happens on failure (retries, fallback value, no submission).
- **Representative prompt**: a short explanation of how the prompt is built, then the prompt in a fenced code block.
- **Data flow**: one line, stages joined by `→`, from event notification to submitted number.
- **Limitations**: three to five bullets a careful reader should know: blind spots, sources of randomness, dependence on third parties, regimes where it is likely to be wrong.

The card describes the method as it runs now. Earlier configurations, past experiments, and logging or monitoring that does not affect the prediction stay out, unless predictions already on the leaderboard were made a materially different way; then one Limitations bullet saying so is enough.

## Disclosure levels

The table is identical at both levels. Only the prose differs.

**minimal** (the default): describe the approach in broad categories. Leave out:

- prompts, system instructions, prompt templates, reasoning traces;
- exact model IDs, versions, sizes, and the services they are reached through (say "a hosted general-purpose language model", not the checkpoint);
- feature names, definitions, transformations, or lists;
- coefficients, blend weights, thresholds, cutoffs, model weights (saying that forecasts are combined "with fixed weights" is fine; the weights are not);
- hyperparameters, seeds, training recipes, tuning procedures;
- exact training windows or how samples were built;
- retrieval queries, ranking logic, filters, heuristics;
- names of proprietary data providers or datasets;
- file paths, function names, code structure, code snippets.

The test for minimal: could a competitor rebuild a meaningful part of the system from this card? If a detail is not needed to understand what kind of system it is, leave it out. Official Rules §3 says participants never have to disclose these things; the card still has to be a meaningful, accurate, high-level description.

**showcase**: the participant wants readers to see the engineering. Add the specifics that show it: exact model IDs and how they are served, sampling settings, the frameworks used, pipeline stages and what passes between them, how multiple samples or models are combined, fallback behavior, training data categories and validation approach. `references/examples/showcase.md` shows the level of detail. The verbatim prompt is the most sensitive item, so leave the Representative prompt section out unless the participant says they want it.

**At both levels, never include**: API keys, secrets, webhook URLs, private endpoints, environment values, personal information about teammates, or anything from a `.env` file. Do not repeat the repo, paper, website, or social links; the portal shows those separately.

## What the portal does to Markdown

- Tables, fenced code blocks, lists, bold, italics, inline code, links, strikethrough, footnotes: shown.
- Raw HTML (`<br>`, `<details>`, `<sub>`, comments): deleted without a trace. The marker on line 1 relies on this.
- Images: removed. No badges, logos, or diagrams.
- Math (`$...$`): not rendered. Write formulas as inline code.
- YAML front matter: shown as garbage.
- A line of `---` directly under text turns that text into a heading. Leave a blank line before any horizontal rule.
- `#####` and `######`: unstyled, smaller than body text. Stop at `####`.
- Links must be absolute `https://` URLs.
- Hard limit of 10,000 characters; aim for 6,000 or fewer. A minimal card is usually under 2,500.

## Checking the card

Run the validator from the skill folder; it checks everything on this page that can be checked mechanically:

```
python3 scripts/validate_card.py path/to/MODEL_CARD.md
```

Fix every `ERROR`. Read every `WARN`: in a minimal card, warnings point at likely leaks (code blocks, exact model IDs, hyperparameters, URLs) and each one should be either removed or kept on purpose.

If Python is not available, check by hand:

1. Line 1 is the marker, with the right disclosure level.
2. No `#` title; nothing but the lede between the marker and the table.
3. Table has the exact header and the six rows in order.
4. Every value is an exact label from `references/taxonomy.md`, in canonical order, joined by `; `.
5. A sentinel (`Unknown`, `Not disclosed`, `None`) stands alone in its cell.
6. Approach has exactly one value. `single-pass` and `multi-stage` do not appear together.
7. Models lists families, not model IDs; AI families alphabetically, then the fixed values in order.
8. The required `##` sections are all present, in order, each with content; no other `##` sections.
9. `## Representative prompt` appears only in a showcase card.
10. No HTML other than the marker, no images, no relative links, under 10,000 characters.
11. Minimal card: nothing from the leave-out list above.
