"""Verify GA invariants, reproducibility, replacement, and experimental metrics."""

import copy
import random
import statistics
import unittest
from unittest.mock import patch

from jssp.data import load_instance
from jssp.decoder import build_schedule, validate_schedule
from jssp.experiments import summarize_runs
from jssp.generational_ga import (
    crossover, evaluate_population, evolve_generation, initialize_population,
    mutate, run_ga,
)
from collections import Counter


class GeneticAlgorithmTests(unittest.TestCase):
    def test_offspring_preserve_counts_and_parents(self):
        for name in ('la01', 'la16', 'la31'):
            _, machines, jobs = load_instance(name)
            rng = random.Random(42)
            parents = initialize_population(jobs, 2, rng)
            original = copy.deepcopy(parents)
            for _ in range(20):
                for child in crossover(*parents, rng, probability=1):
                    mutated = mutate(child, rng, probability=1)
                    self.assertNotEqual(mutated, child)
                    self.assertEqual(Counter(mutated), Counter(parents[0]))
                    schedule, makespan = build_schedule(mutated, jobs, machines)
                    validate_schedule(schedule, jobs, machines, makespan)
            self.assertEqual(parents, original)

    def test_skipped_operators_return_independent_copies(self):
        a, b = [0, 1, 0, 1], [1, 0, 1, 0]
        rng = random.Random(7)
        children = crossover(a, b, rng, probability=0)
        self.assertEqual(children, (a, b))
        self.assertIsNot(children[0], a)
        self.assertIsNot(children[1], b)
        result = mutate(a, rng, probability=0)
        self.assertEqual(result, a)
        self.assertIsNot(result, a)

    def test_replacement_does_not_automatically_preserve_best(self):
        population = [[0, 1, 0, 1], [0, 0, 1, 1], [1, 1, 0, 0]]
        snapshot = copy.deepcopy(population)
        with patch('jssp.generational_ga.select_parent', return_value=population[1].copy()):
            children = evolve_generation(population, [6, 10, 10], random.Random(0), 0, 0)
        self.assertEqual(len(children), 3)
        self.assertTrue(all(c == population[1] for c in children))
        self.assertNotIn(population[0], children)
        self.assertEqual(population, snapshot)
        self.assertEqual(len({id(c) for c in children}), 3)

    def test_cache_changes_no_scores(self):
        _, machines, jobs = load_instance('la01')
        population = initialize_population(jobs, 5, random.Random(12))
        population.append(population[0].copy())
        cache = {}
        scores = evaluate_population(population, jobs, machines, cache=cache)
        direct = [build_schedule(c, jobs, machines)[1] for c in population]
        self.assertEqual(scores, direct)
        self.assertEqual(len(cache), 5)

    def test_reproducibility_and_reporting_archive(self):
        parameters = dict(population_size=4, generations=10, seed=42, decoder='append',
                          crossover_probability=0.9, mutation_probability=0.2)
        a, b = run_ga(**parameters), run_ga(**parameters)
        for key in ('chromosome', 'schedule', 'best_makespan', 'final_makespan',
                    'convergence_generation', 'unique_evaluations'):
            self.assertEqual(a[key], b[key])
        history = a['history']
        self.assertEqual(len(history), 11)
        observed = [h['generation_best'] for h in history]
        self.assertEqual(a['best_makespan'], min(observed))
        self.assertEqual(a['final_makespan'], observed[-1])
        self.assertEqual(a['convergence_generation'], observed.index(min(observed)))
        self.assertEqual([h['best_so_far'] for h in history],
                         [min(observed[:i+1]) for i in range(len(observed))])
        self.assertGreaterEqual(a['elapsed_seconds'], a['time_to_best_seconds'])

    def test_all_instances_with_even_and_odd_populations(self):
        for name in ('la01', 'la02', 'la16', 'la17', 'la31', 'la32'):
            for size in (4, 5):
                result = run_ga(instance=name, population_size=size, generations=2)
                _, machines, jobs = load_instance(name)
                validate_schedule(result['schedule'], jobs, machines, result['best_makespan'])

    def test_zero_generations_and_invalid_parameters(self):
        result = run_ga(population_size=4, generations=0)
        self.assertEqual(len(result['history']), 1)
        self.assertEqual(result['convergence_generation'], 0)
        for parameters in ({'population_size': 1}, {'generations': -1},
                           {'tournament_size': 51}, {'mutation_probability': 2}):
            with self.assertRaises(ValueError):
                run_ga(**parameters)

    def test_summary_uses_sample_standard_deviation(self):
        rows = []
        for value in (10, 12, 14):
            rows.append(dict(category='small', instance='toy', parameter_set='reference',
                             population_size=4, generations=10, crossover_probability=0.8,
                             mutation_probability=0.1, reference_optimum=10,
                             best_makespan=value, final_makespan=value, gap_percent=(value-10)*10,
                             elapsed_seconds=2, time_to_best_seconds=1,
                             convergence_generation=5, early_improvement_percent=10,
                             late_improvement_percent=1, unique_evaluations=20))
        summary = summarize_runs(rows)
        self.assertEqual((summary['best'], summary['worst'], summary['mean']), (10, 14, 12))
        self.assertEqual(summary['std'], statistics.stdev((10, 12, 14)))
        self.assertEqual(summary['mean_gap_percent'], 20)
        self.assertEqual(summary['mean_elapsed_seconds'], 2)

    def test_schedule_validator_rejects_corruption(self):
        jobs = [[(0, 3), (1, 2)], [(1, 4), (0, 1)]]
        schedule, end = build_schedule([0, 1, 0, 1], jobs, 2)
        variants = [schedule[:-1], schedule + [schedule[0]]]
        bad = copy.deepcopy(schedule)
        bad[-1].update(start=2, finish=3)
        variants.append(bad)
        bad = copy.deepcopy(schedule)
        bad[0]['finish'] = 99
        variants.append(bad)
        for variant in variants:
            with self.assertRaises(ValueError):
                validate_schedule(variant, jobs, 2, end)


if __name__ == '__main__':
    unittest.main()
