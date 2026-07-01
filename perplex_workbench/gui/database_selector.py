"""Database selection widget and integration for Streamlit GUI."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from perplex_workbench.core.config_io import save_config_json
from perplex_workbench.core.database_utils import (
    describe_database,
    get_active_oxides,
    get_source_only_oxides,
    list_available_databases,
)


def show_database_selector(config: dict[str, Any], config_path: Path) -> str:
    """Render database selector and return selected database name.

    Args:
        config: Configuration dictionary
        config_path: Path to config file

    Returns:
        Selected database name (e.g., "stx21", "hp633")
    """
    current_db = config.get("database", "stx21")
    databases = list_available_databases()

    # Database selector
    selected = st.selectbox(
        "Thermodynamic Database",
        options=databases,
        index=databases.index(current_db) if current_db in databases else 0,
        key="database_selector",
        help="Choose which thermodynamic database to use for Perple_X calculations",
    )

    # Show database capabilities in expander
    with st.expander(f"📋 Database details: {selected}", expanded=False):
        st.code(describe_database(selected), language="text")

        active = sorted(get_active_oxides(selected))
        st.caption(f"**Modeled oxides ({len(active)})**: {', '.join(active)}")

        source_only = get_source_only_oxides(selected)
        if source_only:
            st.caption(f"**Source-only oxides**: {', '.join(source_only)}")
            st.info(
                "Source-only oxides are tracked in composition records but not "
                "passed to the BUILD file for this database."
            )

    # Switch database if changed
    if selected != current_db:
        if st.button(f"💾 Switch to {selected} database", type="primary"):
            config["database"] = selected
            save_config_json(config_path, config)
            st.success(f"✅ Database changed to {selected}. The new database will be used for all future calculations.")
            st.info("Existing models in your config remain unchanged. Their compositions may need adjustment if switching databases.")
            st.rerun()

    return selected


def get_current_database(config: dict[str, Any]) -> str:
    """Get current database from config with fallback to default.

    Args:
        config: Configuration dictionary

    Returns:
        Database name
    """
    return config.get("database", "stx21")


def database_selector_help_text() -> str:
    """Return help text explaining database selection.

    Returns:
        Help text string
    """
    return """
**Choosing a Database:**

- **stx21** (default): Standard for silicate mantle compositions
  - Modeled oxides: Na2O, MgO, Al2O3, SiO2, CaO, FeO (6 components)
  - Best for typical mantle mineralogy

- **hp633**: Extended database including Ti, K, P
  - Modeled oxides: All 9 major oxides including TiO2, K2O, P2O5
  - Use when these elements are significant in your composition

The database choice affects which oxides are included in Perple_X BUILD calculations.
"""
