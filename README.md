# AMP Challenge 2027

> International competition for generative AI in antimicrobial peptide design.

Antimicrobial resistance is one of the most pressing global health challenges. This competition invites participants to develop generative models that design novel antimicrobial peptides (AMPs) with activity against a panel of clinically relevant bacterial strains, including multi-drug resistant ESKAPE pathogens.

## Categories

Participants can submit to one or more categories. Each category corresponds to a script entry point:

| Category | Entry point | Ranking metric |
|----------|-------------|----------------|
| Broad Spectrum Activity | `generate_broad_spectrum` | Team avg. of ([Overall Success Rate](#success-rate)); ties broken by [MIC90](#mic90) across all 20 strains |
| Gram-Positive Activity | `generate_gram_pos` | Team avg. of ([Gram-positive Success Rate](#success-rate)); ties broken by [MIC50](#mic50) across Gram-positive strains |
| Gram-Negative Activity | `generate_gram_neg` | Team avg. of ([Gram-negative Success Rate](#success-rate)); ties broken by [MIC50](#mic50) across Gram-negative strains |
| Multi-Drug Resistant (MDR) Activity | `generate_mdr` | Team avg. of ([MDR Success Rate](#success-rate)); ties broken by [MIC50](#mic50) across MDR ESKAPE strains |
| Optimal Selectivity | `generate_therapeutic` | Team avg. of [SW](#safety-window-sw); peptides must meet Potency Threshold (MIC ≤ 16 uM) in ≥ 1 strain (completely inactive sequences excluded); ties on non-hemolytic inequalities broken by lowest [MIC50](#mic50) across all tested strains |

## Submission Requirements

### Minimum (benchmark participation)
- Abstract summarizing the method
- Library of 50,000 designed AMPs
- Ranked top-100 candidates with selection/ranking documentation
- Short summary of training data, external databases, and any filters applied

### Full (co-authorship eligibility)
All of the above, plus:
- Public GitHub repository with model weights, inference code, and usage docs
- Permissive OSI-approved license (MIT, BSD-3-Clause, or Apache 2.0)
- Uses **[`uv`](https://docs.astral.sh/uv/concepts/projects/init/#projects)** for dependency management (include `uv.lock` and a defined Python version)
- Category entry points runnable via `uv run <entry-point>` generating the 50,000-member library and top-100 list; any additional arguments must have defaults
- Fixed default random seed (identical output on repeated runs)
- Full training data disclosure; any non-public data must be released under a permissive license

## Sequence Requirements

Generated sequences must:

- Use only the 20 standard proteinogenic amino acids (`ACDEFGHIKLMNPQRSTVWY`)
- Be between 8 and 50 residues long
- Be unique (no duplicates)
- Be linear with free termini (no terminal modifications, including amidation)
- Exclude noncanonical amino acids, stapled peptides, peptidomimetics, and chemically modified variants (lipidated, glycosylated, PEGylated, dendrimeric, etc.)

The full 50,000-sequence library must additionally contain no sequences identical to known antibacterial peptides in `data/antibacterial.fasta`. The top-100 list is held to a stricter standard: no sequence may exceed 80% sequence identity (Levenshtein ratio) with any sequence in that reference set.

## Getting Started

This repository also serves as a working example — see [src/amp_challenge_2027/generate.py](src/amp_challenge_2027/generate.py) for a complete implementation that meets all requirements.

The steps below walk through building a minimal submission. Replace `my-model` with your model name throughout.

### 1. Initialize the project

```bash
uv init --package my-model
cd my-model
```

### 2. Add category entry points

In `pyproject.toml`, add a `[project.scripts]` section with one entry per category you are submitting to:

```toml
[project.scripts]
generate_broad_spectrum = "my_model.generate:main"
generate_gram_pos = "my_model.generate:main"
# add only the categories you are submitting to
```

Note: to add package dependencies, use `uv add <package>` instead of editing `pyproject.toml` directly.

### 3. Implement `generate.py`

Running any entry point produces two files in a subdirectory named after the category:

```
generate_broad_spectrum/
  library.fasta  ← full 50,000-sequence library
  top.fasta      ← top-100 ranked sequences
```


See [src/amp_challenge_2027/generate.py](src/amp_challenge_2027/generate.py) for a complete example.

### 4. Run locally

Install dependencies and test your script:

```bash
uv run generate_broad_spectrum
```

Optional arguments (must have defaults):

| Flag | Default | Description |
|------|---------|-------------|
| `--n-sequences` | `50000` | Number of sequences to generate |
| `--top-k` | `100` | Number of top-ranked sequences to write |
| `--seed` | `42` | Random seed for reproducibility |
| `--length` | `50` | Length of each generated sequence |

### 5. Verify

Push your project (including `uv.lock`) to a **public** GitHub repository, then run the validator:

```bash
uv run python scripts/verify_submission.py <github-url> generate_broad_spectrum
```


### 6. Submit

To submit, fill out the Google Form: TBA

## Validation

Verify your submission with:

```bash
uv run python scripts/verify_submission.py <github-url> <category>
```

This clones your repo, installs dependencies, generates the full library and ranked top-100 into `<category>/library.fasta` and `<category>/top.fasta`, verifies both files, then generates them again to confirm the output is reproducible.

| Argument | Default | Description |
|----------|---------|-------------|
| `url` | — | GitHub repository URL (required positional) |
| `category` | — | Category entry point to verify (required positional) |
| `--branch` | repo default | Git branch to clone |
| `--dir` | `submission/` | Directory to clone into |
| `--extra` | — | Optional [uv](https://docs.astral.sh/uv/concepts/projects/init/#projects) extras to install (repeatable) |
| `--antibacterial-fasta` | `data/antibacterial.fasta` | FASTA file of known antibacterial sequences to check for overlap |

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

## Definitions and Parameters

#### Measurements

Minimum Inhibitory Concentration (MIC) and half-maximal hemolytic concentration (HC50) are recorded in micromolar (uM). The highest tested MIC concentration is 64 uM. For strains where no growth inhibition is observed at this limit, MIC is recorded as >64 uM.

#### Success Rate

The percentage of tested strains within a specified panel (Overall, Gram-positive, Gram-negative, or MDR) where the candidate peptide meets the Potency Threshold.

#### MIC50

The median MIC value across all strains in the relevant panel (50th percentile).

#### MIC90

The MIC value at the 90th percentile across all strains in the relevant panel.

#### Safety Window (SW)

Calculated as SW = HC50 / MIC50 across all 20 strains. For non-hemolytic peptides reaching the 128 uM assay limit, HC50 is recorded as >128 uM, yielding an inequality for the SW.
