# AMP Challenge 2027

International competition for generative AI in antimicrobial peptide design.

Antimicrobial resistance is one of the most pressing global health challenges. This competition invites participants to develop generative models that design novel antimicrobial peptides (AMPs) with activity against a panel of clinically relevant bacterial strains, including multi-drug resistant ESKAPE pathogens. Submissions are evaluated on predicted minimum inhibitory concentration (MIC) across five categories spanning broad-spectrum activity, Gram-positive and Gram-negative specificity, MDR activity, and therapeutic selectivity.

## Definitions and Parameters

**References:** Polymyxin B for the Gram-negative panel; Daptomycin for the Gram-positive panel.

**Measurements:** Minimum Inhibitory Concentration (MIC) and half-maximal hemolytic concentration (HC50) are recorded in micromolar (uM).

**Potency Threshold:** A peptide is classified as active against a specific strain if its Relative Potency satisfies RP ≥ 0.25, where RP = MIC_reference / MIC_candidate.

**Success Rate:** The percentage of tested strains within a specified panel (Overall, Gram-positive, Gram-negative, or MDR) where the candidate peptide successfully meets the Potency Threshold.

**MIC50:** The median MIC value across all strains in the relevant panel, representing the concentration at which half of tested strains are inhibited.

**Therapeutic Index (TI):** Calculated as the ratio of toxicity to the aggregate potency across the entire 20-strain panel: TI = HC50 / MIC50 (Geometric Mean MIC across all 20 strains). For non-hemolytic peptides reaching the 128 uM assay limit, HC50 is recorded as >128 uM, yielding an inequality for the TI.

## Categories

Participants can submit to one or more categories. Each category corresponds to a script entry point:

| Category | Entry point | Ranking metric |
|----------|-------------|----------------|
| Broad Spectrum Activity | `generate_broad_spectrum` | Team avg. of (Overall Success Rate) × (Geometric Mean RP) |
| Gram-Positive Activity | `generate_gram_pos` | Team avg. of (Gram-positive Success Rate) × (Geometric Mean RP across Gram-positive strains) |
| Gram-Negative Activity | `generate_gram_neg` | Team avg. of (Gram-negative Success Rate) × (Geometric Mean RP across Gram-negative strains) |
| Multi-Drug Resistant (MDR) Activity | `generate_mdr` | Team avg. of (MDR Success Rate) × (Geometric Mean RP across MDR ESKAPE strains) |
| Optimal Selectivity | `generate_therapeutic` | Team avg. of (Overall Success Rate) × (TI); peptides must meet RP ≥ 0.25 in ≥ 1 strain (completely inactive sequences excluded); ties broken by lowest geometric mean MIC across all tested strains |

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

The only function you need to implement is `score()`. The category name comes from `sys.argv[0]`, so a single `main()` works for all entry points:

```python
def score(sequences):
    """Score sequences for the target category. Higher is better."""
    ...
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
python scripts/verify_submission.py <github-url> generate_broad_spectrum
```


### 6. Submit

To submit, fill out the Google Form: [[template]]([template])

## Validation

Verify your submission with:

```bash
python scripts/verify_submission.py <github-url> <category>
```

This clones your repo, installs dependencies, generates the full library and ranked top-100 into `<category>/library.fasta` and `<category>/top.fasta`, verifies both files, then generates them again to confirm the output is reproducible.

| Argument | Default | Description |
|----------|---------|-------------|
| `url` | — | GitHub repository URL (required positional) |
| `category` | — | Category entry point to verify (required positional) |
| `--branch` | repo default | Git branch to clone |
| `--dir` | `submission/` | Directory to clone into |
| `--extra` | — | Optional [uv](https://docs.astral.sh/uv/concepts/projects/init/#projects) extras to install (repeatable) |

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
