# AMP Challenge 2027

International competition for generative AI in antimicrobial peptide design.

## Repository Requirements

Your submission must be hosted on a public GitHub repository that:

- Uses **[`uv`](https://docs.astral.sh/uv/concepts/projects/init/#projects)** for dependency management (include `uv.lock` and a defined Python version)
- Produces **reproducible** output: running the script twice with the same inputs must produce identical sequences (e.g., by defining a fixed default seed)
- Exposes a `generate` script entry point runnable as:

```bash
uv run generate --n_sequences <N> --output <model-name>.fasta [additional optional args]
```

Any additional optional arguments must have default values so the command runs without them.

## Sequence Requirements

Generated sequences must:

- Use only standard amino acid characters (`ACDEFGHIKLMNPQRSTVWY`)
- Be between 10 and 60 residues long
- Be unique (no duplicates)
- Be linear
- Not contain any end terminus modifications.

## Getting Start

This repository also serves as a working example — see [src/amp_challenge_2027/generate.py](src/amp_challenge_2027/generate.py) for a complete implementation that meets all requirements.

The steps below walk through building a minimal submission. Replace `my-model` with your model name throughout.

### 1. Initialize the project

```bash
uv init --package my-model
cd my-model
```

### 2. Add the `generate` entry point

In `pyproject.toml`, add a `[project.scripts]` section:

```toml
[project.scripts]
generate = "my_model.generate:main"
```

Note: to add package dependencies, use `uv add <package>` instead of editing `pyproject.toml` directly.

### 3. Implement `generate.py`

Your entry point must accept `--n_sequences` and `--output` and write a FASTA file. Use a fixed default seed so output is reproducible:

```python
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_sequences", type=int, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--seed", type=int, default=42)
    # add any other optional args with defaults here
    args = parser.parse_args()

    # generate sequences and write to args.output as FASTA
    ...
```

### 4. Run locally

Install dependencies and test your script:

```bash
uv run generate --n_sequences 100 --output my-model.fasta
```

Required arguments:

| Flag | Description |
|------|-------------|
| `--n_sequences` | Number of sequences to generate |
| `--output` | Output FASTA file path |

Optional arguments (must have defaults):

| Flag | Default | Description |
|------|---------|-------------|
| `--seed` | `42` | Random seed for reproducibility |
| `--length` | `50` | Length of each generated sequence |

### 5. Verify and submit

Push your project (including `uv.lock`) to a **public** GitHub repository, then run the validator:

```bash
python scripts/verify_submission.py <github-url>
```

## Validation

Verify your submission with:

```bash
python scripts/verify_submission.py <github-url>
```

This clones your repo, installs dependencies, generates 50,000 sequences, verifies they meet the competition requirements, then generates them again to confirm the output is reproducible.

Additional options:

| Flag | Default | Description |
|------|---------|-------------|
| `--branch` | repo default | Git branch to clone |
| `--dir` | `submission/` | Directory to clone into |
| `--n-sequences` | `50000` | Number of sequences to generate |
| `--extra` | — | Optional uv extras to install (repeatable) |

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
