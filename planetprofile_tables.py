from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from validate_tab import column_indices, read_tab


BASE_DIR = Path(__file__).resolve().parent

NATIVE_COLUMN_ORDER = (
    ("t_k", "T(K)"),
    ("p_bar", "P(bar)"),
    ("rho_kgm3", "rho,kg/m3"),
    ("vp_kms", "vp,km/s"),
    ("vs_kms", "vs,km/s"),
    ("cp_jm3k", "cp,J/K/m3"),
    ("alpha_pk", "alpha,1/K"),
    ("ks_bar", "Ks,bar"),
    ("gs_bar", "Gs,bar"),
)


def resolve_path(value: str | Path, base_dir: Path = BASE_DIR) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def format_header_number(value: float) -> str:
    return f"{value:.15g}"


def format_data_value(value: float) -> str:
    if math.isnan(value):
        return "NaN"
    if not math.isfinite(value):
        return str(value)
    if value == 0:
        return "0.00000"
    abs_value = abs(value)
    if abs_value >= 1.0e6 or abs_value < 1.0e-4:
        return f"{value:.6E}".replace("E+0", "E+").replace("E-0", "E-")
    return f"{value:.6g}"


def unique_sorted(values: list[float]) -> list[float]:
    return sorted(set(values))


def regular_step(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return (values[-1] - values[0]) / (len(values) - 1)


def source_name_for_table(source_tab: Path, source_name: str | None = None) -> str:
    return source_name or source_tab.name


def table_lookup(source_tab: Path) -> tuple[dict[tuple[float, float], list[float]], dict[str, int]]:
    tab = read_tab(source_tab)
    indices = column_indices(tab.headers)
    missing = [display for canonical, display in NATIVE_COLUMN_ORDER if canonical not in indices]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    lookup: dict[tuple[float, float], list[float]] = {}
    for row in tab.rows:
        key = (row[indices["t_k"]], row[indices["p_bar"]])
        lookup[key] = row
    return lookup, indices


def write_planetprofile_native_table(
    source_tab: Path,
    destination_tab: Path,
    *,
    source_name: str | None = None,
    first_axis: str = "T",
) -> None:
    lookup, indices = table_lookup(source_tab)
    temperatures = unique_sorted([key[0] for key in lookup])
    pressures = unique_sorted([key[1] for key in lookup])

    first_axis = first_axis.upper()
    if first_axis not in {"T", "P"}:
        raise ValueError("first_axis must be T or P")

    destination_tab.parent.mkdir(parents=True, exist_ok=True)
    with destination_tab.open("w", encoding="utf-8") as handle:
        handle.write("|6.6.6\n")
        handle.write(f"{source_name_for_table(source_tab, source_name):<100s}\n")
        handle.write(f"{2:12d}\n")

        axes = (
            (("T(K)", temperatures), ("P(bar)", pressures))
            if first_axis == "T"
            else (("P(bar)", pressures), ("T(K)", temperatures))
        )
        for label, values in axes:
            handle.write(f"{label:<8s}\n")
            handle.write(f"{format_header_number(values[0]):>24s}     \n")
            handle.write(f"{format_header_number(regular_step(values)):>24s}     \n")
            handle.write(f"{len(values):12d}\n")

        handle.write(f"{len(NATIVE_COLUMN_ORDER):12d}\n")
        handle.write("".join(f"{display:<15s}" for _, display in NATIVE_COLUMN_ORDER).rstrip() + "\n")

        if first_axis == "T":
            ordered_keys = [(temperature, pressure) for pressure in pressures for temperature in temperatures]
        else:
            ordered_keys = [(temperature, pressure) for temperature in temperatures for pressure in pressures]

        missing_points = [key for key in ordered_keys if key not in lookup]
        if missing_points:
            raise ValueError(
                f"Source table does not form a complete rectangular T-P grid; "
                f"missing {len(missing_points)} point(s)."
            )

        for key in ordered_keys:
            row = lookup[key]
            values = [row[indices[canonical]] for canonical, _ in NATIVE_COLUMN_ORDER]
            handle.write(" ".join(f"{format_data_value(value):>14s}" for value in values) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Perple_X tables to PlanetProfile native format."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert = subparsers.add_parser("convert", help="Write a PlanetProfile native-format table.")
    convert.add_argument("--input", required=True, help="Input WERAMI or PlanetProfile table.")
    convert.add_argument("--output", required=True, help="Output PlanetProfile native-format table.")
    convert.add_argument("--source-name", help="Source table name written in the second header line.")
    convert.add_argument("--first-axis", choices=("T", "P"), default="T", help="Fastest-varying output axis.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        source = resolve_path(args.input)
        destination = resolve_path(args.output)
        write_planetprofile_native_table(
            source,
            destination,
            source_name=args.source_name,
            first_axis=args.first_axis,
        )
        print(f"Wrote {destination}")
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
