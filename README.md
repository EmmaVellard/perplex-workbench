# Lunar Perple_X EOS Pipeline

This directory contains a local Python pipeline for generating and validating Perple_X WERAMI tables for lunar near-side and far-side mantle models.

The target PlanetProfile-facing table columns are:

```text
T(K), P(bar), rho_kgm3, VP_kms, VS_kms, Cp_Jm3K, alpha_pK, KS_bar, GS_bar
```

## Current Scientific Status

The included near-side and far-side compositions are placeholders. They are useful for testing the pipeline mechanics only. Replace them with published lunar mantle compositions before scientific use.

Do not add native Fe, Ni, or Cu to these silicate mantle compositions unless you are intentionally modeling metallic phases and have verified elastic properties for every relevant phase. Invalid or missing elastic properties can produce bad seismic columns while still allowing Perple_X to write a table.

KREEP, Th, U, and K effects should mostly be represented through PlanetProfile thermal and radiogenic parameters. Oxide composition alone is not a complete treatment of near-side radiogenic structure.

## What Is Automated

- Writes normalized near-side and far-side oxide compositions.
- Writes reproducible `perplex_option.dat` into each model's repo-local work directory.
- Runs BUILD in the model work directory when a configured build input file exists.
- Requires an existing `<project>.dat` in the model work directory when BUILD input is absent.
- Runs VERTEX.
- Runs WERAMI for system properties on a 2D grid using property 38.
- Copies `<work_dir>/<project>_1.tab` to `outputs/<project>/<project>_raw_werami.tab`.
- Writes `outputs/<project>/<project>_planetprofile.tab` with temperature before pressure.
- Saves `build.log`, `vertex.log`, and `werami.log`.
- Writes `validation_report.txt`.
- Exits nonzero when validation fails.

## What Is Not Automated

- Choosing publication-quality lunar compositions.
- Auditing each BUILD prompt for thermodynamic database and solution model choices.
- Deciding whether Perple_X solution models are appropriate for the scientific question.
- Confirming final PlanetProfile thermal, radiogenic, and grid assumptions.

BUILD should still be checked manually because a syntactically valid `.dat` file can encode the wrong database, components, solution model choices, saturation assumptions, or variable ranges.

## Files

```text
configs/models.example.json
run_full_pipeline.py
make_compositions.py
run_perplex.py
validate_tab.py
compositions/
build_inputs/
outputs/
tests/
```

Copy `configs/models.example.json` to `configs/models.json` and set `perplex_dir` to your local Perple_X install. `configs/models.json` is ignored because it is machine-local. It contains the Perple_X install path, project names, composition paths, build input paths, output directories, and optional work directories. The Perple_X install is treated as an external executable dependency; generated files are written under this repository, using `outputs/<project>/work` by default.

The included BUILD input transcripts use `stx21ver.dat` and `stx21_solution_model.dat` from the configured Perple_X install. They use `${PERPLEX_DIR}` placeholders, which the runner replaces from `configs/models.json` at runtime. That Stixrude 2021 database supports `NA2O`, `MGO`, `AL2O3`, `SIO2`, `CAO`, and `FEO`, so the placeholder `TiO2`, `K2O`, and `P2O5` amounts are not passed to BUILD.

## Run Full Pipeline

Run the whole pipeline from this directory:

```bash
python3 run_full_pipeline.py
```

To run one project:

```bash
python3 run_full_pipeline.py --project moon_far_dry_mantle
```

This regenerates compositions, runs BUILD/VERTEX/WERAMI, copies the raw WERAMI table, writes the PlanetProfile-facing table, and writes validation reports. To debug Perple_X without regenerating compositions:

```bash
python3 run_full_pipeline.py --skip-compositions
```

## Generate Compositions

Run from this directory:

```bash
python3 make_compositions.py
```

This writes:

```text
compositions/moon_far_dry_mantle.json
compositions/moon_far_dry_mantle_bulk_values.txt
compositions/moon_far_dry_mantle_summary.txt
compositions/moon_near_pkt_mantle.json
compositions/moon_near_pkt_mantle_bulk_values.txt
compositions/moon_near_pkt_mantle_summary.txt
```

The bulk values are ordered as:

```text
SiO2, TiO2, Al2O3, FeO, MgO, CaO, Na2O, K2O, P2O5
```

## Run Perple_X

Run from this directory:

```bash
python3 run_perplex.py
```

To run one project:

```bash
python3 run_perplex.py --project moon_far_dry_mantle
```

If `build_inputs/<project>.build.in` exists, the runner feeds that file to BUILD from the repo-local model work directory. If it does not exist, `<project>.dat` must already exist in that work directory.

BUILD input files may use these portable placeholders:

```text
${PERPLEX_DIR}
${PROJECT}
${COMPOSITION_FILE}
${OUTPUT_DIR}
${WORK_DIR}
```

The default `perplex_option.dat` written by the runner is intentionally a smoke-test grid:

```text
grid_levels 1 1
x_nodes 20 40
y_nodes 20 40
```

Increase these values only after the pipeline passes validation, because high auto-refine grids can make VERTEX much slower.

WERAMI is called with:

```text
project name
2
38
1
2
13
14
3
4
10
11
0
n
1
0
```

## Validate Outputs

Validation runs automatically at the end of `run_perplex.py`. You can also run it directly:

```bash
python3 validate_tab.py
```

Or for one project:

```bash
python3 validate_tab.py --project moon_far_dry_mantle
```

Validation fails on:

- `Reading solution models from file: not requested`
- `warning ver177`
- `cannot be computed because of missing/invalid properties`
- `0.100000E+100` or `-0.100000E+100`
- missing `.tab` output
- missing required columns
- NaN-only columns
- zero-only `alpha_pK`
- negative density, Vp, Vs, bulk modulus, or shear modulus

A run can have technical success and readiness failure at the same time. Technical success means Perple_X ran and wrote a `.tab` file. Readiness success means the logs and PlanetProfile-facing table pass validation checks.

## Run Tests

The tests do not require real Perple_X. They build fake BUILD, VERTEX, and WERAMI executables in temporary directories.

Run from this directory:

```bash
python3 -m pytest
```

The tests cover successful fake execution plus missing `.dat`, missing executable, missing `.tab`, log warning, bad-number sentinel, and zero-alpha failures.
