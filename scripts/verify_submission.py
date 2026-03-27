from pathlib import Path
import subprocess
import argparse
import sys


STANDARD_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
MIN_LENGTH = 10
MAX_LENGTH = 60


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

    cmd = [git, "clone", repo_url.removeprefix("git+"), str(repo_dir)]
    if branch:
        cmd += ["-b", branch, "--single-branch"]
    if shallow:
        cmd += ["--depth", "1"]

    try:
        subprocess.run(cmd, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git clone failed:\n{e.stderr}") from e


def _sync_uv(repo_dir: Path, extras: list[str], uv: str = "uv") -> None:
    extra_flags = [flag for extra in extras for flag in ("--extra", extra)]
    try:
        subprocess.run(
            [uv, "sync", "--project", str(repo_dir), *extra_flags],
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"uv sync failed:\n{e.stderr}") from e


def _uv_run(
    repo_dir: Path,
    script_name: str,
    output_fasta: Path,
    n_sequences: int,
    uv: str = "uv",
) -> None:
    cmd = [
        uv,
        "run",
        "--no-sync",
        "--project",
        str(repo_dir),
        script_name,
        "--n_sequences",
        str(n_sequences),
        "--output",
        str(output_fasta),
    ]
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=repo_dir)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Plugin subprocess failed with exit code {e.returncode}."
        ) from e


def _parse_fasta(fasta_path: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    header: str | None = None
    seq_parts: list[str] = []

    for line in fasta_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append((header, "".join(seq_parts)))
            header = line[1:]
            seq_parts = []
        else:
            seq_parts.append(line.upper())

    if header is not None:
        records.append((header, "".join(seq_parts)))

    return records


def _verify_sequences(fasta_path: Path, n_sequences: int) -> None:
    if not fasta_path.exists():
        raise FileNotFoundError(f"Output FASTA not found: {fasta_path}")

    records = _parse_fasta(fasta_path)
    errors: list[str] = []

    if not records:
        errors.append("FASTA file is empty — no sequences found.")
    elif len(records) != n_sequences:
        errors.append(f"Expected {n_sequences} sequences, got {len(records)}.")

    seen: set[str] = set()
    for i, (header, seq) in enumerate(records, start=1):
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


def verify_setup(
    dir: Path,
    url: str,
    branch: str | None = None,
    script_name: str = "generate",
    n_sequences: int = 100,
    extras: list[str] | None = None,
):
    extras = extras or []

    print(f"[1/5] Cloning {url} → {dir}")
    _clone_git_repository(dir, url, branch=branch)

    print("[2/5] Installing dependencies")
    _sync_uv(dir, extras)

    run1 = (dir / "generated_run1.fasta").resolve()
    run2 = (dir / "generated_run2.fasta").resolve()

    print(f"[3/5] Generating {n_sequences} sequences")
    _uv_run(dir, script_name, run1, n_sequences)

    print("[4/5] Verifying sequences")
    _verify_sequences(run1, n_sequences)

    print("[5/5] Checking reproducibility")
    _uv_run(dir, script_name, run2, n_sequences)
    if run1.read_text() != run2.read_text():
        raise ValueError(
            "Reproducibility check failed: two runs with identical inputs produced different sequences."
        )

    print("\nAll checks passed. Submission is valid!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Verify an AMP Challenge 2027 submission.\n\n"
            "Clones the repository, installs dependencies, generates sequences,\n"
            "and checks them for validity (alphabet, length, duplicates)."
        ),
        epilog=(
            "Example:\n"
            "  python verify_submission.py https://github.com/szczurek-lab/amp-challenge-2027"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="GitHub repository URL.")
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
        "--script-name", default="generate", help="uv script entry point to run."
    )
    parser.add_argument(
        "--n-sequences",
        type=int,
        default=50_000,
        help="Number of sequences to generate.",
    )
    parser.add_argument(
        "--extra",
        dest="extras",
        action="append",
        default=[],
        metavar="EXTRA",
        help="Optional uv extras to install (repeatable).",
    )
    args = parser.parse_args()

    try:
        verify_setup(
            args.dir,
            args.url,
            branch=args.branch,
            script_name=args.script_name,
            n_sequences=args.n_sequences,
            extras=args.extras,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
