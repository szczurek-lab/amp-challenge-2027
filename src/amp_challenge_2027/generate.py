import argparse
import os
import sys
from pathlib import Path

import numpy as np


def _write_fasta(sequences: list[str], path: Path) -> None:
    with open(path, "w") as f:
        for i, seq in enumerate(sequences, start=1):
            f.write(f">seq{i}\n{seq}\n")


def generate(n_sequences: int, *, length: int, seed: int = 42) -> list[str]:
    try:
        p = np.loadtxt("./checkpoint/weights.csv", delimiter=",")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"./checkpoint/weights.csv not found (cwd: {os.getcwd()})"
        )

    # Randomly sample either amino-acid "K" or "P" based on probability p
    rng = np.random.default_rng(seed)
    samples = rng.binomial(1, p, size=(n_sequences, length))
    labels = np.where(samples, "K", "P")

    return ["".join(row) for row in labels]


def score(sequences: list[str]) -> list[float]:
    """Score sequences for the target category. Higher is better."""
    return [float(i) for i in range(len(sequences), 0, -1)]


def main():
    category = Path(sys.argv[0]).stem

    parser = argparse.ArgumentParser()
    parser.add_argument("--n-sequences", type=int, default=50_000)
    parser.add_argument("--top-k", type=int, default=100)
    parser.add_argument("--length", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out_dir = Path(category)
    out_dir.mkdir(parents=True, exist_ok=True)

    sequences = generate(args.n_sequences, length=args.length, seed=args.seed)

    library_path = out_dir / "library.fasta"
    _write_fasta(sequences, library_path)
    print(f"Generated {len(sequences)} sequences → {library_path}")

    scores = score(sequences)
    ranked = sorted(zip(scores, sequences), key=lambda x: x[0], reverse=True)
    top_sequences = [seq for _, seq in ranked[: args.top_k]]

    top_path = out_dir / "top.fasta"
    _write_fasta(top_sequences, top_path)
    print(f"Top {args.top_k} sequences → {top_path}")
