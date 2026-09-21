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

The abnormal (market-adjusted) stock return on the trading day after the earnings call, expressed as a percentile between 0 and 1 across all of the quarter's events. The model also gives a direction (up, neutral, or down) and a short rationale. Only the percentile is submitted; the rest is logged.

## Input context

Only the key-fact summary delivered with each event through the competition API. The model does not see the raw transcript, market or price data, analyst estimates, filings, or the web, and it has no tools.

## Model & harness

A hosted general-purpose language model, used through prompting with a structured-output framework that has the model reason before it answers. There is no task-specific training, fine-tuning, or use of worked examples. Each event gets one model call. Transient failures are retried; an answer that cannot be parsed falls back to a neutral prediction of 0.5.

## Data flow

Event notification → fetch the fact summary → one model call → percentile checked to lie between 0 and 1 → submitted.

## Limitations

- Prediction quality is bounded by the fact summary; nothing outside it is seen at prediction time.
- There is no market or price context, so the model cannot tell what was already expected.
- Outputs are stochastic: the same input can give different predictions across runs.
