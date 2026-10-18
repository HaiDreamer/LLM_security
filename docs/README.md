# LLM srcurity

Seed-case dataset and validation tooling.

## Status
Week 1: repository skeleton, seed-case validation, data dictionary v0.1.

## Repository structure
```
<paste the output of `tree -L 2` after you create the folders>
```

## Data
| Item | Path | Description |
|---|---|---|
| Raw seed cases | `<dataset/raw/data_dictionary_v0.1.jsonl>` | Provided Week-1 package (P1), not modified |
| Labels | `<"not completed">` | Annotator labels |
| Model outputs | `<"not completed">` | Observed model responses |

Raw data, labels, and model outputs are stored separately and never edited in place.

## Data dictionary
See `<docs/data_dictionary_v0.1.md>`.

## Setup
```bash
<python -m venv .venv && source .venv/bin/activate>
<pip install -r requirements.txt>
```

## Run validation
```bash
<python project/main/validate_seed_dataset.py <path-to-jsonl>>
```
Checks: unique `<id field>`, required fields present, valid language and modality values. (NOT finalized)

## Expected result
| Check | Count |
|---|---|
| Records | <N> |
| Unique IDs | <N> |
| Records with missing fields | <0> |
| Invalid language/modality values | <0> |

Running the validation twice from a clean environment gives the same counts.

## Notes
<In the begining of the project.>