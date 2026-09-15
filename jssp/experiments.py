"""Execute the assignment matrix and summarize measured independent runs."""

import json
import platform
import statistics
from pathlib import Path

from .generational_ga import run_ga
from .output import plot_experiments, save_result, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "experiments.json"


def summarize_runs(rows):
    """Summarize one instance/parameter group using sample standard deviations."""
    first = rows[0]
    values = [r["best_makespan"] for r in rows]
    fields = ("category", "instance", "parameter_set", "population_size", "generations",
              "crossover_probability", "mutation_probability", "reference_optimum")
    summary = {key: first[key] for key in fields}
    summary.update(runs=len(rows), best=min(values), worst=max(values),
                   mean=statistics.mean(values), std=statistics.stdev(values),
                   mean_gap_percent=statistics.mean(r["gap_percent"] for r in rows),
                   std_gap_percent=statistics.stdev(r["gap_percent"] for r in rows))
    for field in ("elapsed_seconds", "time_to_best_seconds", "convergence_generation",
                  "final_makespan", "early_improvement_percent", "late_improvement_percent",
                  "unique_evaluations"):
        summary["mean_" + field] = statistics.mean(r[field] for r in rows)
    summary["std_elapsed_seconds"] = statistics.stdev(r["elapsed_seconds"] for r in rows)
    return summary


def run_experiments(config_path=DEFAULT_CONFIG, output=Path("results/final"), runs=None):
    """Run all six instances and three parameter sets, sequentially on one machine."""
    config = json.loads(Path(config_path).read_text())
    if runs is not None:
        config["independent_runs"] = runs
    count = config["independent_runs"]
    if not isinstance(count, int) or count < 10:
        raise ValueError("Assignment experiments require at least 10 independent runs.")
    required = {"small": ["la01", "la02"], "medium": ["la16", "la17"],
                "large": ["la31", "la32"]}
    if config["instances"] != required or len(config["parameter_sets"]) != 3:
        raise ValueError("Use the six bundled instances and exactly three parameter sets.")
    names = [p["name"] for p in config["parameter_sets"]]
    if len(set(names)) != 3 or any(not name.replace("_", "").isalnum() for name in names):
        raise ValueError("Parameter names must be unique letters/digits/underscores.")
    output = Path(output)
    if (output / "manifest.json").exists():
        raise ValueError("This experiment directory already exists; choose another --output.")
    output.mkdir(parents=True, exist_ok=True)
    bounds = json.loads((ROOT / "data" / "reference_bounds.json").read_text())
    references = {r["instance"]: r["upper_bound"] for r in bounds["instances"]}
    if any(r["lower_bound"] != r["upper_bound"] for r in bounds["instances"]):
        raise ValueError("This experiment's gap labels require proven reference optima.")
    # Save only the settings, timing environment, and batch completion status.
    manifest = dict(status="running", config=config, python=platform.python_version(),
                    platform=platform.platform(), total_runs=6 * 3 * count)
    write_json(output / "manifest.json", manifest)
    all_rows, summaries, curves = [], [], []
    completed = 0
    for category, instances in config["instances"].items():
        for instance in instances:
            for parameter_set in config["parameter_sets"]:
                parameters = {k: v for k, v in parameter_set.items() if k != "name"}
                name = parameter_set["name"]
                group_output = output / instance / name
                group_rows, histories = [], []
                best_result = None
                for run in range(count):
                    seed = config["seed_start"] + run
                    result = run_ga(instance=instance, seed=seed, decoder=config["decoder"],
                                    tournament_size=config["tournament_size"], **parameters)
                    history = result["history"]
                    last = len(history) - 1
                    early = history[max(1, last // 4)]["best_so_far"]
                    late_start = history[(3 * last) // 4]["best_so_far"]
                    initial = history[0]["best_so_far"]
                    row = dict(category=category, instance=instance, parameter_set=name,
                               run=run + 1, seed=seed, **parameters,
                               reference_optimum=references[instance],
                               best_makespan=result["best_makespan"],
                               final_makespan=result["final_makespan"],
                               gap_percent=100 * (result["best_makespan"] / references[instance] - 1),
                               elapsed_seconds=result["elapsed_seconds"],
                               time_to_best_seconds=result["time_to_best_seconds"],
                               convergence_generation=result["convergence_generation"],
                               unique_evaluations=result["unique_evaluations"],
                               early_improvement_percent=100 * (initial - early) / initial,
                               late_improvement_percent=100 * (late_start - result["best_makespan"]) / late_start)
                    group_rows.append(row)
                    all_rows.append(row)
                    histories.append(history)
                    raw_output = group_output / "runs"
                    raw_output.mkdir(parents=True, exist_ok=True)
                    write_json(raw_output / f"seed_{seed}.json", result)
                    if best_result is None or result["best_makespan"] < best_result["best_makespan"]:
                        best_result = result
                    completed += 1
                    print(f"[{completed}/{manifest['total_runs']}] {instance}/{name} "
                          f"seed={seed}: best={result['best_makespan']}, "
                          f"time={result['elapsed_seconds']:.2f}s", flush=True)
                summaries.append(summarize_runs(group_rows))
                for generation in range(len(histories[0])):
                    values = [history[generation]["best_so_far"] for history in histories]
                    curves.append(dict(instance=instance, parameter_set=name, generation=generation,
                                       mean_best_so_far=statistics.mean(values),
                                       std_best_so_far=statistics.stdev(values)))
                save_result(best_result, group_output / "best", make_plot=False)
                # Save completed groups incrementally; the manifest marks incomplete batches.
                write_csv(output / "runs.csv", all_rows)
                write_csv(output / "summary.csv", summaries)
                write_csv(output / "convergence.csv", curves)
    runtime_rows = []
    for category, instances in config["instances"].items():
        for instance in instances:
            row = dict(category=category, instance=instance)
            for summary in summaries:
                if summary["instance"] == instance:
                    row[summary["parameter_set"] + "_mean_seconds"] = summary["mean_elapsed_seconds"]
            runtime_rows.append(row)
    write_csv(output / "runtime_table.csv", runtime_rows)
    plot_experiments(curves, summaries, output)
    manifest.update(status="complete", completed_runs=completed)
    write_json(output / "manifest.json", manifest)
    return summaries
