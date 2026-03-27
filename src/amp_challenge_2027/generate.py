import argparse

import numpy as np
import seqme as sm


def generate(n_sequences: int, *, length: int, seed: int = 42) -> list[str]:
    p = np.loadtxt("./checkpoint/weights.csv", delimiter=",")

    # Randomly sample either amino-acid "K" or "P" based on probability p
    rng = np.random.default_rng(seed)
    samples = rng.binomial(1, p, size=(n_sequences, length))
    labels = np.where(samples, "K", "P")

    sequences = ["".join(row) for row in labels]

    return sequences


def main():
    parser = argparse.ArgumentParser(description="Generate sequences of 'K' and 'P'.")
    parser.add_argument(
        "--n_sequences",
        type=int,
        required=True,
        help="Number of sequences to generate",
    )

    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output FASTA file path",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=10,
        help="Length of each sequence",
    )

    args = parser.parse_args()

    print("Running model...")

    sequences = generate(args.n_sequences, length=args.length)

    sm.to_fasta(sequences, args.output)

    print(f"Generated {len(sequences)} sequences → {args.output}")
