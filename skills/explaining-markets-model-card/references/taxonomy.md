# The six standardized fields

The table at the top of every card characterizes the agent along six dimensions so submissions can be compared, by people and by software, without disclosing implementation IP. In the table, classify; do not explain. Explanation belongs in the prose sections.

The same labels and ordering are stored in `assets/taxonomy.json`, which the validator reads. If this file and the JSON ever disagree, the JSON wins.

| Category | Question it answers | Select |
| --- | --- | --- |
| Approach | What broad kind of system is this? | one |
| Models | Which major model families are used? | many |
| Information set | What broad categories of information enter the prediction? | many |
| Learning / adaptation | How does the system learn from historical examples? | many |
| Agent architecture | At a high level, how is inference organized? | many |
| Prediction construction | What ultimately produces the submitted 0-1 prediction? | many |

## Rules that apply to every field

- Use the labels exactly as written here, including case, spacing, and the ` / ` inside labels.
- Separate multiple values with `; ` (semicolon, one space).
- List values in the canonical order given below, not in the order you found them.
- `Unknown`, `Not disclosed`, and `None` are sentinels. A sentinel always stands alone in its cell.
  - `Unknown`: the material is insufficient, ambiguous, or conflicting. Missing documentation means `Unknown`, not `Not disclosed`.
  - `Not disclosed`: the participant explicitly chose to withhold this.
  - `None`: the category is confidently absent.
- Do not guess. But do look properly before settling for `Unknown`, and tell the participant about any field you left `Unknown` so they can settle it; a published `Unknown` helps nobody.

## What counts as evidence

Classify the agent that is deployed, or about to be deployed, for the current competition submission. When sources conflict, prefer them in this order:

1. the active deployment path and its current runtime configuration;
2. configuration used by that path;
3. current implementation code;
4. current participant documentation or an existing model card;
5. tests and comments;
6. research logs, archived experiments, benchmarks, dead code.

Abandoned experiments, commented-out alternatives, unused dependencies, and optional branches are not part of the agent unless they clearly sit on the deployed path. A dependency in the lockfile is not evidence that a model is used.

Classify a component only if it materially contributes to the submitted prediction. A model used to pretty-print logs does not belong in the table.

## 1. Approach (choose one)

1. `LLM / GenAI`: generative AI materially drives the prediction, with no materially contributing trained ML or statistical component.
2. `Traditional ML`: one or more historically fitted, non-generative predictive models materially drive the prediction.
3. `Hybrid`: generative AI and traditional ML, statistical, or rule-based components both materially contribute.
4. `Rules / statistical`: fixed rules, formulas, or statistical procedures, with no materially contributing GenAI or historically trained ML model.
5. `Other`: none of the above reasonably describes the system.

"Ensemble" is not an approach. It is an architecture (field 5).

This field is what Official Rules §3 requires every card to state, so it should never be `Not disclosed`.

## 2. Models

Report only broad model families that materially contribute to the current prediction.

For generative AI, report the public family, never a specific checkpoint, minor version, size, or configuration:

- GPT-5 variants → `GPT-5.x`
- Claude variants → `Claude`
- Gemini variants → `Gemini`
- Qwen variants → `Qwen`
- Llama variants → `Llama`
- Mistral variants → `Mistral`
- DeepSeek variants → `DeepSeek`

Other public AI families may be reported at the same level of abstraction. A privately trained or fine-tuned generative model with no public family is `other`.

For non-generative models use these values:

1. `linear`
2. `boosted trees`
3. `neural network`
4. `embedding model`
5. `time-series model`
6. `Bayesian model`
7. `rules / statistical`
8. `other`

List the models that make the prediction. A calibration map, scaler, or other post-processing step fitted on top of a model is not a separate model here; it is reported as `calibrated` under Learning / adaptation. `rules / statistical` is for a rule set or statistical procedure that itself produces or materially shifts the prediction.

Order: AI families first, alphabetically; then the non-generative values in the order above. Example: `Claude; GPT-5.x; boosted trees; embedding model`.

Do not report estimator variants, dimensions, layer counts, model sizes, context lengths, quantization, or hyperparameters here, at either disclosure level. A showcase card can give exact model IDs in its Model & harness section; the table stays at family level so every card is comparable.

## 3. Information set

Use these values, in this order:

1. `competition facts`: the fact summaries, or any other substantive material, that the competition supplies: delivered for the event through the official API, or taken from the competition's historical archive to fit a model. Reading only identifiers from the event notification (ticker, timestamps, the cutoff) does not count.
2. `call / transcript`: earnings-call audio or transcripts obtained outside the competition API.
3. `earnings / fundamentals`
4. `estimates`
5. `prices / returns`
6. `filings`
7. `historical company information`
8. `peers / industry`
9. `news / web`
10. `proprietary / other`: proprietary, alternative, or otherwise nonstandard information, without identifying the source.

Classify categories of information, not individual variables or features. Include information used to train or fit a model, not only what is read at prediction time. A quantity built from two categories belongs to both: an earnings surprise measured against analyst consensus is `earnings / fundamentals; estimates`.

Everything a submission uses must respect the event's `knowledge_cutoff` (Official Rules §4). If what you find appears to use information from after the cutoff, do not describe it as compliant; tell the participant what you saw.

## 4. Learning / adaptation

Use these values, in this order:

1. `zero-shot / prompted`: a foundation model is used through prompting, without task-specific parameter training.
2. `in-context examples`: labeled or outcome-bearing examples are provided in context at prediction time.
3. `historically trained ML`: a non-generative prediction model is fitted using historical examples or outcomes.
4. `fine-tuned LLM`: an LLM has task-specific parameter updates.
5. `calibrated`: a learned or fitted calibration step maps model output to the submitted score.
6. `online / in-quarter updating`: parameters, calibration, training data, or learned model state update using information or outcomes arriving during the active competition period.

`calibrated` applies when any materially contributing component has a fitted calibration step, even if the final blend is not recalibrated. Fetching fresh information or retrieving new documents is not by itself `online / in-quarter updating`. A prompt that merely states base rates is not `in-context examples` and not `calibrated`. A prompt whose wording was tuned against historical outcomes by an optimizer is still `zero-shot / prompted` unless it carries examples; mention the tuning in prose if the participant wants it known.

## 5. Agent architecture

Use these values, in this order:

1. `single-pass`: one substantive inference or prediction stage.
2. `multi-stage`: substantive intermediate outputs feed later stages.
3. `retrieval-augmented`: prediction-time retrieval supplies external or historical context.
4. `tool-using`: an AI model or agent invokes tools, search, APIs, or callable functions during inference. Ordinary code loading fixed inputs is not enough.
5. `multiple agents / roles`: distinct specialist agents or explicit roles materially contribute.
6. `self-consistency / committee`: multiple independent samples or judgments from substantially the same approach are combined.
7. `ensemble`: materially distinct models or prediction pipelines are combined.

`single-pass` and `multi-stage` are mutually exclusive. A model that reasons before answering within one call is still `single-pass`. Fetching the event's inputs, parsing the output, clamping it to [0, 1], and applying a fitted calibration map are not stages. `multi-stage` means one substantive model's output becomes another's input. Independent pipelines that each make one pass and are then blended are `single-pass; ensemble`.

## 6. Prediction construction

Use these values, in this order:

1. `direct LLM score`: an LLM directly produces or materially determines the submitted continuous prediction.
2. `classification → score`: categories or class probabilities are converted into the submitted score.
3. `regression`: a regression model estimates the target or a quantity mapped directly to it.
4. `ranking`: a ranking model or cross-sectional ordering materially determines the prediction.
5. `similarity / retrieval`: retrieved analogues or similarity scores materially determine the prediction.
6. `weighted / learned ensemble`: multiple forecasts are combined through a fixed or learned aggregation rule.
7. `Other`: none of the above applies.

If an LLM outputs both a class and a number and the number is what gets submitted, that is `direct LLM score`. It is `classification → score` only when code turns the class or class probabilities into the number. Averaging repeated draws from the same model is a fixed aggregation rule, so an entry that submits the mean of several LLM draws is `direct LLM score; weighted / learned ensemble` here and `self-consistency / committee` under Agent architecture.

The arrow is the character `→` (U+2192), not `->`.
