"""Read and validate Lawrence job shop instances."""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "lawrence"


def load_instance(name):
    """Return job count, machine count, and ordered machine-duration pairs."""
    if name not in {"la01", "la02", "la16", "la17", "la31", "la32"}:
        raise ValueError(f"Unknown bundled instance: {name}")
    rows = [
        list(map(int, line.split()))
        for line in (DATA_DIR / f"{name}.txt").read_text().splitlines()
        if line.strip()
    ]
    n_jobs, n_machines = rows[0]
    if len(rows[1:]) != n_jobs or n_jobs <= 0 or n_machines <= 0:
        raise ValueError("Invalid instance dimensions.")
    jobs = []
    for row in rows[1:]:
        if len(row) != 2 * n_machines:
            raise ValueError("Incorrect operation count.")
        operations = list(zip(row[::2], row[1::2]))
        if any(not 0 <= m < n_machines or d <= 0 for m, d in operations):
            raise ValueError("Invalid machine ID or processing time.")
        jobs.append(operations)
    return n_jobs, n_machines, jobs
