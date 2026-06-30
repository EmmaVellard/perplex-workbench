# Example Outputs

This directory contains a small tracked example-output set under `outputs/examples/` from smoke-test lunar runs:

- `examples/comparisons/composition_oxides.svg`
- `examples/comparisons/planetprofile_properties.svg`
- `examples/moon_far_highlands_surface_proxy/moon_far_highlands_surface_proxy_planetprofile.tab`
- `examples/moon_far_highlands_surface_proxy/oxide_omissions.txt`
- `examples/moon_near_maria_surface_proxy/moon_near_maria_surface_proxy_planetprofile.tab`
- `examples/moon_near_maria_surface_proxy/oxide_omissions.txt`

The Perple_X work files, raw WERAMI tables, and logs are intentionally not tracked here. They are larger, reproducible, and may contain machine-local paths from the Perple_X installation.

These examples demonstrate file shape and pipeline mechanics only. They should not be cited as final lunar mantle EOS tables.

Regenerate the full output tree with:

```bash
python3 run_full_pipeline.py
```
