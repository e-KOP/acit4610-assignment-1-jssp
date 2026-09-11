# ACIT4610: Job Shop Scheduling with Genetic Algorithms

Python project for ACIT4610 Assignment 1: minimize job shop makespan using a genetic
algorithm and a schedule building algorithm (SBA).

**Current status:** runnable data loader and SBA foundation. The genetic algorithm
and repeated statistical experiments are not implemented yet. The demo evaluates
one shuffled chromosome; its output must not be presented as GA performance.

Group number: to be supplied by the student group before submission.

## Requirements and setup

Python 3.10 or newer and Git. The current implementation has no third-party dependencies.

```bash
git clone https://github.com/e-KOP/acit4610-assignment-1-jssp.git
cd acit4610-assignment-1-jssp
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

This repository is public: anyone can clone it. Pushing a branch to this repository
requires collaborator access; ask the repository owner to invite your GitHub account.
On Windows, use `py -m venv .venv` and `.venv\Scripts\Activate.ps1` in PowerShell.
Run commands from the repository root. A virtual environment is optional for the
current standard-library-only implementation.

## Run a schedule-building example

```bash
python -m jssp --instance la01 --seed 42 --decoder insertion --output results/la01-insertion
python -m jssp --instance la01 --seed 42 --decoder append --output results/la01-append
```

Each command produces:

- `solution.json`: instance, seed, method, chromosome, and makespan.
- `schedule.csv`: job, operation, machine, start, and finish for every operation.
- `gantt.svg`: machine-based Gantt chart; open in a browser and hover for operation details.

Repeating the same seed and method produces the same schedule. Existing files in
the specified output directory are replaced; use distinct directories to retain runs.

## Read data in Python

```python
from jssp.data import load_instance

n_jobs, n_machines, jobs = load_instance("la01")
machine, duration = jobs[2][0]  # First operation of job 2
```

Paths are resolved relative to the source file, without machine-specific absolute paths.
The six selected instances are bundled in `data/lawrence`, so no download is required.

| Category | Instances | Jobs | Machines |
| --- | --- | ---: | ---: |
| Small | la01, la02 | 10 | 5 |
| Medium | la16, la17 | 10 | 10 |
| Large | la31, la32 | 30 | 10 |

See [data provenance](data/README.md) for source revision, checksums, and license.

## Representation and decoding

A gene is a zero-based job ID. The kth occurrence of that job schedules its kth
operation. For la01, a chromosome has 50 genes: each ID from 0 to 9 occurs five times.
The decoder rejects missing, extra, or unknown job IDs.

The append builder uses `start = max(job_ready, machine_finish)`. The insertion
builder scans the machine's occupied intervals to find the earliest sufficiently
large gap after `job_ready`. If no gap fits, it appends the operation. It never moves
previously scheduled operations. Processing times and machine assignments come from
the dataset, and `finish = start + duration`.

Both builders enforce job precedence and prevent machine overlap. Makespan is the
largest finish time. Neither builder by itself searches across chromosomes or
guarantees a globally optimal solution. Insertion does not guarantee a smaller
makespan than append for every chromosome.

## Add your own genetic algorithm

Use the existing data loader, decoder, and output functions so your implementation
works with the same inputs and produces the same schedule format. The steps below
describe how to integrate your code; `jssp/ga.py` does not exist yet.

### 1. Create your algorithm module

Create `jssp/ga.py` and implement a function named `genetic_algorithm`. Keep your
initialization, selection, crossover, mutation, and termination logic in this module.
The function should accept `jobs`, `n_machines`, `population_size`, `generations`,
`crossover_probability`, `mutation_probability`, `seed`, and `decoder`.

`jobs[job_id][operation_id]` contains `(machine_id, duration)`. All IDs are zero-based,
and each job's list is already in its required processing order. Read a different
instance with `load_instance("la16")`, for example; do not hard-code machine paths
or modify the benchmark files. Treat `jobs` as read-only during optimization.

### 2. Build chromosomes and evaluate them with SBA

This runnable example shows the connection between the data and one fitness evaluation:

```python
import random
from jssp.data import load_instance
from jssp.decoder import build_schedule

_, n_machines, jobs = load_instance("la01")
rng = random.Random(42)
chromosome = [job_id for job_id, operations in enumerate(jobs) for _ in operations]
rng.shuffle(chromosome)

schedule, makespan = build_schedule(
    chromosome, jobs, n_machines, method="insertion"
)
print("Makespan:", makespan)
```

Inside your GA, use the supplied seed to create one local random generator and use
it throughout the run. Initialize each individual from a separate copy of the
chromosome template. Crossover and mutation must preserve each job's occurrence
count: for la01, every ID from 0 to 9 must appear exactly five times.

Call `build_schedule(..., method=decoder)` whenever you evaluate an individual.
It returns **`(schedule, makespan)`**, in that order. Lower makespan is better;
selection must prefer lower values. The supported decoder names are `append` and
`insertion`. Keep any fitness transformation inside your GA.

### 3. Return a common result format

At the end of your GA, decode the best chromosome again and return:

```python
best_schedule, best_makespan = build_schedule(
    best_chromosome, jobs, n_machines, method=decoder
)
return best_chromosome, best_makespan, best_schedule, history
```

This snippet belongs inside `genetic_algorithm`. Let `history` contain the best
makespan found so far: index 0 for the initial population, followed by one value
per completed generation. Keep the schedule returned by SBA unchanged: it is a list
of dictionaries with `job`, `operation`, `machine`, `start`, and `finish` fields.
The existing CSV writer and Gantt exporter expect these fields.

### 4. Connect the algorithm to the command-line entry point

After implementing the function, add `from .ga import genetic_algorithm` to
`jssp/__main__.py`. In `main()`, replace the current block that loads data, shuffles
one chromosome, and calls `build_schedule` with:

```python
_, n_machines, jobs = load_instance(args.instance)
ga_parameters = {
    "population_size": 50,
    "generations": 100,
    "crossover_probability": 0.8,
    "mutation_probability": 0.1,
}
chromosome, makespan, schedule, history = genetic_algorithm(
    jobs=jobs,
    n_machines=n_machines,
    seed=args.seed,
    decoder=args.decoder,
    **ga_parameters,
)
```

Keep the existing output code. Immediately after the `result = dict(...)` statement,
before writing `solution.json`, add:

```python
result.update(kind="genetic_algorithm", parameters=ga_parameters, history=history)
```

Remove unused imports and update the entry point's description to match the GA.
Then run the same command from the repository root:

```bash
python -m jssp --instance la01 --seed 42 --decoder insertion --output results/la01-ga
```

After these edits, the command runs your GA and saves its best schedule. Before
these edits, it remains a single-chromosome decoder demo. The fixed parameters above
are for initial integration; `configs/experiments.json` still needs a separate batch
runner to execute all parameter sets and independent runs.

### 5. Check the integration before sharing

Run the existing tests and add GA tests under `tests/` for valid offspring, repeatable
results with a fixed seed, and feasibility of the returned best schedule. Existing
SBA tests alone do not verify a newly added GA. Add any third-party dependencies to
`requirements.txt`, update the README's current status, and submit your changes on
a branch through a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow.

## Verify correctness

```bash
python -m unittest discover -s tests -v
```

Tests cover a worked two-job example, gap insertion, invalid chromosomes, and all
six instances under both builders. Feasibility checks independently verify durations,
precedence, machine capacity, operation counts, and makespan.

## Project structure

```text
jssp/data.py                 Instance loading and validation
jssp/decoder.py              Append and insertion schedule builders
jssp/output.py               SVG Gantt export
jssp/__main__.py             Reproducible decoder demo
job_shop.py                  Small data-reading example
data/lawrence/               Six selected benchmark instances
data/reference_bounds.json  Reference bounds from the upstream snapshot
configs/experiments.json     Planned parameter sets and independent runs
tests/                      Correctness tests
results/                    Generated output
docs/assignment-checklist.md Remaining algorithm, experiment, and submission work
```

The experiment configuration defines 18 combinations and 30 runs per combination.
It is a plan; the demo does not consume it. Follow the
[assignment checklist](docs/assignment-checklist.md) to complete the GA and analysis.
The report must be written by the student group according to the assignment rules.

## Git workflow

```bash
git switch -c codex/ga-selection
# Edit and test the implementation
git add jssp tests README.md
git commit -m "Implement tournament selection"
git push -u origin codex/ga-selection
```

Use descriptive branches and small commits. Before submission, provide instructor
access to the repository and confirm a clean clone can reproduce the outputs.
