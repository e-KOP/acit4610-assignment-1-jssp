"""Generational GA with complete replacement and a reporting-only best archive."""

import random
from collections import Counter
from time import perf_counter

from .data import load_instance
from .decoder import build_schedule, validate_schedule


def initialize_population(jobs, population_size, rng, verbose=False):
    """Shuffle independent copies containing one job ID per operation."""
    # The kth occurrence of a job selects its kth operation during decoding.
    base = [job for job, operations in enumerate(jobs) for _ in operations]
    population = []
    for index in range(population_size):
        chromosome = base.copy()
        rng.shuffle(chromosome)
        population.append(chromosome)
        if verbose:
            print(f"Initial individual {index}: {chromosome}")
    return population


def evaluate_population(population, jobs, n_machines, decoder="insertion",
                        cache=None, verbose=False):
    """Minimize SBA makespan; reuse scores only for exactly identical chromosomes."""
    # The cache belongs to one run, whose jobs and decoder never change.
    if cache is None:
        cache = {}
    scores = []
    for index, chromosome in enumerate(population):
        key = tuple(chromosome)
        if key not in cache:
            _, cache[key] = build_schedule(chromosome, jobs, n_machines, decoder)
        scores.append(cache[key])
        if verbose:
            print(f"Individual {index}: makespan = {cache[key]}")
    return scores


def select_parent(population, scores, rng, tournament_size=2, verbose=False):
    """Select the lowest-makespan candidate from one random tournament."""
    # Indices identify complete individuals. Different tournaments can reuse a parent.
    candidates = rng.sample(range(len(population)), tournament_size)
    winner = min(candidates, key=lambda index: scores[index])
    if verbose:
        print("Tournament:", [(index, scores[index]) for index in candidates])
        print(f"Selected parent: {winner}")
    return population[winner].copy()


def fill_child(first_parent, second_parent, kept_jobs):
    """Keep selected jobs in position and fill gaps in the other parent's order."""
    child = [gene if gene in kept_jobs else None for gene in first_parent]
    remaining = iter(gene for gene in second_parent if gene not in kept_jobs)
    for position in range(len(child)):
        if child[position] is None:
            child[position] = next(remaining)
    return child


def crossover(parent_a, parent_b, rng, probability=0.8, verbose=False):
    """Create two children without changing any job's occurrence count."""
    if Counter(parent_a) != Counter(parent_b):
        raise ValueError("Parents must contain the same job counts.")
    job_ids = sorted(set(parent_a))
    # Probability applies once per pair; skipped crossover still produces copies.
    if len(job_ids) < 2 or rng.random() >= probability:
        if verbose:
            print("Crossover skipped; copying parents.")
        return parent_a.copy(), parent_b.copy()
    # Keep ALL occurrences of selected IDs, so repair is unnecessary.
    kept_jobs = set(rng.sample(job_ids, len(job_ids) // 2))
    if verbose:
        print("Crossover: jobs kept in position:", sorted(kept_jobs))
    return (fill_child(parent_a, parent_b, kept_jobs),
            fill_child(parent_b, parent_a, kept_jobs))


def mutate(chromosome, rng, probability=0.1, verbose=False):
    """Apply at most one swap per chromosome, preserving all job counts."""
    child = chromosome.copy()
    # Probability applies per chromosome, not per gene.
    if len(set(child)) < 2 or rng.random() >= probability:
        if verbose:
            print("Mutation skipped.")
        return child
    first = rng.randrange(len(child))
    # Swapping different IDs guarantees a changed sequence, not a better score.
    second = rng.choice([i for i, gene in enumerate(child) if gene != child[first]])
    if verbose:
        print(f"Mutation: positions {first} <-> {second}, "
              f"jobs {child[first]} <-> {child[second]}")
    child[first], child[second] = child[second], child[first]
    return child


def evolve_generation(population, scores, rng, crossover_probability,
                      mutation_probability, tournament_size=2, verbose=False):
    """Fill an empty population with offspring; never insert an elite."""
    next_population = []
    while len(next_population) < len(population):
        # Select only from the current generation, never partially created offspring.
        parent_a = select_parent(population, scores, rng, tournament_size, verbose)
        parent_b = select_parent(population, scores, rng, tournament_size, verbose)
        children = crossover(parent_a, parent_b, rng, crossover_probability, verbose)
        for child in children:
            if len(next_population) == len(population):
                break  # Discard the surplus child when population size is odd.
            next_population.append(mutate(child, rng, mutation_probability, verbose))
            if verbose:
                print(f"Next population: {len(next_population)}/{len(population)}")
    return next_population


def run_ga(instance="la01", population_size=50, generations=150,
           crossover_probability=0.8, mutation_probability=0.1,
           tournament_size=2, seed=42, decoder="insertion", verbose=False):
    """Return measured results, the best observed schedule, and generation history."""
    if population_size < 2 or generations < 0:
        raise ValueError("Use population_size >= 2 and generations >= 0.")
    if not 1 <= tournament_size <= population_size:
        raise ValueError("Tournament size must be within the population size.")
    if not all(0 <= p <= 1 for p in (crossover_probability, mutation_probability)):
        raise ValueError("Probabilities must be between 0 and 1.")
    if decoder not in {"append", "insertion"}:
        raise ValueError("Decoder must be append or insertion.")
    _, n_machines, jobs = load_instance(instance)
    rng = random.Random(seed)
    cache = {}
    # Exclude data loading, plotting and export from optimization time.
    started = perf_counter()
    population = initialize_population(jobs, population_size, rng, verbose)
    best_makespan = float("inf")
    best_chromosome = None
    best_found_generation = 0
    time_to_best = 0.0
    history = []

    for generation in range(generations + 1):
        # Generation zero is initialization, followed by exactly G full replacements.
        scores = evaluate_population(population, jobs, n_machines, decoder, cache, verbose)
        winner = min(range(population_size), key=lambda i: scores[i])
        elapsed = perf_counter() - started
        if scores[winner] < best_makespan:
            best_makespan = scores[winner]
            best_chromosome = population[winner].copy()
            best_found_generation = generation
            time_to_best = elapsed
        # This archive is only for reporting; it never participates in reproduction.
        history.append(dict(generation=generation, generation_best=min(scores),
                            generation_mean=sum(scores) / population_size,
                            best_so_far=best_makespan, elapsed_seconds=elapsed))
        if verbose:
            print(f"Generation {generation}: current={min(scores)}, "
                  f"best_seen={best_makespan}, mean={sum(scores) / population_size:.2f}")
        if generation < generations:
            population = evolve_generation(population, scores, rng, crossover_probability,
                                           mutation_probability, tournament_size, verbose)

    elapsed_seconds = perf_counter() - started
    schedule, checked_makespan = build_schedule(best_chromosome, jobs, n_machines, decoder)
    validate_schedule(schedule, jobs, n_machines, checked_makespan)
    assert checked_makespan == best_makespan
    return dict(instance=instance, seed=seed, decoder=decoder,
                parameters=dict(population_size=population_size, generations=generations,
                                crossover_probability=crossover_probability,
                                mutation_probability=mutation_probability,
                                tournament_size=tournament_size),
                best_makespan=best_makespan, final_makespan=min(scores),
                convergence_generation=best_found_generation,
                time_to_best_seconds=time_to_best, elapsed_seconds=elapsed_seconds,
                unique_evaluations=len(cache), chromosome=best_chromosome,
                schedule=schedule, history=history)
