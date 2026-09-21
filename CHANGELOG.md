# Changelog

Card format versions (`em-model-card vN`) change only when a card written under the old rules would no longer validate. Skill releases are tagged `vX.Y.Z`.

## v1.0.0 (unreleased)

- First release. Card format `em-model-card v1`: marker line, lede, six-row classification table, five required sections, optional Representative prompt in showcase cards.
- Two disclosure levels: `minimal` (default) and `showcase`.
- Bundled validator (`scripts/validate_card.py`), Python 3.8+, standard library only.
