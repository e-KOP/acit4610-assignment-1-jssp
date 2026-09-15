"""Run one GA, the assignment experiment matrix, or a small decoding example."""

import argparse
from pathlib import Path

from .decoder import build_schedule, validate_schedule
from .experiments import DEFAULT_CONFIG, run_experiments
from .generational_ga import run_ga
from .output import save_result, write_csv, write_gantt, write_json


def decoding_example(output):
    """Export a transparent genotype-to-schedule example with zero-based IDs."""
    jobs = [[(0, 3), (1, 2)], [(1, 4), (0, 1)]]
    chromosome = [0, 1, 0, 1]
    schedule, makespan = build_schedule(chromosome, jobs, 2, "append")
    validate_schedule(schedule, jobs, 2, makespan)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "example.json", dict(jobs=jobs, chromosome=chromosome,
                                           decoder="append", makespan=makespan,
                                           schedule=schedule))
    write_csv(output / "decoding_steps.csv", [dict(step=i + 1, gene=chromosome[i], **op)
                                             for i, op in enumerate(schedule)])
    write_gantt(schedule, 2, output / "gantt.svg")
    print("Chromosome:", chromosome)
    for step, op in enumerate(schedule, 1):
        print(f"Step {step}: {op}")
    print("Makespan:", makespan)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--experiments", action="store_true")
    mode.add_argument("--example", action="store_true")
    parser.add_argument("--instance", default="la01")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--generations", type=int, default=150)
    parser.add_argument("--crossover", type=float, default=0.8)
    parser.add_argument("--mutation", type=float, default=0.1)
    parser.add_argument("--tournament-size", type=int, default=2)
    parser.add_argument("--decoder", choices=["append", "insertion"], default="insertion")
    parser.add_argument("--verbose", action="store_true", help="Print teaching traces for one GA run.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--runs", type=int, help="Override independent runs per experiment (minimum 10).")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.experiments:
        output = args.output or Path("results/final")
        run_experiments(args.config, output, args.runs)
    elif args.example:
        output = args.output or Path("results/example")
        decoding_example(output)
    else:
        output = args.output or Path("results/single")
        result = run_ga(instance=args.instance, seed=args.seed,
                        population_size=args.population_size, generations=args.generations,
                        crossover_probability=args.crossover, mutation_probability=args.mutation,
                        tournament_size=args.tournament_size, decoder=args.decoder, verbose=args.verbose)
        save_result(result, output)
        print(f"{args.instance}: best observed={result['best_makespan']}, "
              f"last generation={result['final_makespan']}, "
              f"time={result['elapsed_seconds']:.3f}s")
    print(f"Outputs: {output.resolve()}")


if __name__ == "__main__":
    main()
