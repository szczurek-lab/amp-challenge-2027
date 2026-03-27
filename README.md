# AMP Challenge 2027

International competition for generative AI in antimicrobial peptide design.

## Submission Requirements

Your submission must be a public GitHub repository that:

- Uses **`uv`** for dependency management (include `uv.lock` and a defined Python version)
- Exposes a `generate` script entry point runnable as:

```bash
uv run generate --n_sequences <N> --output <model-name>.fasta [additional optional args]
```

Any additional optional arguments must have default values so the command runs without them.

## Sequence Requirements

Generated sequences must:

- Use only standard amino acid characters (`ACDEFGHIKLMNPQRSTVWY`)
- Be between 5 and 60 residues long
- Be unique (no duplicates)

## Validation

Verify your submission with:

```bash
python scripts/verify_submission.py <github-url>
```

This clones your repo, installs dependencies, generates 50,000 sequences, and checks them for validity.

Additional options:

| Flag | Default | Description |
|------|---------|-------------|
| `--branch` | repo default | Git branch to clone |
| `--dir` | `submission/` | Directory to clone into |
| `--n-sequences` | `50000` | Number of sequences to generate |
| `--extra` | — | Optional uv extras to install (repeatable) |

## Quick Start

### Using the example model

Install dependencies and run:

```bash
uv run generate --n_sequences 100 --output my-model.fasta
```

Optional arguments:

| Flag | Default | Description |
|------|---------|-------------|
| `--length` | `10` | Length of each generated sequence |

### Setting up your own model

Initialize a new project with `uv`:

```bash
uv init --package amp-challenge-2027
```

Configure the entry point in `pyproject.toml`:

```toml
[project.scripts]
generate = "amp_challenge_2027.generate:main"
```

## Project Structure

```
amp-challenge-2027/
├── checkpoint/
│   └── weights.csv          # Trained model weights
├── scripts/
│   └── verify_submission.py # Submission validator
├── src/
│   └── amp_challenge_2027/
│       └── generate.py      # Entry point: sequence generation logic
├── pyproject.toml
└── uv.lock
```
