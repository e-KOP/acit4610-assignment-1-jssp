"""Demonstrate reading a bundled Lawrence instance."""

from jssp.data import load_instance


if __name__ == "__main__":
    n_jobs, n_machines, jobs = load_instance("la01")
    print("Number of jobs:", n_jobs)
    print("Number of machines:", n_machines)
    print("Job 0:", jobs[0])
    print("Job 2:", jobs[2])

    # Access the first operation of job 2 using zero-based indexing
    machine, duration = jobs[2][0]
    print("Machine ID:", machine)
    print("Processing time:", duration)
