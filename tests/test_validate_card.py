"""Tests for skills/explaining-markets-model-card/scripts/validate_card.py.

Run from the repo root:  python3 -m unittest discover -s tests -v
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "explaining-markets-model-card"
sys.path.insert(0, str(SKILL / "scripts"))

import validate_card as vc  # noqa: E402

MINIMAL = (SKILL / "references" / "examples" / "minimal.md").read_text(encoding="utf-8")
SHOWCASE = (SKILL / "references" / "examples" / "showcase.md").read_text(encoding="utf-8")


def errors(text):
    return [i.message for i in vc.validate(text).errors]


def warnings(text):
    return [i.message for i in vc.validate(text).warnings]


def with_row(label, value, base=MINIMAL):
    out = []
    for line in base.split("\n"):
        if line.startswith("| %s |" % label):
            line = "| %s | %s |" % (label, value)
        out.append(line)
    return "\n".join(out)


class BundledFiles(unittest.TestCase):
    def test_examples_are_clean(self):
        for text in (MINIMAL, SHOWCASE):
            result = vc.validate(text)
            self.assertEqual([str(i) for i in result.issues], [])

    def test_template_fails_until_filled_in(self):
        template = (SKILL / "assets" / "template.md").read_text(encoding="utf-8")
        self.assertFalse(vc.validate(template).ok)

    def test_parsed_fields(self):
        result = vc.validate(MINIMAL)
        self.assertEqual(result.version, 1)
        self.assertEqual(result.disclosure, "minimal")
        self.assertEqual(result.fields["approach"], ["LLM / GenAI"])
        self.assertEqual(result.fields["models"], ["GPT-5.x"])
        self.assertEqual(
            sorted(result.fields),
            sorted(f["key"] for f in vc.load_taxonomy()["fields"]),
        )


class Marker(unittest.TestCase):
    def test_missing_marker(self):
        text = MINIMAL.split("\n", 1)[1]
        self.assertTrue(any("format marker" in e for e in errors(text)))

    def test_front_matter(self):
        text = "---\nname: x\n---\n" + MINIMAL
        self.assertTrue(any("front matter" in e for e in errors(text)))

    def test_unknown_disclosure_level(self):
        text = MINIMAL.replace("disclosure=minimal", "disclosure=open")
        self.assertTrue(any("disclosure must be one of" in e for e in errors(text)))

    def test_unsupported_version(self):
        text = MINIMAL.replace("em-model-card v1", "em-model-card v9")
        self.assertTrue(any("not supported" in e for e in errors(text)))


class Table(unittest.TestCase):
    def test_missing_table(self):
        text = "\n".join(l for l in MINIMAL.split("\n") if not l.startswith("|"))
        self.assertTrue(any("table is missing" in e for e in errors(text)))

    def test_row_order(self):
        lines = MINIMAL.split("\n")
        a = next(i for i, l in enumerate(lines) if l.startswith("| Approach"))
        lines[a], lines[a + 1] = lines[a + 1], lines[a]
        self.assertTrue(any("in this order" in e for e in errors("\n".join(lines))))

    def test_missing_row(self):
        text = "\n".join(l for l in MINIMAL.split("\n") if not l.startswith("| Models"))
        self.assertTrue(any("in this order" in e for e in errors(text)))

    def test_no_title(self):
        text = MINIMAL.replace("\n\nA general", "\n\n# My Agent\n\nA general", 1)
        msgs = errors(text)
        self.assertTrue(any("no '# ' title" in e for e in msgs))
        self.assertTrue(any("no heading above the table" in e for e in msgs))

    def test_lede_required(self):
        lines = MINIMAL.split("\n")
        del lines[2]
        self.assertTrue(any("lede" in e for e in errors("\n".join(lines))))


class Values(unittest.TestCase):
    def test_unknown_value_gets_suggestion(self):
        msgs = errors(with_row("Information set", "competition fact"))
        self.assertTrue(any("Did you mean 'competition facts'" in e for e in msgs))

    def test_wrong_case(self):
        msgs = errors(with_row("Approach", "hybrid"))
        self.assertTrue(any("Did you mean 'Hybrid'" in e for e in msgs))

    def test_approach_is_single_select(self):
        msgs = errors(with_row("Approach", "LLM / GenAI; Hybrid"))
        self.assertTrue(any("exactly one" in e for e in msgs))

    def test_ensemble_is_not_an_approach(self):
        self.assertTrue(errors(with_row("Approach", "Ensemble")))

    def test_canonical_order(self):
        msgs = errors(with_row("Information set", "filings; competition facts"))
        self.assertTrue(any("canonical order: competition facts; filings" in e for e in msgs))

    def test_separator(self):
        for bad in ("competition facts;filings", "competition facts ; filings"):
            self.assertTrue(any("exactly '; '" in e for e in errors(with_row("Information set", bad))))
        self.assertTrue(errors(with_row("Information set", "competition facts, filings")))

    def test_duplicates(self):
        msgs = errors(with_row("Information set", "filings; filings"))
        self.assertTrue(any("listed twice" in e for e in msgs))

    def test_sentinel_alone(self):
        msgs = errors(with_row("Information set", "competition facts; Not disclosed"))
        self.assertTrue(any("must appear alone" in e for e in msgs))
        self.assertEqual(errors(with_row("Information set", "Not disclosed")), [])

    def test_unknown_warns(self):
        text = with_row("Learning / adaptation", "Unknown")
        self.assertEqual(errors(text), [])
        self.assertTrue(any("'Unknown'" in w for w in warnings(text)))

    def test_single_pass_and_multi_stage(self):
        msgs = errors(with_row("Agent architecture", "single-pass; multi-stage"))
        self.assertTrue(any("cannot appear together" in e for e in msgs))

    def test_markup_in_value(self):
        msgs = errors(with_row("Approach", "`LLM / GenAI`"))
        self.assertTrue(any("plain text" in e for e in msgs))

    def test_prediction_construction_other(self):
        self.assertEqual(errors(with_row("Prediction construction", "Other")), [])


class Models(unittest.TestCase):
    def test_families_then_fixed_values(self):
        ok = with_row("Models", "Claude; GPT-5.x; boosted trees; embedding model")
        self.assertEqual(errors(ok), [])

    def test_families_alphabetical(self):
        msgs = errors(with_row("Models", "GPT-5.x; Claude"))
        self.assertTrue(any("alphabetically" in e for e in msgs))

    def test_family_after_fixed_value(self):
        msgs = errors(with_row("Models", "boosted trees; Claude"))
        self.assertTrue(any("AI families first" in e for e in msgs))

    def test_fixed_values_order(self):
        msgs = errors(with_row("Models", "neural network; linear"))
        self.assertTrue(any("canonical order: linear; neural network" in e for e in msgs))

    def test_model_id_rejected(self):
        for bad in ("gpt-5-nano-2025-08-07", "deepseek/deepseek-v4-flash", "claude-opus-4-8"):
            msgs = errors(with_row("Models", bad))
            self.assertTrue(any("looks like a model ID" in e for e in msgs), bad)

    def test_family_case(self):
        msgs = errors(with_row("Models", "claude"))
        self.assertTrue(any("exactly as 'Claude'" in e for e in msgs))

    def test_unlisted_family_allowed(self):
        self.assertEqual(errors(with_row("Models", "Grok")), [])

    def test_versioned_family_warns(self):
        self.assertTrue(any("version number" in w for w in warnings(with_row("Models", "Claude Opus 4.8"))))


class Sections(unittest.TestCase):
    def test_missing_section(self):
        text = MINIMAL.replace("## Data flow", "### Data flow")
        self.assertTrue(any("missing section '## Data flow'" in e for e in errors(text)))

    def test_order(self):
        text = MINIMAL.replace("## Data flow", "## TMP").replace("## Limitations", "## Data flow")
        text = text.replace("## TMP", "## Limitations")
        self.assertTrue(any("sections must appear in this order" in e for e in errors(text)))

    def test_extra_section(self):
        text = MINIMAL + "\n## Results\n\nBacktest numbers.\n"
        self.assertTrue(any("not one of the standard sections" in e for e in errors(text)))

    def test_subheadings_allowed(self):
        text = MINIMAL.replace("## Limitations\n", "## Limitations\n\n### Known gaps\n")
        self.assertEqual(errors(text), [])

    def test_empty_section(self):
        head, _sep, _tail = MINIMAL.partition("## Limitations")
        self.assertTrue(any("'Limitations' is empty" in e for e in errors(head + "## Limitations\n")))

    def test_prompt_section_needs_showcase(self):
        text = MINIMAL.replace(
            "## Data flow", "## Representative prompt\n\nPredict the return.\n\n## Data flow"
        )
        self.assertTrue(any("disclosure=showcase" in e for e in errors(text)))

    def test_deep_heading(self):
        text = MINIMAL + "\n##### Tiny\n\nText.\n"
        self.assertTrue(any("unstyled" in e for e in errors(text)))

    def test_heading_inside_code_block_ignored(self):
        text = SHOWCASE.replace("--- Inputs ---", "# not a heading\n--- Inputs ---")
        self.assertEqual(errors(text), [])


class PortalLimits(unittest.TestCase):
    def test_too_long(self):
        text = MINIMAL + "\n" + ("word " * 2500)
        self.assertTrue(any("refuses anything over 10000" in e for e in errors(text)))

    def test_length_counts_utf16_units(self):
        self.assertEqual(vc.js_length("a\U0001F600"), 3)

    def test_html(self):
        text = MINIMAL.replace("- Outputs are", "<details>x</details>\n- Outputs are")
        self.assertTrue(any("raw HTML" in e for e in errors(text)))

    def test_autolink_is_not_html(self):
        text = SHOWCASE.replace("## Data flow", "See <https://example.com>.\n\n## Data flow")
        self.assertEqual(errors(text), [])

    def test_image(self):
        text = MINIMAL + "\n![diagram](https://example.com/x.png)\n"
        self.assertTrue(any("images are not shown" in e for e in errors(text)))

    def test_relative_link(self):
        text = MINIMAL + "\nSee [the code](src/predict.py).\n"
        self.assertTrue(any("absolute https://" in e for e in errors(text)))

    def test_setext_heading(self):
        text = MINIMAL.replace("## Limitations", "Some text\n---\n\n## Limitations")
        self.assertTrue(any("turns the text above it into a heading" in e for e in errors(text)))


class MinimalLeakWarnings(unittest.TestCase):
    def test_code_block(self):
        text = MINIMAL + "\n```\nYou are a financial analyst.\n```\n"
        self.assertTrue(any("code block in a minimal card" in w for w in warnings(text)))

    def test_model_id(self):
        text = MINIMAL.replace("A hosted general-purpose", "gpt-5-nano-2025-08-07, a hosted general-purpose")
        self.assertTrue(any("exact model ID" in w for w in warnings(text)))

    def test_hyperparameter(self):
        text = MINIMAL.replace("Each event gets", "Temperature is 0.2. Each event gets")
        self.assertTrue(any("hyperparameters" in w for w in warnings(text)))

    def test_ordinary_hyphenated_words_do_not_warn(self):
        text = MINIMAL.replace("Each event gets", "A 5-minute, in-quarter, zero-shot step. Each event gets")
        self.assertEqual(warnings(text), [])

    def test_showcase_is_not_warned(self):
        self.assertEqual(warnings(SHOWCASE), [])


class CommandLine(unittest.TestCase):
    script = str(SKILL / "scripts" / "validate_card.py")

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, self.script, *args], capture_output=True, text=True
        )

    def test_ok(self):
        proc = self.run_cli(str(SKILL / "references" / "examples" / "minimal.md"))
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(proc.stdout.startswith("OK:"))

    def test_failure_exit_code(self):
        proc = self.run_cli(str(SKILL / "assets" / "template.md"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("FAILED:", proc.stdout)

    def test_json(self):
        proc = self.run_cli(str(SKILL / "references" / "examples" / "showcase.md"), "--json")
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["disclosure"], "showcase")
        self.assertEqual(data["fields"]["models"], ["DeepSeek"])

    def test_missing_file(self):
        self.assertEqual(self.run_cli("/nonexistent/card.md").returncode, 2)


if __name__ == "__main__":
    unittest.main()
