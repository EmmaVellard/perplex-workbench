from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = BASE_DIR / "configs" / "models.json"
OUTDIR = BASE_DIR / "compositions"

# Keep this order fixed. Use the same order when answering BUILD prompts.
OXIDE_ORDER = [
    "SiO2",
    "TiO2",
    "Al2O3",
    "FeO",
    "MgO",
    "CaO",
    "Na2O",
    "K2O",
    "P2O5",
]

MODEL_STATUS = (
    "LITERATURE-BASED PROXY ONLY: these near/far compositions are first-pass "
    "terrane proxies for pipeline testing, not final lunar mantle models."
)


@dataclass(frozen=True)
class LunarComposition:
    project: str
    description: str
    raw_wt_percent: dict[str, float]
    source_note: str = MODEL_STATUS
    scientific_status: str = "literature_proxy"
    literature_proxy: bool = True


def ordered_composition(composition: dict[str, float]) -> dict[str, float]:
    unknown = sorted(set(composition) - set(OXIDE_ORDER))
    if unknown:
        raise ValueError(f"Unknown oxide(s): {', '.join(unknown)}")
    return {oxide: float(composition.get(oxide, 0.0)) for oxide in OXIDE_ORDER}


def normalize_wt_percent(composition: dict[str, float]) -> dict[str, float]:
    ordered = ordered_composition(composition)
    total = sum(ordered.values())
    if total <= 0:
        raise ValueError("Composition total must be positive.")
    return {oxide: value * 100.0 / total for oxide, value in ordered.items()}


def config_base_dir(config_path: Path) -> Path:
    if config_path.parent.name == "configs":
        return config_path.parent.parent
    return config_path.parent


def resolve_path(value: str | Path, base_dir: Path = BASE_DIR) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def write_composition(model: LunarComposition, outdir: Path = OUTDIR) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    raw = ordered_composition(model.raw_wt_percent)
    normalized = normalize_wt_percent(raw)

    document = {
        "project": model.project,
        "description": model.description,
        "units": "wt%",
        "oxide_order": OXIDE_ORDER,
        "composition_raw": raw,
        "composition_normalized": normalized,
        "scientific_status": model.scientific_status,
        "placeholder": False,
        "literature_proxy": model.literature_proxy,
        "source_note": model.source_note,
        "notes": [
            MODEL_STATUS,
            "Use normalized values in Perple_X BUILD unless you intentionally want unnormalized amounts.",
            "Fe is represented as FeO for the silicate mantle.",
            "Do not include native Fe, Ni, or Cu in these mantle compositions.",
            "KREEP/Th/U/K radiogenic effects should mostly be represented in PlanetProfile thermal/radiogenic parameters.",
            "The stx21ver.dat Perple_X database used by this pipeline supports NA2O, MGO, AL2O3, SIO2, CAO, and FEO; TiO2, K2O, and P2O5 are retained in the composition record but omitted from BUILD.",
        ],
    }

    json_path = outdir / f"{model.project}.json"
    json_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    values_path = outdir / f"{model.project}_bulk_values.txt"
    with values_path.open("w", encoding="utf-8") as handle:
        for oxide in OXIDE_ORDER:
            handle.write(f"{normalized[oxide]:.8f}\n")

    summary_path = outdir / f"{model.project}_summary.txt"
    with summary_path.open("w", encoding="utf-8") as handle:
        handle.write(f"{model.project}\n")
        handle.write(f"{model.description}\n")
        handle.write(f"{MODEL_STATUS}\n\n")
        handle.write("Normalized oxide composition, wt%:\n")
        for oxide in OXIDE_ORDER:
            handle.write(f"{oxide:8s} {normalized[oxide]:10.5f}\n")
        handle.write(f"\nTotal: {sum(normalized.values()):.5f}\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {values_path}")
    print(f"Wrote {summary_path}")


def model_from_config_entry(entry: dict) -> LunarComposition | None:
    composition = (
        entry.get("oxides_wt_percent")
        or entry.get("raw_wt_percent")
        or entry.get("composition_raw")
    )
    if composition is None:
        return None
    if not isinstance(composition, dict):
        raise ValueError(f"Composition for {entry.get('project', '<unknown>')} must be a JSON object.")

    project = entry.get("project")
    if not project:
        raise ValueError("Each inline composition model must define a project name.")
    return LunarComposition(
        project=project,
        description=entry.get("description", project),
        raw_wt_percent=composition,
        source_note=entry.get("source_note", MODEL_STATUS),
        scientific_status=entry.get("scientific_status", "user_defined"),
        literature_proxy=bool(entry.get("literature_proxy", False)),
    )


def models_from_config(config_path: Path, project: str | None = None) -> list[LunarComposition]:
    if not config_path.exists():
        raise FileNotFoundError(
            f"Missing config file: {config_path}. Copy configs/models.example.json to configs/models.json "
            "and set perplex_dir to your local Perple_X install."
        )
    data = json.loads(config_path.read_text(encoding="utf-8"))
    models: list[LunarComposition] = []
    for entry in data.get("models", []):
        if project and entry.get("project") != project:
            continue
        model = model_from_config_entry(entry)
        if model is not None:
            models.append(model)

    if project and not models:
        configured_projects = {entry.get("project") for entry in data.get("models", [])}
        if project in configured_projects:
            return []
        raise ValueError(f"Project not found in config: {project}")

    return models


def configured_or_default_models(config_path: Path, project: str | None = None) -> list[LunarComposition]:
    if config_path.exists():
        models = models_from_config(config_path, project=project)
        data = json.loads(config_path.read_text(encoding="utf-8"))
        if models or data.get("models"):
            return models
    if project:
        selected = [model for model in lunar_models() if model.project == project]
        if not selected:
            raise ValueError(f"Project not found: {project}")
        return selected
    return lunar_models()


def lunar_models() -> list[LunarComposition]:
    return [
        LunarComposition(
            project="moon_far_dry_mantle",
            description="Farside/highlands-like depleted lunar terrane proxy based on published average highlands surface oxides",
            raw_wt_percent={
                "SiO2": 45.5,
                "TiO2": 0.60,
                "Al2O3": 24.0,
                "FeO": 5.90,
                "MgO": 7.50,
                "CaO": 15.90,
                "Na2O": 0.60,
                "K2O": 0.00,
                "P2O5": 0.00,
            },
            source_note=(
                "Major oxides use a commonly tabulated lunar highlands average surface composition "
                "(SiO2 45.5, Al2O3 24.0, CaO 15.9, FeO 5.9, MgO 7.5, TiO2 0.6, Na2O 0.6 wt%). "
                "Used here as a farside/highlands proxy; not a directly sampled mantle composition."
            ),
        ),
        LunarComposition(
            project="moon_near_pkt_mantle",
            description="Nearside/maria-like enriched lunar terrane proxy based on published average maria surface oxides",
            raw_wt_percent={
                "SiO2": 45.4,
                "TiO2": 3.90,
                "Al2O3": 14.9,
                "FeO": 14.1,
                "MgO": 9.20,
                "CaO": 11.8,
                "Na2O": 0.60,
                "K2O": 0.00,
                "P2O5": 0.00,
            },
            source_note=(
                "Major oxides use a commonly tabulated lunar maria average surface composition "
                "(SiO2 45.4, Al2O3 14.9, CaO 11.8, FeO 14.1, MgO 9.2, TiO2 3.9, Na2O 0.6 wt%). "
                "Used here as a nearside/maria proxy; PKT/KREEP heat-producing elements should be treated separately."
            ),
        ),
    ]


def placeholder_models() -> list[LunarComposition]:
    return lunar_models()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate normalized composition files.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to models config.")
    parser.add_argument("--project", help="Generate only one project from the config.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config_path = resolve_path(args.config, BASE_DIR)
    models = configured_or_default_models(config_path, project=args.project)
    if not models:
        print("No inline compositions to generate; using configured composition files as-is.")
        return
    for model in models:
        outdir = resolve_path("compositions", config_base_dir(config_path))
        write_composition(model, outdir=outdir)
    print("\nWARNING:", MODEL_STATUS)


if __name__ == "__main__":
    main()
