# Lunar Perple_X EOS Pipeline

This directory contains a local Python pipeline for generating and validating Perple_X WERAMI tables for lunar near-side and far-side lunar composition proxies.

For the current composition numbers and caveats, see [composition.md](composition.md).

The target PlanetProfile-facing table columns are:

```text
T(K), P(bar), rho_kgm3, VP_kms, VS_kms, Cp_Jm3K, alpha_pK, KS_bar, GS_bar
```

## Current Scientific Status

The included near-side and far-side compositions are first-pass literature-based terrane proxies. They are useful for testing the pipeline mechanics and comparing an enriched nearside/maria-like case against a depleted farside/highlands-like case, but they are not final lunar mantle compositions.

The far-side model uses a commonly tabulated highlands surface average: SiO2 45.5, Al2O3 24.0, CaO 15.9, FeO 5.9, MgO 7.5, TiO2 0.6, and Na2O 0.6 wt%. The near-side model uses a commonly tabulated maria surface average: SiO2 45.4, Al2O3 14.9, CaO 11.8, FeO 14.1, MgO 9.2, TiO2 3.9, and Na2O 0.6 wt%. These values match the maria/highlands oxide table reproduced in lunar geology references and are consistent with the expected contrast that maria are richer in Fe and Ti, while highlands are richer in Al and Ca. Modern mapping studies such as Lu et al. (2020) also emphasize this maria/highlands chemical contrast, and recent lunar-composition reviews note that inferred lunar mantle FeO is commonly higher than Earth's mantle.

Reference trail for these first-pass choices:

- [Lunar surface chemical composition table](https://en.wikipedia.org/wiki/Geology_of_the_Moon#Elemental_composition), which reproduces common maria/highlands oxide averages and cites Taylor and Papike lunar petrology references.
- [Lu et al. (2020), Seamless maps of major elements of the Moon](https://arxiv.org/abs/2007.15858), for the mapped contrast between mare and highland major-element abundances.
- [Sossi et al. (2024), Composition, Structure and Origin of the Moon](https://arxiv.org/abs/2408.16840), for broader bulk silicate Moon and lunar mantle composition context.

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
- Writes `outputs/<project>/<project>_planetprofile_native.tab` in the native Perple_X/PlanetProfile table layout.
- Saves `build.log`, `vertex.log`, and `werami.log`.
- Warns when nonzero oxides in the composition JSON are omitted from the active Perple_X BUILD component list.
- Writes comparison SVG plots under `outputs/comparisons/`.
- Exports PlanetProfile-ready `.tab` files to a chosen directory when requested.
- Writes `validation_report.txt`.
- Exits nonzero when validation fails.

## What Is Not Automated

- Choosing publication-quality lunar mantle compositions.
- Auditing each BUILD prompt for thermodynamic database and solution model choices.
- Deciding whether Perple_X solution models are appropriate for the scientific question.
- Confirming final PlanetProfile thermal, radiogenic, and grid assumptions.

BUILD should still be checked manually because a syntactically valid `.dat` file can encode the wrong database, components, solution model choices, saturation assumptions, or variable ranges.

## Files

```text
configs/models.example.json
build_inputs/lunar_stx21_template.build.in
run_full_pipeline.py
make_compositions.py
run_perplex.py
validate_tab.py
plot_comparisons.py
planetprofile_tables.py
export_planetprofile.py
composition.md
compositions/
build_inputs/
outputs/
tests/
```

Copy `configs/models.example.json` to `configs/models.json` and set `perplex_dir` to your local Perple_X install. `configs/models.json` is ignored because it is machine-local. The Perple_X install is treated as an external executable dependency; generated files are written under this repository, using `outputs/<project>/work` by default.

For normal use, `configs/models.json` is the only file you need to edit. Each model block contains the project name, the optional PlanetProfile export filename, and the oxide composition:

```json
{
  "project": "moon_far_dry_mantle",
  "planetprofile_filename": "Moon_Far_Highlands_proxy_PerpleX.tab",
  "oxides_wt_percent": {
    "SiO2": 45.5,
    "TiO2": 0.6,
    "Al2O3": 24.0,
    "FeO": 5.9,
    "MgO": 7.5,
    "CaO": 15.9,
    "Na2O": 0.6,
    "K2O": 0.0,
    "P2O5": 0.0
  }
}
```

The pipeline turns these inline model definitions into `compositions/<project>.json`, renders the generic BUILD transcript, runs Perple_X, validates the generated table, and optionally exports a PlanetProfile-ready `.tab` file.

Advanced overrides are still supported. A model can set `composition_file`, `build_input_file`, `output_dir`, or `work_dir` if it needs custom files or non-default directories. If those fields are omitted, the pipeline uses the inline oxides, `build_inputs/lunar_stx21_template.build.in`, and `outputs/<project>/`.

The included BUILD template uses `stx21ver.dat` and `stx21_solution_model.dat` from the configured Perple_X install. It uses `${PERPLEX_DIR}` placeholders, which the runner replaces from `configs/models.json` at runtime. It also uses `${PERPLEX_BULK_VALUES}`, which the runner expands from each composition JSON in the Perple_X component order `NA2O MGO AL2O3 SIO2 CAO FEO`. That Stixrude 2021 database supports `NA2O`, `MGO`, `AL2O3`, `SIO2`, `CAO`, and `FEO`, so `TiO2`, `K2O`, and `P2O5` are retained in the composition record but are not passed to BUILD.

When a composition contains a nonzero oxide that is not passed to BUILD, the runner prints a warning and writes `outputs/<project>/oxide_omissions.txt`.

The BUILD template currently excludes pure `qtz` because this database can produce invalid quartz seismic properties for the highlands-like proxy over the smoke-test P-T grid. That exclusion keeps PlanetProfile-facing density and seismic tables finite, but it should be revisited if the goal shifts from pipeline testing to a publication-quality crust or mantle-crust equilibrium model.

## Run Full Pipeline

Run the whole pipeline from this directory:

```bash
python3 run_full_pipeline.py
```

This is the recommended entry point. It reads `configs/models.json`, regenerates the configured compositions, renders BUILD input from the template, runs BUILD/VERTEX/WERAMI, writes PlanetProfile-facing tables, validates the outputs, and writes comparison plots.

To run one project:

```bash
python3 run_full_pipeline.py --project moon_far_dry_mantle
```

The default full run writes:

```text
outputs/comparisons/composition_oxides.svg
outputs/comparisons/planetprofile_properties.svg
```

To debug Perple_X without regenerating compositions:

```bash
python3 run_full_pipeline.py --skip-compositions
```

To skip comparison plots:

```bash
python3 run_full_pipeline.py --skip-plots
```

To generate, validate, and export PlanetProfile-ready EOS files into this repository:

```bash
python3 run_full_pipeline.py --export-planetprofile
```

This writes export copies and a manifest under:

```text
outputs/planetprofile_export/
```

To export directly to a PlanetProfile checkout, pass the target EOS table directory explicitly:

```bash
python3 run_full_pipeline.py \
  --export-planetprofile \
  --planetprofile-export-dir /path/to/PlanetProfile/PlanetProfile/Thermodynamics/EOStables/Perple_X
```

Then set the relevant PlanetProfile config field, for example `Planet.Sil.mantleEOS`, to the exported filename.

## Add A New Model

For a new composition, add one block to `configs/models.json` under `models`:

```json
{
  "project": "moon_custom_model",
  "description": "Short scientific description",
  "planetprofile_filename": "Moon_Custom_Model_PerpleX.tab",
  "scientific_status": "draft",
  "literature_proxy": true,
  "source_note": "Where these numbers came from and what they represent.",
  "oxides_wt_percent": {
    "SiO2": 45.0,
    "TiO2": 1.0,
    "Al2O3": 18.0,
    "FeO": 10.0,
    "MgO": 12.0,
    "CaO": 13.0,
    "Na2O": 1.0,
    "K2O": 0.0,
    "P2O5": 0.0
  }
}
```

Then run only that model:

```bash
python3 run_full_pipeline.py --project moon_custom_model --export-planetprofile
```

The oxide values do not need to add to exactly 100; the composition generator normalizes them and records both the raw and normalized values. If you include oxides that are not in the active BUILD component list, such as `TiO2`, the pipeline keeps them in the composition record and prints an omission warning when they are not passed to Perple_X.

## Generate Compositions

Run from this directory:

```bash
python3 make_compositions.py
```

This reads `configs/models.json` and writes one composition set per configured model, for example:

```text
compositions/moon_far_dry_mantle.json
compositions/moon_far_dry_mantle_bulk_values.txt
compositions/moon_far_dry_mantle_summary.txt
compositions/moon_near_pkt_mantle.json
compositions/moon_near_pkt_mantle_bulk_values.txt
compositions/moon_near_pkt_mantle_summary.txt
```

The human-readable bulk values are ordered as:

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

By default, the runner renders `build_inputs/lunar_stx21_template.build.in` for each configured model and feeds the rendered transcript to BUILD from the repo-local model work directory. If a model sets a custom `build_input_file`, that file is rendered instead. If no BUILD input is available, `<project>.dat` must already exist in that work directory.

BUILD input files may use these portable placeholders:

```text
${PERPLEX_DIR}
${PROJECT}
${COMPOSITION_FILE}
${OUTPUT_DIR}
${WORK_DIR}
${PERPLEX_BULK_VALUES}
${BUILD_TITLE}
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

## Plot Comparisons

After valid PlanetProfile tables exist, regenerate the comparison SVGs directly with:

```bash
python3 plot_comparisons.py
```

This writes `composition_oxides.svg` and `planetprofile_properties.svg` under `outputs/comparisons/` by default. The property plot compares pressure profiles averaged over the sampled temperature grid.

## Recreate PlanetProfile Table Format

PlanetProfile's existing Perple_X EOS tables use the native WERAMI-style header, for example:

```text
|6.6.6
example_1.tab
           2
T(K)
...
P(bar)
...
           9
T(K) P(bar) rho,kg/m3 vp,km/s ...
```

The pipeline now writes that format automatically as:

```text
outputs/<project>/<project>_planetprofile_native.tab
```

You can also convert any generated WERAMI table directly:

```bash
python3 planetprofile_tables.py convert \
  --input outputs/moon_far_dry_mantle/moon_far_dry_mantle_raw_werami.tab \
  --output outputs/moon_far_dry_mantle/moon_far_dry_mantle_planetprofile_native.tab \
  --source-name moon_far_dry_mantle_1.tab
```

## Export Existing Outputs

If the pipeline has already been run, export the validated native tables without rerunning Perple_X:

```bash
python3 export_planetprofile.py
```

or for a specific project and destination:

```bash
python3 export_planetprofile.py \
  --project moon_far_dry_mantle \
  --planetprofile-export-dir /path/to/PlanetProfile/PlanetProfile/Thermodynamics/EOStables/Perple_X
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
