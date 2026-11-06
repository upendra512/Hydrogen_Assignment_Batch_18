"""Run with:  python -m pytest tests/ -q

These are not decoration. They are the guard rail that stops a chemistry edit
silently breaking conservation. Keep them green.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gasifier import postprocess as pp
from gasifier import reactor_1d
from gasifier.config import load_case
from gasifier import devolatilization as devol


def test_case_loads():
    c = load_case()
    assert c.area > 0
    assert c.coal_feed > 0
    assert abs(sum(c.raw["inlets"]["primary"]["composition_mol_frac"].values()) - 1.0) < 1e-6


def test_partition_conserves_elements():
    """The volatile split must conserve C, H, O exactly at any char yield."""
    c = load_case()
    y = devol.daf_fractions(c)
    M = {"C": 0.012011, "H": 0.001008, "O": 0.015999, "N": 0.014007}
    for char_frac in (0.0, 0.25, 0.5, 0.75):
        dm = 1.0
        p = devol.partition(dm, char_frac * dm, y)
        g = p["gases"]
        placed = {
            "C": g["CO"] + g["CO2"] + g["CH4"] + p["soot_C_kg"] / M["C"] + char_frac * dm / M["C"],
            "H": 4 * g["CH4"] + 2 * g["H2"] + 2 * g["H2O"],
            "O": g["CO"] + 2 * g["CO2"] + g["H2O"],
            "N": 2 * g["N2"],
        }
        for el in ("C", "H", "O", "N"):
            avail = dm * y[el] / M[el]
            assert abs(placed[el] - avail) / avail < 1e-9, (el, placed[el], avail)


def test_tier1_runs_and_conserves():
    c = load_case()
    r = reactor_1d.solve(c, n_out=60)
    eb = pp.element_balance(r)
    for el, d in eb.items():
        assert abs(d["error_pct"]) < 1.0, f"{el} balance off by {d['error_pct']:.3f}%"


def test_tier1_is_physically_sane():
    c = load_case()
    r = reactor_1d.solve(c, n_out=120)
    assert r["T"].max() > 1500.0, "no ignition - check numerics.ignition_T_K"
    assert r["x"]["O2"][-1] < 0.01, "O2 not consumed - check the feed ratio"
    assert r["x"]["CO"][-1] > 0.10, "no CO produced"
    assert 0.0 <= pp.carbon_conversion(r) <= 1.0
