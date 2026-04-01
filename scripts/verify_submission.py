from pathlib import Path
import subprocess
import argparse
import os
import sys
import shutil

import Levenshtein

STANDARD_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
MIN_LENGTH = 8
MAX_LENGTH = 50

CATEGORIES = [
    "generate_broad_spectrum",
    "generate_gram_pos",
    "generate_gram_neg",
    "generate_mdr",
    "generate_therapeutic",
]

TOP_SIZE = 100
LIBRARY_SIZE = 50_000


def _read_fasta(path: Path) -> tuple[list[str], list[str]]:
    headers, sequences = [], []
    header, seq_parts = None, []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                headers.append(header)
                sequences.append("".join(seq_parts))
            header, seq_parts = line[1:], []
        else:
            seq_parts.append(line.upper())
    if header is not None:
        headers.append(header)
        sequences.append("".join(seq_parts))
    return headers, sequences


def _check_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"'{name}' is not installed or not found on PATH.")


def _clone_git_repository(
    repo_dir: Path,
    repo_url: str,
    branch: str | None = None,
    shallow: bool = True,
    git: str = "git",
):
    if repo_dir.exists():
        raise FileExistsError(f"'{repo_dir}' already exists.")

    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    cmd = [git, "clone"]
    if branch:
        cmd += ["-b", branch, "--single-branch"]
    if shallow:
        cmd += ["--depth", "1"]
    cmd += [repo_url.removeprefix("git+"), str(repo_dir)]

    try:
        subprocess.run(cmd, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git clone failed:\n{e.stderr}") from e


def _sync_uv(repo_dir: Path, extras: list[str], uv: str = "uv") -> None:
    extra_flags = [flag for extra in extras for flag in ("--extra", extra)]
    try:
        subprocess.run(
            [uv, "sync", *extra_flags],
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            cwd=repo_dir,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"uv sync failed:\n{e.stderr}") from e


def _uv_run(
    repo_dir: Path,
    category: str,
    uv: str = "uv",
) -> None:
    cmd = [uv, "run", "--no-sync", category]
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=repo_dir, env=env)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Plugin subprocess failed with exit code {e.returncode}."
        ) from e


def _verify_sequences(fasta_path: Path) -> set[str]:
    headers, sequences = _read_fasta(fasta_path)
    errors: list[str] = []

    if not sequences:
        errors.append("FASTA file is empty — no sequences found.")
    elif len(sequences) != LIBRARY_SIZE:
        errors.append(f"Expected {LIBRARY_SIZE} sequences, got {len(sequences)}.")

    seen: set[str] = set()
    for i, (header, seq) in enumerate(zip(headers, sequences), start=1):
        if not header.strip():
            errors.append(f"Record {i}: missing header.")
        if not seq:
            errors.append(f"Record {i} ('{header}'): empty sequence.")
            continue
        invalid = set(seq) - STANDARD_AMINO_ACIDS
        if invalid:
            errors.append(
                f"Record {i} ('{header}'): invalid characters {sorted(invalid)}."
            )
        if len(seq) < MIN_LENGTH:
            errors.append(
                f"Record {i} ('{header}'): sequence too short ({len(seq)} < {MIN_LENGTH})."
            )
        if len(seq) > MAX_LENGTH:
            errors.append(
                f"Record {i} ('{header}'): sequence too long ({len(seq)} > {MAX_LENGTH})."
            )
        if seq in seen:
            errors.append(f"Record {i} ('{header}'): duplicate sequence.")
        seen.add(seq)

    if errors:
        raise ValueError(
            "Sequence verification failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return seen

def _veritfy_max_simularity(sequences: set[str], references: set[str], threshold: float = 0.8) -> None:
    for seq in sequences:
        for ref in references:
            if Levenshtein.ratio(seq, ref) > threshold:
                raise ValueError(
                    f"Similarity check failed: sequence '{seq}' has similarity "
                    f"> {threshold} with reference '{ref}'."
                )


def _verify_no_overlap(full_sequences: set[str], antibacterial_sequences: set[str]) -> None:
    overlap = full_sequences & antibacterial_sequences
    if overlap:
        raise ValueError(
            f"Overlap check failed: {len(overlap)} sequence(s) found in antibacterial reference."
        )


def _verify_top(top_fasta: Path, full_sequences: set[str], top_k: int) -> None:
    _, top_sequences = _read_fasta(top_fasta)
    errors: list[str] = []

    if len(top_sequences) != top_k:
        errors.append(f"Expected {top_k} sequences, got {len(top_sequences)}.")

    seen: set[str] = set()
    for i, seq in enumerate(top_sequences, start=1):
        if seq not in full_sequences:
            errors.append(f"Record {i}: sequence not found in full library.")
        if seq in seen:
            errors.append(f"Record {i}: duplicate sequence in top list.")
        seen.add(seq)

    if errors:
        raise ValueError(
            "Rank verification failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )


def verify_setup(
    dir: Path,
    url: str,
    category: str,
    branch: str | None = None,
    extras: list[str] | None = None,
    antibacterial_fasta: Path | None = None,
):
    extras = extras or []

    _check_tool("git")
    print(f"[1] Cloning {url} → {dir}")
    _clone_git_repository(dir, url, branch=branch)

    _check_tool("uv")
    print("[2] Installing dependencies")
    _sync_uv(dir, extras)

    library_fasta = dir / category / "library.fasta"
    top_fasta = dir / category / "top.fasta"

    print("[3] Generating library")
    _uv_run(dir, category)

    print("[4] Verifying full library")
    full_sequences = _verify_sequences(library_fasta)

    print("[5] Verifying top list")
    _verify_top(top_fasta, full_sequences, TOP_SIZE)

    if antibacterial_fasta is not None:
        _, antibacterial_sequences = _read_fasta(antibacterial_fasta)
        antibacterial_set = set(antibacterial_sequences)

        print(f"[6] Checking library overlap with {antibacterial_fasta}")
        _verify_no_overlap(full_sequences, antibacterial_set)

        print(f"[7] Checking top similarity with {antibacterial_fasta}")
        _, top_sequences = _read_fasta(top_fasta)
        _veritfy_max_simularity(set(top_sequences), antibacterial_set)

    print("[8] Checking reproducibility" if antibacterial_fasta is not None else "[6] Checking reproducibility")
    library_data = library_fasta.read_bytes()
    top_data = top_fasta.read_bytes()
    _uv_run(dir, category)

    if library_fasta.read_bytes() != library_data:
        raise ValueError(
            "Reproducibility check failed: two runs with identical inputs produced different output."
        )
    if top_fasta.read_bytes() != top_data:
        raise ValueError(
            "Reproducibility check failed: top list differs between runs."
        )

    print(f"\nAll checks passed. Submission is valid for category '{category}'!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Verify an AMP Challenge 2027 submission.\n\n"
            "Clones the repository, installs dependencies, generates sequences,\n"
            "and checks them for validity (alphabet, length, duplicates)."
        ),
        epilog=(
            "Example:\n"
            "  python scripts/verify_submission.py https://github.com/szczurek-lab/amp-challenge-2027 generate_broad_spectrum"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="GitHub repository URL.")
    parser.add_argument(
        "category",
        choices=CATEGORIES,
        help="Category entry point to verify.",
    )
    parser.add_argument(
        "--branch", default=None, help="Git branch to clone (default: repo default)."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("submission"),
        help="Directory to clone the repository into (default: submission).",
    )
    parser.add_argument(
        "--extra",
        dest="extras",
        action="append",
        default=[],
        metavar="EXTRA",
        help="Optional uv extras to install (repeatable).",
    )
    parser.add_argument(
        "--antibacterial-fasta",
        type=Path,
        default=Path("data/antibacterial.fasta"),
        help="FASTA file of known antibacterial sequences to check for overlap (default: data/antibacterial.fasta).",
    )
    args = parser.parse_args()

    try:
        verify_setup(
            args.dir,
            args.url,
            args.category,
            branch=args.branch,
            extras=args.extras,
            antibacterial_fasta=args.antibacterial_fasta,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
