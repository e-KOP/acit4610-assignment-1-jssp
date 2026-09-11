"""Decode operation-based chromosomes using append or idle-gap insertion."""

from collections import Counter


def earliest_slot(intervals, ready, duration, method):
    """Find a feasible start without moving any previously placed operation."""
    if method == "append":
        return max(ready, intervals[-1][1] if intervals else 0)
    start = ready
    for occupied_start, occupied_finish in intervals:
        if start + duration <= occupied_start:
            break
        start = max(start, occupied_finish)
    return start


def build_schedule(chromosome, jobs, n_machines, method="insertion"):
    """Return a schedule and makespan; each job occurrence selects its next operation."""
    if method not in {"append", "insertion"}:
        raise ValueError("Method must be append or insertion.")
    if n_machines <= 0 or any(
        not 0 <= machine < n_machines or duration <= 0
        for operations in jobs for machine, duration in operations
    ):
        raise ValueError("Invalid machines or processing times.")
    expected = Counter({job: len(ops) for job, ops in enumerate(jobs)})
    if Counter(chromosome) != expected:
        raise ValueError("Chromosome contains incorrect job counts.")

    next_operation = [0] * len(jobs)
    job_ready = [0] * len(jobs)
    machine_intervals = [[] for _ in range(n_machines)]
    schedule = []
    for job in chromosome:
        operation = next_operation[job]
        machine, duration = jobs[job][operation]
        start = earliest_slot(
            machine_intervals[machine], job_ready[job], duration, method
        )
        finish = start + duration
        schedule.append(dict(
            job=job, operation=operation, machine=machine, start=start, finish=finish
        ))
        machine_intervals[machine].append((start, finish))
        machine_intervals[machine].sort()
        job_ready[job] = finish
        next_operation[job] += 1
    return schedule, max(job_ready, default=0)
