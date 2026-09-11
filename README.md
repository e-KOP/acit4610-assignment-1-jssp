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

For a private repository, clone using an account that has repository access.
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
