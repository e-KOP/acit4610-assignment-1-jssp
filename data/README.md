# Benchmark provenance

These six text instances are unchanged copies from ScheduleOpt/benchmarks.

- Source: https://github.com/ScheduleOpt/benchmarks
- Commit: `79f0edc1a2e95ed0e3cc105e79a6d03910a6d091`
- Source directory: `jobshop/instances/text/Lawrence1984/`
- Original family: Lawrence (1984), Resource constrained project scheduling: An experimental investigation of heuristic scheduling techniques (Supplement), Carnegie-Mellon University.
- Retrieved from the existing local clone on September 11, 2026.
- License: CC BY-SA 4.0; the upstream license is included in [LICENSE](LICENSE).
- `checksums.json` records the SHA-256 digest of each unchanged text file.
- `reference_bounds.json` contains only the six selected records extracted from the upstream `jobshop/solutions/bks.json` at the same revision. The subset extraction and provenance wrapper are the only changes.

The first line gives job and machine counts. Each subsequent line is one job's ordered machine-duration pairs. Machine IDs are zero-based. Durations use the benchmark's abstract time unit.

Reference bounds are comparison targets, not results produced by this project. Preserve this attribution and the upstream license when redistributing the data.
