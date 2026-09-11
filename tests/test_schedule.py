"""Check precedence, machine capacity, data loading, and idle-gap insertion."""

import random
import unittest

from jssp.data import load_instance
from jssp.decoder import build_schedule


class ScheduleTests(unittest.TestCase):
    def test_small_example(self):
        jobs = [[(0, 3), (1, 2)], [(1, 4), (0, 1)]]
        schedule, makespan = build_schedule([0, 1, 0, 1], jobs, 2)
        self.assertEqual(makespan, 6)
        self.assertEqual([(op["start"], op["finish"]) for op in schedule],
                         [(0, 3), (0, 4), (4, 6), (4, 5)])

    def test_insertion_fills_an_earlier_gap(self):
        jobs = [[(0, 3)], [(1, 8), (0, 4)], [(2, 4), (0, 2)]]
        chromosome = [0, 1, 1, 2, 2]
        appended, append_end = build_schedule(chromosome, jobs, 3, "append")
        inserted, insert_end = build_schedule(chromosome, jobs, 3, "insertion")
        self.assertEqual(appended[-1]["start"], 12)
        self.assertEqual(inserted[-1]["start"], 4)
        self.assertEqual((append_end, insert_end), (14, 12))

    def test_invalid_chromosome(self):
        for chromosome in ([0], [0, 2], [0, 0]):
            with self.assertRaises(ValueError):
                build_schedule(chromosome, [[(0, 1)], [(0, 2)]], 1)

    def test_all_instances_produce_feasible_schedules(self):
        for name, dimensions in [("la01", (10, 5)), ("la02", (10, 5)),
                                 ("la16", (10, 10)), ("la17", (10, 10)),
                                 ("la31", (30, 10)), ("la32", (30, 10))]:
            n_jobs, n_machines, jobs = load_instance(name)
            self.assertEqual((n_jobs, n_machines), dimensions)
            for method in ("append", "insertion"):
                with self.subTest(instance=name, method=method):
                    chromosome = [job for job, ops in enumerate(jobs) for _ in ops]
                    random.Random(42).shuffle(chromosome)
                    schedule, makespan = build_schedule(chromosome, jobs, n_machines, method)
                    self.assertEqual(len(schedule), sum(map(len, jobs)))
                    for job, operations in enumerate(jobs):
                        placed = sorted((op for op in schedule if op["job"] == job),
                                        key=lambda op: op["operation"])
                        for index, op in enumerate(placed):
                            self.assertEqual(op["machine"], operations[index][0])
                            self.assertEqual(op["finish"] - op["start"], operations[index][1])
                            self.assertGreaterEqual(op["start"], placed[index - 1]["finish"] if index else 0)
                    for machine in range(n_machines):
                        placed = sorted((op for op in schedule if op["machine"] == machine),
                                        key=lambda op: op["start"])
                        for previous, current in zip(placed, placed[1:]):
                            self.assertLessEqual(previous["finish"], current["start"])
                    self.assertEqual(makespan, max(op["finish"] for op in schedule))


if __name__ == "__main__":
    unittest.main()
