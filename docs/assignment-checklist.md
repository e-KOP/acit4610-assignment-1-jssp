# Assignment implementation checklist

## Available now

- [x] Six Lawrence instances: la01, la02, la16, la17, la31, la32.
- [x] Portable, validated data loader and source attribution.
- [x] Operation-based representation with exact job multiplicities.
- [x] Append and idle-gap insertion schedule builders.
- [x] Reproducible decoder demonstration and CSV/JSON/SVG output.
- [x] Independent checks of precedence, capacity, and processing times.
- [x] Installation and execution instructions with English code comments.

## Algorithm and experiment work remaining

- [ ] Implement population initialization, selection, crossover, mutation, elitism, and termination.
- [ ] Preserve operation counts during crossover and mutation.
- [ ] Evaluate individuals using decoded makespan; lower is better.
- [ ] Implement a runner consuming configs/experiments.json.
- [ ] Run all 6 instances with all 3 parameter sets and 30 independent seeds (540 runs).
- [ ] Record best, worst, mean, standard deviation, execution time, and convergence generation.
- [ ] Define convergence consistently, for example the last generation improving the incumbent.
- [ ] Save raw per-run measurements and incumbent history for reproducibility.
- [ ] Compare results with the bundled reference bounds.
- [ ] Produce parameter comparisons, convergence curves, and a runtime table for all 18 combinations.
- [ ] Interpret parameter effects in early and later generations using measured results.

The planned parameter sets isolate population size and mutation probability relative
to a reference. They do not establish the effects of crossover probability or generation
budget, which are held fixed. Revise the plan if those effects are to be investigated.

## Student submission

- [ ] Students write the 1000-1500-word PDF report themselves.
- [ ] Include the Canvas group number and accessible GitHub repository URL.
- [ ] Explain complete GA design, decoder steps, constraints, fitness, and a worked Gantt example.
- [ ] Include measured comparisons, timing table, findings, and conclusions.
- [ ] Verify instructors can access the repository and run the code.
- [ ] One submission per approved group through Canvas by September 17, 2026, at 12:00.

The assignment permits AI assistance with code subject to university guidance and
prohibits AI-written report text. This checklist is a development aid, not the report.
