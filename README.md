# Perple_X Workbench

[![Tests](https://github.com/EmmaVellard/perplex-workbench/workflows/Tests/badge.svg)](https://github.com/EmmaVellard/perplex-workbench/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A GUI-first workflow for defining rock/planetary compositions, running Perple_X BUILD/VERTEX/WERAMI, validating outputs, and exporting PlanetProfile-ready EOS tables.

The included Moon near-side/far-side models are example smoke tests. They are useful for checking the workflow, not publication-ready lunar mantle compositions. For composition provenance and caveats, see [composition.md](composition.md).

## Installation

### Prerequisites
- Python 3.10 or later
- [Perple_X](https://github.com/jadconnolly/Perple_X) installed locally
- Docker (optional, for containerized usage)

### Quick Install

**Option 1: From PyPI (when published)**
```bash
pip install perplex-workbench
perplex-gui
```

**Option 2: From source**
```bash
git clone https://github.com/EmmaVellard/perplex-workbench.git
cd perplex-workbench
pip install -e .
perplex-gui
```

**Option 3: Development install**
```bash
git clone https://github.com/EmmaVellard/perplex-workbench.git
cd perplex-workbench
pip install -e ".[dev]"
pytest  # Run tests
perplex-gui
```

### First-Time Setup

1. **Copy example config**
   ```bash
   cp configs/models.example.json configs/models.json
   ```

2. **Install Perple_X**
   - Download from [jadconnolly/Perple_X](https://github.com/jadconnolly/Perple_X)
   - Note the installation path (contains BUILD, VERTEX, WERAMI executables)

3. **Launch the GUI**
   ```bash
   perplex-gui
   # Or: streamlit run perplex_workbench/gui/streamlit_app.py
   ```

4. **Configure Perple_X path**
   - In the GUI: Step 1 → enter your Perple_X directory path → Save
   - Or edit `configs/models.json` and set `"perplex_dir": "/path/to/perplex"`

The app opens in your browser at http://localhost:8501. Use `configs/models.json` as your local editable config; it is ignored by Git.

### Docker Installation (Alternative)

Run in an isolated container:

```bash
# Build image
docker build -t perplex-workbench .

# Run with GUI
docker run -p 8501:8501 \
  -v /path/to/perplex:/opt/perplex:ro \
  -v $(pwd)/outputs:/app/outputs \
  perplex-workbench

# Or use docker-compose
docker-compose up -d
```

See [DOCKER.md](DOCKER.md) for detailed Docker usage.

## GUI Workflow

The left menu has two main workspaces:

- `Build Composition`: create a new model, copy an existing model, edit oxide values and metadata, preview normalization, and delete saved models from `configs/models.json`.
- `Run Pipeline`: select a saved model, review caveats, generate composition files, run Perple_X, validate outputs, make comparison plots, and export PlanetProfile tables.

GitHub hosts this workbench only; it does not include BUILD, VERTEX, WERAMI, or Perple_X datafiles.

## What The GUI Writes

- Source model definitions: `configs/models.json`
- Generated composition files: `compositions/`
- Perple_X work/output files: `outputs/<project>/`
- PlanetProfile exports: `outputs/planetprofile_export/` or a directory you choose in the GUI

Do not edit generated files in `compositions/` or `outputs/` as the source of truth. Edit or copy models through the GUI instead.

## Thermodynamic Databases

### Available Databases

**stx21 (default)** - Stixrude & Lithgow-Bertelloni 2021
- Modeled oxides: Na2O, MgO, Al2O3, SiO2, CaO, FeO
- Best for: Silicate mantles, standard compositions
- Database file: `stx21ver.dat`

**hp633** - Holland & Powell 2011 (v6.33)
- Modeled oxides: Na2O, MgO, Al2O3, SiO2, K2O, CaO, TiO2, FeO
- Source-only oxide in the default profile: P2O5
- Best for: Compositions requiring TiO2 or K2O
- Database file: `hp633ver.dat`
- Solution model file: `solution_model.dat`

### Selecting a Database

**In config file:**
```json
{
  "database": "hp633",
  "perplex_dir": "/path/to/perplex"
}
```

**Via environment variable:**
```bash
export PERPLEX_DATABASE=hp633
perplex-gui
```

**Via CLI flag:**
```bash
perplex-run --database hp633
```

The GUI still lets you record `TiO2`, `K2O`, and `P2O5` because they are common source-composition fields. With the default stx21 profile, all three are source-only. With the default hp633 profile, TiO2 and K2O are passed to BUILD, while P2O5 remains source-only. Use a custom thermodynamic database, solution model file, and BUILD input before interpreting P-bearing effects.

## Command Line Interface

After installation, all functionality is available via command-line tools:

```bash
# Launch GUI
perplex-gui

# Run full pipeline
perplex-pipeline
perplex-pipeline --project moon_far_highlands_surface_proxy
perplex-pipeline --export-planetprofile

# Generate compositions only
perplex-make-compositions --config configs/models.json

# Run Perple_X (BUILD/VERTEX/WERAMI)
perplex-run --config configs/models.json --project my_project

# Export PlanetProfile tables
perplex-export --config configs/models.json --planetprofile-export-dir outputs/export

# Generate comparison plots
perplex-plot --config configs/models.json --output-dir outputs/plots
```

Legacy scripts at the repository root (`run_perplex.py`, `make_compositions.py`, etc.) still work for backward compatibility.

## Tests

Tests use fake Perple_X executables, so real Perple_X is not required:

```bash
pip install -e ".[dev]"
pytest
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this software in your research, please cite:

```bibtex
@software{perplex_workbench,
  author = {Vellard, Emma},
  title = {Perple_X Workbench: GUI workflow for planetary thermodynamics},
  year = {2024},
  url = {https://github.com/EmmaVellard/perplex-workbench}
}
```

## Acknowledgments

- [Perple_X](https://github.com/jadconnolly/Perple_X) by James Connolly
- [PlanetProfile](https://github.com/NASA-Planetary-Science/PlanetProfile) by NASA Planetary Science
- Lunar composition data from Wikipedia and published literature (see [composition.md](composition.md))
