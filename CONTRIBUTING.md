# Four-person collaboration

Each group member should use their own GitHub account. The repository owner can
invite the other three members through Settings > Collaborators when their usernames
are available. No invitations have been sent during initial setup.

## Shared workflow

1. Clone the repository after receiving access.
2. Start from the latest main branch: `git switch main` then `git pull --ff-only`.
3. Create a descriptive branch, for example `git switch -c codex/ga-crossover`.
4. Keep code comments, docstrings, and README instructions in English.
5. Run `python -m unittest discover -s tests -v` before committing.
6. Push the branch and open a pull request describing behavior and validation.
7. Ask another group member to review it before merging into main.

Review is a team convention; branch protection has not been configured. Avoid force
pushes to main. Do not commit credentials, virtual environments, or fabricated results.

## Suggested responsibilities

| Work area | Responsibilities |
| --- | --- |
| Data and decoding | Loader, representation, SBA, feasibility validation |
| Genetic algorithm | Selection, crossover, mutation, elitism, termination |
| Experiments | Independent seeds, three parameter sets, raw measurements, statistics |
| Visualization and integration | Gantt charts, convergence curves, reproducibility, README |

Assign these areas among the four members together. Each member should understand
the complete pipeline and contribute to the student-written report.

Before submission, add the Canvas group number and ensure the instructor has access.
