#!/usr/bin/env python3
"""Validate an Explaining Markets model card (format em-model-card v1).

Usage:
    python3 validate_card.py MODEL_CARD.md            # human-readable report
    python3 validate_card.py MODEL_CARD.md --json     # parsed fields + issues

Exit status is 0 when there are no errors (warnings are allowed) and 1
otherwise. Standard library only, so it runs wherever Python 3.8+ does.

The rules come from two places: the labels, ordering and section names live in
../assets/taxonomy.json (shared with anything else that parses cards), and the
rendering limits mirror the competition portal, which shows cards with
react-markdown + remark-gfm, deletes raw HTML, drops images, and caps the card
at 10,000 characters.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "assets" / "taxonomy.json"

MARKER_RE = re.compile(r"^<!-- em-model-card v(\d+) disclosure=([A-Za-z-]+) -->$")
ATX_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
SETEXT_RE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
TABLE_SEP_RE = re.compile(r"^\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)+\|?[ \t]*$")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
HTML_RE = re.compile(r"<(?!https?://|mailto:)[A-Za-z/!][^>]*>")
IMAGE_RE = re.compile(r"!\[")
LINK_RE = re.compile(r"\]\(\s*<?([^)\s>]+)")
MATH_RE = re.compile(r"\$\$|\$[^\s$][^$\n]*[^\s$]\$")
URL_RE = re.compile(r"https?://")
# Lowercase, starts with a letter, has a hyphen and a digit: gpt-5-nano,
# deepseek-v4-flash, claude-opus-4-8, gemini-2.5-flash, openai/gpt-5-nano.
MODEL_ID_RE = re.compile(r"(?<![\w/-])[a-z][a-z0-9.]*(?:[-/][a-z0-9.]+)+(?![\w-])")
HYPERPARAM_RE = re.compile(
    r"\b(temperature|top_p|top_k|max_tokens|learning[_ ]rate|n_estimators|max_depth)\b",
    re.IGNORECASE,
)


class Issue:
    def __init__(self, severity, line, message):
        self.severity = severity  # "ERROR" or "WARN"
        self.line = line  # 1-based, or None for whole-file issues
        self.message = message

    def __str__(self):
        where = "line %d: " % self.line if self.line else ""
        return "%-5s %s%s" % (self.severity, where, self.message)

    def as_dict(self):
        return {"severity": self.severity, "line": self.line, "message": self.message}


class Result:
    def __init__(self):
        self.issues = []
        self.version = None
        self.disclosure = None
        self.fields = {}
        self.chars = 0

    def error(self, line, message):
        self.issues.append(Issue("ERROR", line, message))

    def warn(self, line, message):
        self.issues.append(Issue("WARN", line, message))

    @property
    def errors(self):
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warnings(self):
        return [i for i in self.issues if i.severity == "WARN"]

    @property
    def ok(self):
        return not self.errors

    def as_dict(self):
        return {
            "ok": self.ok,
            "version": self.version,
            "disclosure": self.disclosure,
            "chars": self.chars,
            "fields": self.fields,
            "issues": [i.as_dict() for i in sorted(self.issues, key=_issue_key)],
        }


def _issue_key(issue):
    return (issue.line or 0, issue.severity)


def load_taxonomy(path=TAXONOMY_PATH):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def js_length(text):
    """Length as the portal counts it (JavaScript String.length)."""
    return len(text.encode("utf-16-le")) // 2


def _fence_mask(lines):
    """True for every line that is a code-fence delimiter or inside a fence."""
    mask = []
    open_char = None
    for line in lines:
        m = FENCE_RE.match(line)
        if open_char is None:
            if m:
                open_char = m.group(1)[0]
                mask.append(True)
            else:
                mask.append(False)
        else:
            mask.append(True)
            if m and m.group(1)[0] == open_char:
                open_char = None
    return mask


def _split_row(line):
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", body)]


def _looks_like_model_id(value):
    return (
        " " not in value
        and value == value.lower()
        and any(ch in value for ch in "-/:")
        and any(ch.isalpha() for ch in value)
    )


def _suggest(value, candidates):
    for cand in candidates:
        if cand.casefold() == value.casefold():
            return cand
    close = difflib.get_close_matches(value, candidates, n=1, cutoff=0.6)
    return close[0] if close else None


def _check_field(result, line_no, field, raw, taxonomy):
    label = field["label"]
    sentinels = taxonomy["sentinels"]
    sep = taxonomy["separator"]

    if not raw:
        result.error(line_no, "%s: value is empty." % label)
        return []
    if raw == "VALUE" or raw.startswith("VALUE;"):
        result.error(line_no, "%s: template placeholder was not replaced." % label)
        return []
    if any(ch in raw for ch in "`*_[]"):
        result.error(
            line_no,
            "%s: use plain text labels (no backticks, emphasis, or links)." % label,
        )

    parts = [p.strip() for p in raw.split(";")]
    if any(not p for p in parts):
        result.error(line_no, "%s: empty value between separators." % label)
        parts = [p for p in parts if p]
    if raw != sep.join(parts):
        result.error(
            line_no, "%s: separate values with exactly '; ' (semicolon, one space)." % label
        )
    if len(set(parts)) != len(parts):
        result.error(line_no, "%s: a value is listed twice." % label)

    used_sentinels = [p for p in parts if p in sentinels]
    if used_sentinels and len(parts) > 1:
        result.error(
            line_no,
            "%s: '%s' must appear alone, never next to another value."
            % (label, used_sentinels[0]),
        )
        return parts
    if used_sentinels:
        if used_sentinels[0] == "Unknown":
            result.warn(
                line_no,
                "%s is 'Unknown' and will be published that way; ask the "
                "participant if they can settle it." % label,
            )
        return parts

    if field["select"] == "single" and len(parts) != 1:
        result.error(line_no, "%s: choose exactly one value." % label)

    fixed = field["values"]
    open_vocab = field.get("open_vocabulary", False)
    families, canon = [], []
    for part in parts:
        if part in fixed:
            canon.append(part)
            continue
        hint = _suggest(part, fixed + sentinels + field.get("known_ai_families", []))
        if not open_vocab:
            msg = "%s: '%s' is not a standardized value." % (label, part)
            if hint:
                msg += " Did you mean '%s'?" % hint
            result.error(line_no, msg)
            continue
        # Open vocabulary (Models): anything else is a generative-AI family.
        if hint and hint.casefold() == part.casefold() and hint != part:
            result.error(line_no, "%s: write '%s' exactly as '%s'." % (label, part, hint))
        elif _looks_like_model_id(part):
            result.error(
                line_no,
                "%s: '%s' looks like a model ID. The table reports the public "
                "family (for example 'GPT-5.x', 'Claude', 'DeepSeek'); exact IDs "
                "belong in the Model & harness section of a showcase card." % (label, part),
            )
        elif part not in field.get("known_ai_families", []) and re.search(r"\d", part):
            result.warn(
                line_no,
                "%s: '%s' contains a version number; report the family rather "
                "than a specific version unless the family name includes it." % (label, part),
            )
        families.append(part)

    if open_vocab:
        seen_fixed = False
        for part in parts:
            if part in fixed:
                seen_fixed = True
            elif seen_fixed:
                result.error(
                    line_no,
                    "%s: list AI families first, then the non-generative values." % label,
                )
                break
        if families != sorted(families, key=str.casefold):
            result.error(line_no, "%s: list AI families alphabetically." % label)

    order = [fixed.index(p) for p in canon]
    if order != sorted(order):
        wanted = sep.join(sorted(canon, key=fixed.index))
        result.error(
            line_no, "%s: values must follow the canonical order: %s" % (label, wanted)
        )

    for group in field.get("mutually_exclusive", []):
        hit = [p for p in parts if p in group]
        if len(hit) > 1:
            result.error(
                line_no, "%s: '%s' cannot appear together." % (label, "' and '".join(hit))
            )
    return parts


def validate(text, taxonomy=None):
    taxonomy = taxonomy or load_taxonomy()
    result = Result()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    result.chars = js_length(text)
    lines = text.split("\n")
    fenced = _fence_mask(lines)
    # Prose with inline code blanked out, so identifiers in backticks do not
    # trip the HTML, link, or math checks.
    prose = [
        "" if fenced[i] else INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)
        for i, line in enumerate(lines)
    ]

    # --- marker -----------------------------------------------------------
    first = lines[0].strip() if lines else ""
    m = MARKER_RE.match(first)
    if first == "---":
        result.error(1, "YAML front matter is not supported; line 1 must be the format marker.")
    elif not m:
        result.error(
            1,
            "line 1 must be the format marker, e.g. "
            "'<!-- em-model-card v%d disclosure=minimal -->'." % taxonomy["version"],
        )
    else:
        result.version = int(m.group(1))
        result.disclosure = m.group(2)
        if result.version != taxonomy["version"]:
            result.error(
                1,
                "format version v%d is not supported by this validator (expects v%d)."
                % (result.version, taxonomy["version"]),
            )
        if result.disclosure not in taxonomy["disclosure_levels"]:
            result.error(
                1,
                "disclosure must be one of: %s." % ", ".join(taxonomy["disclosure_levels"]),
            )
    disclosure = result.disclosure if result.disclosure in taxonomy["disclosure_levels"] else None

    # --- length -----------------------------------------------------------
    if not text.strip():
        result.error(None, "the card is empty.")
        return result
    if result.chars > taxonomy["max_chars"]:
        result.error(
            None,
            "card is %d characters; the portal refuses anything over %d."
            % (result.chars, taxonomy["max_chars"]),
        )
    elif result.chars > taxonomy["target_chars"]:
        result.warn(
            None,
            "card is %d characters; aim for %d or fewer so it reads in one sitting."
            % (result.chars, taxonomy["target_chars"]),
        )

    # --- headings ---------------------------------------------------------
    headings = []  # (line_no, level, title)
    for i, line in enumerate(lines):
        if fenced[i]:
            continue
        hm = ATX_RE.match(line)
        if hm:
            headings.append((i + 1, len(hm.group(1)), hm.group(2).strip()))
            continue
        if (
            i > 0
            and SETEXT_RE.match(line)
            and lines[i - 1].strip()
            and not fenced[i - 1]
            and not lines[i - 1].lstrip().startswith("|")
            and not ATX_RE.match(lines[i - 1])
        ):
            result.error(
                i + 1,
                "this line turns the text above it into a heading; leave a blank "
                "line before a horizontal rule and use '#' marks for headings.",
            )
    for line_no, level, title in headings:
        if level == 1:
            result.error(
                line_no,
                "no '# ' title: the portal already prints the submission name as "
                "the page title.",
            )
        elif level > 4:
            result.error(line_no, "heading level %d is unstyled in the portal; use #### at most." % level)

    # --- table ------------------------------------------------------------
    table_at = next(
        (i for i, line in enumerate(lines) if not fenced[i] and line.lstrip().startswith("|")),
        None,
    )
    table_end = table_at
    if table_at is None:
        result.error(None, "the classification table is missing.")
    else:
        header = _split_row(lines[table_at])
        if header != taxonomy["table_header"]:
            result.error(
                table_at + 1,
                "table header must be '| %s |'." % " | ".join(taxonomy["table_header"]),
            )
        if table_at > 0 and lines[table_at - 1].strip():
            result.error(table_at + 1, "leave a blank line before the table.")
        if table_at + 1 >= len(lines) or not TABLE_SEP_RE.match(lines[table_at + 1]):
            result.error(table_at + 2, "the table needs a '| --- | --- |' row under its header.")
        rows = []
        j = table_at + 2
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            rows.append((j + 1, _split_row(lines[j])))
            j += 1
        table_end = j
        fields = taxonomy["fields"]
        labels = [f["label"] for f in fields]
        got = [cells[0] if cells else "" for _, cells in rows]
        if got != labels:
            result.error(
                table_at + 1,
                "the table must have exactly these rows, in this order: %s."
                % "; ".join(labels),
            )
        for line_no, cells in rows:
            if len(cells) != 2:
                result.error(line_no, "each table row has exactly two cells.")
                continue
            field = next((f for f in fields if f["label"] == cells[0]), None)
            if field is None:
                hint = _suggest(cells[0], labels)
                result.error(
                    line_no,
                    "'%s' is not a category.%s"
                    % (cells[0], " Did you mean '%s'?" % hint if hint else ""),
                )
                continue
            result.fields[field["key"]] = _check_field(result, line_no, field, cells[1], taxonomy)

        # Lede: prose between the marker and the table, with no heading.
        lede = [
            lines[i].strip()
            for i in range(1, table_at)
            if lines[i].strip() and not fenced[i] and not ATX_RE.match(lines[i])
        ]
        if not lede:
            result.error(
                table_at + 1,
                "add a one-or-two sentence lede between the marker and the table; "
                "it is what the leaderboard hover preview shows.",
            )
        elif any(l.startswith("LEDE:") for l in lede):
            result.error(2, "template placeholder 'LEDE:' was not replaced.")
        elif sum(len(l) for l in lede) > 300:
            result.warn(
                2,
                "the lede is over 300 characters; the hover preview has room for "
                "about 200 before it pushes the table out of view.",
            )
        for line_no, _level, _title in headings:
            if line_no - 1 < table_at:
                result.error(line_no, "no heading above the table; open with the lede.")

    # --- sections ---------------------------------------------------------
    level = taxonomy["section_heading_level"]
    marks = "#" * level
    spec = taxonomy["sections"]
    titles = [s["title"] for s in spec]
    allowed = [
        s["title"]
        for s in spec
        if s["required"] or disclosure is None or s.get("disclosure") == disclosure
    ]
    found = []
    for line_no, lvl, title in headings:
        if line_no - 1 < (table_end or 0):
            continue
        if 1 < lvl < level:
            result.error(line_no, "sections use '%s'; do not use a higher-level heading." % marks)
        if lvl != level:
            continue
        if title not in titles:
            hint = _suggest(title, titles)
            result.error(
                line_no,
                "'%s %s' is not one of the standard sections (%s).%s Use '%s#' for "
                "sub-headings inside a section."
                % (marks, title, "; ".join(titles), " Did you mean '%s'?" % hint if hint else "", marks),
            )
            continue
        if title not in allowed:
            result.error(
                line_no,
                "'%s' is only allowed in a card marked disclosure=%s."
                % (title, next(s["disclosure"] for s in spec if s["title"] == title)),
            )
        found.append((line_no, title))
    found_titles = [t for _, t in found]
    for s in spec:
        if s["required"] and s["title"] not in found_titles:
            result.error(None, "missing section '%s %s'." % (marks, s["title"]))
    if len(set(found_titles)) != len(found_titles):
        result.error(None, "a section appears more than once.")
    elif found_titles != [t for t in titles if t in found_titles]:
        result.error(
            found[0][0] if found else None,
            "sections must appear in this order: %s." % "; ".join(titles),
        )
    section_lines = [ln for ln, lvl, _ in headings if lvl <= level]
    for line_no, title in found:
        nxt = min([ln for ln in section_lines if ln > line_no] or [len(lines) + 1])
        if not any(lines[k].strip() for k in range(line_no, nxt - 1)):
            result.error(line_no, "section '%s' is empty." % title)

    # --- things the portal deletes or mangles ------------------------------
    for i, line in enumerate(prose):
        if i == 0 or not line:
            continue
        if HTML_RE.search(line):
            result.error(i + 1, "raw HTML is deleted by the portal; use Markdown only.")
        if IMAGE_RE.search(line):
            result.error(i + 1, "images are not shown by the portal; remove the image.")
        for lm in LINK_RE.finditer(line):
            target = lm.group(1)
            if not target.startswith(("https://", "mailto:")):
                result.error(i + 1, "link target '%s' must be an absolute https:// URL." % target)
        if MATH_RE.search(line):
            result.warn(i + 1, "'$...$' is not rendered as math; write formulas as inline code.")

    # --- likely IP leaks in a minimal card --------------------------------
    if disclosure == "minimal":
        fence_starts = [i for i in range(len(lines)) if fenced[i] and (i == 0 or not fenced[i - 1])]
        for i in fence_starts:
            result.warn(
                i + 1,
                "code block in a minimal card: prompts, code, and configs are the "
                "detail this level leaves out.",
            )
        for i, line in enumerate(lines):
            if i == 0 or fenced[i] or (table_at is not None and table_at <= i < table_end):
                continue
            for mm in MODEL_ID_RE.finditer(line):
                token = mm.group(0)
                if re.search(r"\d", token) and "-" in token:
                    result.warn(
                        i + 1,
                        "'%s' looks like an exact model ID; a minimal card names "
                        "model families only." % token,
                    )
            hp = HYPERPARAM_RE.search(line)
            if hp:
                result.warn(
                    i + 1,
                    "'%s': hyperparameters are left out of a minimal card." % hp.group(1),
                )
            if URL_RE.search(line):
                result.warn(
                    i + 1,
                    "URL in a minimal card: check it does not name a vendor, "
                    "endpoint, or data source you meant to keep private.",
                )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("card", help="path to the model card Markdown file")
    parser.add_argument("--json", action="store_true", help="print parsed fields and issues as JSON")
    parser.add_argument("--taxonomy", default=str(TAXONOMY_PATH), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    try:
        text = Path(args.card).read_text(encoding="utf-8")
    except OSError as exc:
        print("ERROR cannot read %s: %s" % (args.card, exc), file=sys.stderr)
        return 2
    result = validate(text, load_taxonomy(args.taxonomy))

    if args.json:
        print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
        return 0 if result.ok else 1

    for issue in sorted(result.issues, key=_issue_key):
        print(issue)
    summary = "%d characters, %d error(s), %d warning(s)" % (
        result.chars,
        len(result.errors),
        len(result.warnings),
    )
    print(("OK: " if result.ok else "FAILED: ") + summary)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
