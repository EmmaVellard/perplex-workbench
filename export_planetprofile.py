from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import run_perplex


DEFAULT_EXPORT_DIR = run_perplex.BASE_DIR / "outputs" / "planetprofile_export"


class ExportError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExportedTable:
    project: str
    source: Path
    destination: Path


def native_table_path(model: run_perplex.ModelConfig) -> Path:
    return model.output_dir / f"{model.project}_planetprofile_native.tab"


def export_filename(model: run_perplex.ModelConfig) -> str:
    return model.planetprofile_filename or f"{model.project}_planetprofile_native.tab"


def select_models(
    config: run_perplex.PipelineConfig,
    project: str | None = None,
) -> list[run_perplex.ModelConfig]:
    selected = [model for model in config.models if project is None or model.project == project]
    if project and not selected:
        raise ExportError(f"Project not found in config: {project}")
    return selected


def export_tables(
    models: list[run_perplex.ModelConfig],
    export_dir: Path,
) -> list[ExportedTable]:
    export_dir.mkdir(parents=True, exist_ok=True)
    exported: list[ExportedTable] = []

    for model in models:
        source = native_table_path(model)
        if not source.exists():
            raise ExportError(
                f"Missing native PlanetProfile table for {model.project}: {source}. "
                "Run run_full_pipeline.py first."
            )

        destination = export_dir / export_filename(model)
        shutil.copy2(source, destination)
        exported.append(ExportedTable(project=model.project, source=source, destination=destination))

    write_manifest(export_dir, exported)
    return exported


def write_manifest(export_dir: Path, exported: list[ExportedTable]) -> Path:
    manifest = {
        "description": "PlanetProfile-ready Perple_X EOS tables exported by perplex-workbench.",
        "tables": [
            {
                "project": table.project,
                "source": str(table.source),
                "destination": str(table.destination),
                "filename_for_planetprofile": table.destination.name,
            }
            for table in exported
        ],
    }
    manifest_path = export_dir / "planetprofile_export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export generated native Perple_X tables for use in PlanetProfile."
    )
    parser.add_argument("--config", default=str(run_perplex.DEFAULT_CONFIG), help="Path to configs/models.json.")
    parser.add_argument("--project", help="Export only one project from the config.")
    parser.add_argument(
        "--planetprofile-export-dir",
        default=str(DEFAULT_EXPORT_DIR),
        help="Directory where PlanetProfile-ready .tab files will be copied.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = run_perplex.resolve_path(args.config, run_perplex.BASE_DIR)

    try:
        config = run_perplex.load_config(config_path)
        base_dir = run_perplex.config_base_dir(config_path)
        export_dir = run_perplex.resolve_path(args.planetprofile_export_dir, base_dir)
        exported = export_tables(select_models(config, args.project), export_dir)
    except (FileNotFoundError, PermissionError, ExportError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for table in exported:
        print(f"Exported {table.project}: {table.destination}")
    print(f"Wrote {export_dir / 'planetprofile_export_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
