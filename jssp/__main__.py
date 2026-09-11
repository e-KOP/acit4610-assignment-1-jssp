"""Run a reproducible decoder demonstration; this is not a genetic algorithm."""

import argparse
import csv
import json
import random
from pathlib import Path

from .data import load_instance
from .decoder import build_schedule
from .output import write_gantt


def main():
    """Read an instance, decode one random chromosome, and export its schedule."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", default="la01")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--decoder", choices=["append", "insertion"], default="insertion")
    parser.add_argument("--output", type=Path, default=Path("results/demo"))
    args = parser.parse_args()
    _, n_machines, jobs = load_instance(args.instance)
    chromosome = [job for job, ops in enumerate(jobs) for _ in ops]
    random.Random(args.seed).shuffle(chromosome)
    schedule, makespan = build_schedule(chromosome, jobs, n_machines, args.decoder)
    args.output.mkdir(parents=True, exist_ok=True)
    result = dict(kind="decoder_demo", instance=args.instance, seed=args.seed,
                  decoder=args.decoder, chromosome=chromosome, makespan=makespan)
    (args.output / "solution.json").write_text(json.dumps(result, indent=2) + "\n")
    with (args.output / "schedule.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["job", "operation", "machine", "start", "finish"])
        writer.writeheader()
        writer.writerows(schedule)
    write_gantt(schedule, n_machines, args.output / "gantt.svg")
    print(f"{args.instance}: makespan={makespan}, decoder={args.decoder}")
    print(f"Outputs: {args.output.resolve()}")


if __name__ == "__main__":
    main()
