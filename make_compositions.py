from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
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

PLACEHOLDER_WARNING = (
    "PLACEHOLDER ONLY: replace this composition with a published lunar mantle "
    "composition before scientific use."
)


@dataclass(frozen=True)
class LunarComposition:
    project: str
    description: str
    raw_wt_percent: dict[str, float]
    source_note: str = PLACEHOLDER_WARNING


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
        "placeholder": True,
        "source_note": model.source_note,
        "notes": [
            PLACEHOLDER_WARNING,
            "Use normalized values in Perple_X BUILD unless you intentionally want unnormalized amounts.",
            "Fe is represented as FeO for the silicate mantle.",
            "Do not include native Fe, Ni, or Cu in these mantle compositions.",
            "KREEP/Th/U/K radiogenic effects should mostly be represented in PlanetProfile thermal/radiogenic parameters.",
        ],
    }

    json_path = outdir / f"{model.project}.json"
    json_path.write_text(json.dumps(document, indent=2) + "\n")

    values_path = outdir / f"{model.project}_bulk_values.txt"
    with values_path.open("w", encoding="utf-8") as handle:
        for oxide in OXIDE_ORDER:
            handle.write(f"{normalized[oxide]:.8f}\n")

    summary_path = outdir / f"{model.project}_summary.txt"
    with summary_path.open("w", encoding="utf-8") as handle:
        handle.write(f"{model.project}\n")
        handle.write(f"{model.description}\n")
        handle.write(f"{PLACEHOLDER_WARNING}\n\n")
        handle.write("Normalized oxide composition, wt%:\n")
        for oxide in OXIDE_ORDER:
            handle.write(f"{oxide:8s} {normalized[oxide]:10.5f}\n")
        handle.write(f"\nTotal: {sum(normalized.values()):.5f}\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {values_path}")
    print(f"Wrote {summary_path}")


def placeholder_models() -> list[LunarComposition]:
    return [
        LunarComposition(
            project="moon_far_dry_mantle",
            description="Placeholder farside dry, depleted, KREEP-poor lunar mantle end-member",
            raw_wt_percent={
                "SiO2": 45.0,
                "TiO2": 0.20,
                "Al2O3": 3.50,
                "FeO": 12.50,
                "MgO": 36.0,
                "CaO": 2.00,
                "Na2O": 0.05,
                "K2O": 0.02,
                "P2O5": 0.03,
            },
        ),
        LunarComposition(
            project="moon_near_pkt_mantle",
            description="Placeholder nearside PKT/KREEP-influenced lunar mantle sensitivity end-member",
            raw_wt_percent={
                "SiO2": 45.0,
                "TiO2": 1.50,
                "Al2O3": 8.00,
                "FeO": 13.50,
                "MgO": 28.0,
                "CaO": 3.30,
                "Na2O": 0.20,
                "K2O": 0.30,
                "P2O5": 0.20,
            },
        ),
    ]


def main() -> None:
    for model in placeholder_models():
        write_composition(model)
    print("\nWARNING:", PLACEHOLDER_WARNING)


if __name__ == "__main__":
    main()
