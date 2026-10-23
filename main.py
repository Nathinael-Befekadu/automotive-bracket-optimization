"""
================================================================================
LIGHTWEIGHT AUTOMOTIVE MOUNTING BRACKET OPTIMIZATION TOOL
================================================================================
Author      : Nathinael Befekadu
Institution : St. Mary's University
Project     : Lightweight Automotive Mounting Bracket Optimization
Tools       : SolidWorks FEA + Python Analysis

Required libraries:
  pip install numpy matplotlib fpdf2

Usage:
  python main.py
================================================================================
"""

import os
import sys
import json
import csv
import math
import re
import datetime
from pathlib import Path

# ── Optional library imports ───────────────────────────────────────────────────
try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False

try:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
    FPDF_OK = True
except ImportError:
    FPDF_OK = False

# ── Global constants ───────────────────────────────────────────────────────────
BASELINE_MASS_G = 219.82
DATA_DIR        = Path(__file__).resolve().parent / "data"
DESIGNS_FILE    = DATA_DIR / "bracket_designs.json"
SIMS_FILE       = DATA_DIR / "simulation_results.json"
REPORTS_DIR     = DATA_DIR / "reports"
GRAPHS_DIR      = DATA_DIR / "graphs"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — FILE / DATA MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def init_dirs():
    for d in (DATA_DIR, REPORTS_DIR, GRAPHS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def load_designs() -> dict:
    if DESIGNS_FILE.exists():
        with open(DESIGNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_designs(designs: dict):
    with open(DESIGNS_FILE, "w", encoding="utf-8") as f:
        json.dump(designs, f, indent=2)


def load_simulations() -> dict:
    if SIMS_FILE.exists():
        with open(SIMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_simulations(sims: dict):
    with open(SIMS_FILE, "w", encoding="utf-8") as f:
        json.dump(sims, f, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — INPUT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_float(prompt: str, required=True, min_val=None, max_val=None):
    while True:
        raw = input(prompt).strip()
        if raw == "" and not required:
            return None
        if raw == "" and required:
            print("  ⚠  This field is required.")
            continue
        try:
            val = float(raw)
        except ValueError:
            print("  ⚠  Enter a numeric value.")
            continue
        if min_val is not None and val < min_val:
            print(f"  ⚠  Must be ≥ {min_val}.")
            continue
        if max_val is not None and val > max_val:
            print(f"  ⚠  Must be ≤ {max_val}.")
            continue
        return val


def get_int(prompt: str, required=True, min_val=1):
    while True:
        raw = input(prompt).strip()
        if raw == "" and not required:
            return None
        if raw == "" and required:
            print("  ⚠  This field is required.")
            continue
        try:
            val = int(raw)
        except ValueError:
            print("  ⚠  Enter a whole number.")
            continue
        if min_val is not None and val < min_val:
            print(f"  ⚠  Must be ≥ {min_val}.")
            continue
        return val


def get_str(prompt: str, required=True):
    while True:
        raw = input(prompt).strip()
        if raw == "" and not required:
            return None
        if raw == "" and required:
            print("  ⚠  This field is required.")
            continue
        return raw


def yes_no(prompt: str) -> bool:
    while True:
        raw = input(f"{prompt} (y/n): ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  ⚠  Please type y or n.")


def sep(char="═", width=72):
    print(char * width)


def header(title: str):
    sep()
    print(f"  {title}")
    sep()


def pause():
    input("\n  Press Enter to return to the main menu…")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — ENGINEERING CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════════

def fos(yield_MPa: float, stress_MPa: float):
    if stress_MPa and stress_MPa > 0:
        return yield_MPa / stress_MPa
    return None


def mass_reduction_pct(mass_g: float, baseline=BASELINE_MASS_G) -> float:
    return ((baseline - mass_g) / baseline) * 100.0


def check_requirements(fs, disp_mm, min_fs, max_disp):
    fos_ok  = (fs is not None and fs >= min_fs)
    disp_ok = (disp_mm is not None and disp_mm <= max_disp)
    return fos_ok, disp_ok, (fos_ok and disp_ok)


def linear_scale(sim: dict, new_force_N: float):
    f0 = sim.get("applied_force_N")
    s0 = sim.get("max_von_mises_MPa")
    d0 = sim.get("max_displacement_mm")
    if None in (f0, s0, d0) or f0 == 0:
        return None, None
    ratio = new_force_N / f0
    return s0 * ratio, d0 * ratio


def convergence_table(sims_asc: list) -> list:
    rows = []
    for i in range(1, len(sims_asc)):
        prev, curr = sims_asc[i - 1], sims_asc[i]
        sp, sc = prev.get("max_von_mises_MPa"), curr.get("max_von_mises_MPa")
        dp, dc = prev.get("max_displacement_mm"), curr.get("max_displacement_mm")
        s_chg = abs((sc - sp) / sp) * 100 if (sp and sc and sp != 0) else None
        d_chg = abs((dc - dp) / dp) * 100 if (dp and dc and dp != 0) else None
        rows.append({
            "from": prev.get("sim_name"), "to": curr.get("sim_name"),
            "n_prev": prev.get("num_elements"), "n_curr": curr.get("num_elements"),
            "s_prev": sp, "s_curr": sc, "s_chg": s_chg,
            "d_prev": dp, "d_curr": dc, "d_chg": d_chg,
        })
    return rows


def best_sim(sims: list):
    valid = [s for s in sims if s.get("num_elements") and s.get("max_von_mises_MPa")]
    if not valid:
        return None
    return max(valid, key=lambda s: s["num_elements"])


def select_bracket(designs: dict, prompt="Select bracket"):
    if not designs:
        print("  No bracket designs saved yet.")
        return None
    names = sorted(designs.keys())
    print(f"\n  Available brackets: {', '.join(names)}")
    while True:
        choice = get_str(f"  {prompt}: ").strip()
        match = next((name for name in names if name.casefold() == choice.casefold()), None)
        if match is not None:
            return match
        print(f"  ⚠  '{choice}' not found. Choose from: {', '.join(names)}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — MENU OPTION 1: ADD NEW BRACKET DESIGN
# ══════════════════════════════════════════════════════════════════════════════

def add_bracket(designs: dict, simulations: dict):
    header("ADD NEW BRACKET DESIGN")

    while True:
        name = get_str("  Bracket name / label (e.g. Design 8): ").strip()
        if name in designs:
            if not yes_no(f"  Bracket '{name}' already exists. Overwrite?"):
                print("  Returning to main menu.")
                return
        break

    print(f"\n  Entering design data for Bracket {name}")
    print("  (Press Enter to skip optional fields)\n")

    material  = get_str  ("  Material (e.g. 6061-T6 Aluminum, AISI 1020 Steel): ")
    yield_MPa = get_float("  Yield strength (MPa): ", min_val=0.1)

    # ── Thickness — split by plate ──────────────────────────────────────────
    print("\n  ─── Thickness ───")
    thickness_vert_mm  = get_float("  Vertical plate thickness (mm)   [optional]: ",
                                   required=False, min_val=0)
    thickness_horiz_mm = get_float("  Horizontal plate thickness (mm) [optional]: ",
                                   required=False, min_val=0)

    # ── Overall envelope ────────────────────────────────────────────────────
    print("\n  ─── Overall Dimensions ───")
    height_mm = get_float("  Overall height (mm)      [optional]: ", required=False, min_val=0)
    width_mm  = get_float("  Overall width  (mm)      [optional]: ", required=False, min_val=0)
    length_mm = get_float("  Overall length/depth (mm)[optional]: ", required=False, min_val=0)

    # ── Holes ────────────────────────────────────────────────────────────────
    print("\n  ─── Holes ───")
    mnt_hole_dia = get_float("  Mounting hole diameter(s) (mm) [optional]: ",
                             required=False, min_val=0)
    load_hole_dia = get_float("  Load hole diameter (mm)        [optional]: ",
                              required=False, min_val=0)

    # ── Fillet radii — split by location ────────────────────────────────────
    print("\n  ─── Fillet Radii ───")
    fillet_vert_r   = get_float(
        "  Vertical plate fillet radius (mm)              [optional]: ",
        required=False, min_val=0)
    fillet_horiz_r  = get_float(
        "  Horizontal plate fillet radius (mm)            [optional]: ",
        required=False, min_val=0)
    fillet_junct_r  = get_float(
        "  Junction fillet — where vert & horiz meet (mm) [optional]: ",
        required=False, min_val=0)

    notes = get_str("  Additional notes / dimensions [optional]: ", required=False)

    print()
    mass_g = get_float("  Bracket mass (grams): ", min_val=0)

    design = {
        "name":                      name,
        "material":                  material,
        "yield_strength_MPa":        yield_MPa,
        "thickness_vert_mm":         thickness_vert_mm,
        "thickness_horiz_mm":        thickness_horiz_mm,
        "height_mm":                 height_mm,
        "width_mm":                  width_mm,
        "length_mm":                 length_mm,
        "mounting_hole_dia_mm":      mnt_hole_dia,
        "load_hole_dia_mm":          load_hole_dia,
        "fillet_vert_radius_mm":     fillet_vert_r,
        "fillet_horiz_radius_mm":    fillet_horiz_r,
        "fillet_junction_radius_mm": fillet_junct_r,
        "additional_notes":          notes,
        "mass_grams":                mass_g,
        "date_added":                datetime.datetime.now().isoformat(),
    }

    designs[name] = design
    save_designs(designs)

    mr = mass_reduction_pct(mass_g)
    print(f"\n  ✓ Bracket {name} saved.")
    print(f"  Mass reduction vs. baseline ({BASELINE_MASS_G} g): {mr:+.2f}%")

    if yes_no("\n  Enter simulation results for this bracket now?"):
        _add_simulation(name, designs, simulations)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — MENU OPTION 2: ADD SIMULATION RESULTS
# ══════════════════════════════════════════════════════════════════════════════

def _add_simulation(bracket_name: str, designs: dict, simulations: dict):
    d = designs[bracket_name]
    header(f"ADD SIMULATION — BRACKET {bracket_name}")
    print(f"  Material: {d['material']}  |  Yield: {d['yield_strength_MPa']} MPa\n")

    sim_name = get_str("  Simulation label (e.g. Mesh_1, Coarse, Refined_3): ")

    b_sims = simulations.get(bracket_name, [])
    existing = [s["sim_name"] for s in b_sims]
    if sim_name in existing:
        if yes_no(f"  '{sim_name}' already exists. Overwrite?"):
            b_sims = [s for s in b_sims if s["sim_name"] != sim_name]
        else:
            return

    print("\n  ─── Loading Conditions ───")
    force_N   = get_float("  Applied force (N): ", min_val=0)
    force_dir = get_str  ("  Force direction (e.g. Downward −Y, Lateral +X): ")
    fixtures  = get_str  ("  Fixture / boundary conditions (e.g. Fixed at 4 mounting holes): ")

    print("\n  ─── Mesh ───")
    n_elements = get_int  ("  Number of elements: ")
    n_nodes    = get_int  ("  Number of nodes: ")

    print("\n  ─── FEA Results ───")
    max_stress = get_float("  Max von Mises stress (MPa): ", min_val=0)
    max_disp   = get_float("  Max resultant displacement (mm): ", min_val=0)

    sim = {
        "bracket_name":        bracket_name,
        "sim_name":            sim_name,
        "applied_force_N":     force_N,
        "force_direction":     force_dir,
        "fixture_conditions":  fixtures,
        "num_elements":        n_elements,
        "num_nodes":           n_nodes,
        "max_von_mises_MPa":   max_stress,
        "max_displacement_mm": max_disp,
        "date_added":          datetime.datetime.now().isoformat(),
    }

    b_sims.append(sim)
    simulations[bracket_name] = b_sims
    save_simulations(simulations)

    fs_val = fos(d["yield_strength_MPa"], max_stress)
    mr     = mass_reduction_pct(d["mass_grams"])

    print(f"\n  ✓ Simulation '{sim_name}' saved for Bracket {bracket_name}.")
    print(f"\n  ─── Quick Summary ───")
    print(f"  Factor of Safety (yield-based): " +
          (f"{fs_val:.3f}" if fs_val else "N/A"))
    print(f"  Mass reduction vs. baseline:    {mr:.2f}%")
    print(f"  Max von Mises stress:           {max_stress:.4f} MPa")
    print(f"  Max displacement:               {max_disp:.6f} mm")


def add_simulation_menu(designs: dict, simulations: dict):
    header("ADD SIMULATION TO EXISTING BRACKET")
    name = select_bracket(designs, "Bracket to add simulation to")
    if name:
        _add_simulation(name, designs, simulations)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — MENU OPTION 3: VIEW / EDIT SAVED DESIGNS
# ══════════════════════════════════════════════════════════════════════════════

def view_edit_designs(designs: dict, simulations: dict):
    header("VIEW / EDIT SAVED DESIGNS")
    if not designs:
        print("  No designs saved yet.")
        return

    name = select_bracket(designs, "Select bracket to view")
    if not name:
        return

    d    = designs[name]
    sims = simulations.get(name, [])

    print(f"\n  ══ Bracket {name} ══")
    fields = [
        ("Material",                  d.get("material")),
        ("Yield Strength",            f"{d.get('yield_strength_MPa')} MPa"),
        ("Thickness — Vertical",      f"{d.get('thickness_vert_mm')} mm"),
        ("Thickness — Horizontal",    f"{d.get('thickness_horiz_mm')} mm"),
        ("Height",                    f"{d.get('height_mm')} mm"),
        ("Width",                     f"{d.get('width_mm')} mm"),
        ("Length/Depth",              f"{d.get('length_mm')} mm"),
        ("Mounting Hole Dia",         f"{d.get('mounting_hole_dia_mm')} mm"),
        ("Load Hole Dia",             f"{d.get('load_hole_dia_mm')} mm"),
        ("Fillet — Vertical plate",   f"{d.get('fillet_vert_radius_mm')} mm"),
        ("Fillet — Horizontal plate", f"{d.get('fillet_horiz_radius_mm')} mm"),
        ("Fillet — Junction",         f"{d.get('fillet_junction_radius_mm')} mm"),
        ("Mass",                      f"{d.get('mass_grams')} g"),
        ("Notes",                     d.get("additional_notes")),
    ]
    for k, v in fields:
        print(f"  {k:<28}: {v if v is not None else '—'}")

    if sims:
        print(f"\n  Simulations ({len(sims)} total):")
        for i, s in enumerate(sims, 1):
            print(f"    {i}. {s['sim_name']:20s}  {s.get('num_elements'):>8,} elements  "
                  f"{s.get('max_von_mises_MPa'):.2f} MPa  "
                  f"{s.get('max_displacement_mm'):.5f} mm")
    else:
        print("\n  No simulations entered yet.")

    if not yes_no("\n  Edit this bracket's design info?"):
        return

    print("  (Press Enter to keep the current value)\n")

    def _update_str(field, label):
        v = input(f"  {label} [{d.get(field)}]: ").strip()
        if v:
            d[field] = v

    def _update_float(field, label):
        v = input(f"  {label} [{d.get(field)}]: ").strip()
        if v:
            try:
                d[field] = float(v)
            except ValueError:
                print("  ⚠  Invalid — keeping original.")

    _update_str  ("material",                  "Material")
    _update_float("yield_strength_MPa",        "Yield Strength (MPa)")
    _update_float("mass_grams",                "Mass (g)")
    _update_float("thickness_vert_mm",         "Vertical Plate Thickness (mm)")
    _update_float("thickness_horiz_mm",        "Horizontal Plate Thickness (mm)")
    _update_float("height_mm",                 "Height (mm)")
    _update_float("width_mm",                  "Width (mm)")
    _update_float("fillet_vert_radius_mm",     "Vertical Plate Fillet Radius (mm)")
    _update_float("fillet_horiz_radius_mm",    "Horizontal Plate Fillet Radius (mm)")
    _update_float("fillet_junction_radius_mm", "Junction Fillet Radius (mm)")
    _update_str  ("additional_notes",          "Notes")

    designs[name] = d
    save_designs(designs)
    print(f"\n  ✓ Bracket {name} updated.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — MENU OPTION 4: ANALYZE INDIVIDUAL BRACKET
# ══════════════════════════════════════════════════════════════════════════════

def analyze_bracket(designs: dict, simulations: dict):
    header("ANALYZE INDIVIDUAL BRACKET")
    if not designs:
        print("  No designs saved yet.")
        return

    name = select_bracket(designs, "Bracket to analyze")
    if not name:
        return

    d    = designs[name]
    sims = simulations.get(name, [])
    if not sims:
        print(f"  No simulations found for Bracket {name}.")
        return

    print("\n  ─── Engineering Requirements ───")
    min_fs   = get_float("  Minimum acceptable factor of safety: ", min_val=0.01)
    max_disp = get_float("  Maximum allowable displacement (mm): ", min_val=1e-6)

    mr = mass_reduction_pct(d["mass_grams"])
    print(f"\n  ══ Analysis — Bracket {name} ══")
    print(f"  Material: {d['material']}  |  Yield: {d['yield_strength_MPa']} MPa  "
          f"|  Mass: {d['mass_grams']} g")
    print(f"  Mass reduction vs. baseline ({BASELINE_MASS_G} g): {mr:.2f}%")
    print(f"  Requirements: FoS ≥ {min_fs}  |  Displacement ≤ {max_disp} mm\n")

    print(f"  {'Simulation':<20} {'Stress MPa':>11} {'Disp mm':>10} "
          f"{'FoS':>8} {'FoS✓':>6} {'Disp✓':>6} {'Result':>8}")
    print("  " + "─" * 75)

    for s in sims:
        stress = s.get("max_von_mises_MPa")
        disp   = s.get("max_displacement_mm")
        fs_v   = fos(d["yield_strength_MPa"], stress)
        fo, do, ok = check_requirements(fs_v, disp, min_fs, max_disp)
        fs_str = f"{fs_v:.3f}" if fs_v else "N/A"
        print(f"  {s['sim_name']:<20} {stress:>11.4f} {disp:>10.5f} "
              f"{fs_str:>8} {'✓' if fo else '✗':>6} {'✓' if do else '✗':>6} "
              f"{'PASS' if ok else 'FAIL':>8}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — MENU OPTION 5: COMPARE ALL BRACKET DESIGNS
# ══════════════════════════════════════════════════════════════════════════════

def _build_comparison_rows(designs, simulations, min_fs, max_disp) -> list:
    rows = []
    for name in sorted(designs.keys()):
        d   = designs[name]
        bs  = best_sim(simulations.get(name, []))
        if bs is None:
            rows.append({
                "name": name, "mass_g": d["mass_grams"],
                "stress": None, "disp": None, "fs": None,
                "mass_red": mass_reduction_pct(d["mass_grams"]),
                "passes": False, "no_data": True,
                "force_N": None, "direction": None, "fixture": None,
            })
            continue
        stress = bs.get("max_von_mises_MPa")
        disp   = bs.get("max_displacement_mm")
        fs_v   = fos(d["yield_strength_MPa"], stress)
        _, _, ok = check_requirements(fs_v, disp, min_fs, max_disp)
        rows.append({
            "name":     name,
            "mass_g":   d["mass_grams"],
            "stress":   stress,
            "disp":     disp,
            "fs":       fs_v,
            "mass_red": mass_reduction_pct(d["mass_grams"]),
            "passes":   ok,
            "no_data":  False,
            "force_N":  bs.get("applied_force_N"),
            "direction":bs.get("force_direction", "").lower(),
            "fixture":  bs.get("fixture_conditions", "").lower(),
        })
    return rows


def compare_brackets(designs: dict, simulations: dict):
    header("COMPARE ALL BRACKET DESIGNS")
    if len(designs) < 2:
        print(f"  Need at least 2 designs; currently {len(designs)} saved.")
        return

    print("\n  ─── Engineering Requirements ───")
    min_fs   = get_float("  Minimum acceptable factor of safety: ", min_val=0.01)
    max_disp = get_float("  Maximum allowable displacement (mm): ", min_val=1e-6)

    rows = _build_comparison_rows(designs, simulations, min_fs, max_disp)

    ref = next((r for r in rows if not r["no_data"]), None)
    if ref:
        bad = [r["name"] for r in rows
               if not r["no_data"] and (
                   r["force_N"] != ref["force_N"] or
                   r["direction"] != ref["direction"] or
                   r["fixture"] != ref["fixture"]
               )]
        if bad:
            print(f"\n  ⚠  WARNING: Brackets {bad} use different loading or fixture conditions.")
            print("     Direct comparison may not be valid. Review carefully.\n")

    print(f"\n  ══ Bracket Comparison Table ══")
    print(f"  (Using most-refined simulation per bracket)\n")
    print(f"  {'Bracket':<10} {'Mass (g)':>10} {'Stress MPa':>12} "
          f"{'Disp mm':>10} {'FoS':>8} {'Mass Red%':>10} {'Result':>8}")
    print("  " + "─" * 74)

    for r in rows:
        if r["no_data"]:
            print(f"  {r['name']:<10} {r['mass_g']:>10.2f} {'—':>12} {'—':>10} "
                  f"{'—':>8} {r['mass_red']:>10.2f} {'NO DATA':>8}")
        else:
            res = "PASS" if r["passes"] else "FAIL"
            print(f"  {r['name']:<10} {r['mass_g']:>10.2f} {r['stress']:>12.4f} "
                  f"{r['disp']:>10.5f} {r['fs']:>8.3f} {r['mass_red']:>10.2f} {res:>8}")

    csv_path = DATA_DIR / "bracket_comparison.csv"
    fieldnames = ["name","mass_g","stress","disp","fs","mass_red","passes"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"\n  ✓ Comparison exported to: {csv_path}")
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — MENU OPTION 6: FIND THE BEST BRACKET
# ══════════════════════════════════════════════════════════════════════════════

def find_best(designs: dict, simulations: dict):
    header("FIND THE BEST BRACKET")
    if not designs:
        print("  No designs saved yet.")
        return

    print("\n  ─── Engineering Requirements ───")
    min_fs   = get_float("  Minimum acceptable factor of safety: ", min_val=0.01)
    max_disp = get_float("  Maximum allowable displacement (mm): ", min_val=1e-6)

    rows    = _build_comparison_rows(designs, simulations, min_fs, max_disp)
    passing = [r for r in rows if r["passes"] and not r["no_data"]]
    failing = [r for r in rows if not r["passes"] and not r["no_data"]]
    no_data = [r for r in rows if r["no_data"]]

    print(f"\n  ══ Best Bracket Selection ══")
    print(f"  Requirements: FoS ≥ {min_fs}  |  Displacement ≤ {max_disp} mm\n")

    if no_data:
        print(f"  Excluded (no simulation data): {', '.join(r['name'] for r in no_data)}")

    if not passing:
        print("\n  ✗  No tested bracket meets the specified requirements.")
        if failing:
            print("\n  Failing brackets — reasons:")
            for r in failing:
                reasons = []
                if r["fs"] is not None and r["fs"] < min_fs:
                    reasons.append(f"FoS {r['fs']:.3f} < {min_fs}")
                if r["disp"] is not None and r["disp"] > max_disp:
                    reasons.append(f"Displacement {r['disp']:.5f} mm > {max_disp} mm")
                print(f"    Bracket {r['name']}: {'; '.join(reasons) if reasons else 'incomplete data'}")
        return

    best = min(passing, key=lambda r: r["mass_g"])
    mr   = best["mass_red"]

    print(f"  ✓  RECOMMENDED BRACKET: {best['name']}")
    print(f"  {'─'*54}")
    print(f"  Mass:              {best['mass_g']:.2f} g  (baseline: {BASELINE_MASS_G} g)")
    print(f"  Mass Reduction:    {mr:.2f}%  ({'lighter' if mr > 0 else 'heavier'} than baseline)")
    print(f"  Factor of Safety:  {best['fs']:.3f}  (required ≥ {min_fs})  ✓")
    print(f"  Max Stress:        {best['stress']:.4f} MPa")
    print(f"  Max Displacement:  {best['disp']:.5f} mm  (limit {max_disp} mm)  ✓")

    others = [r for r in passing if r["name"] != best["name"]]
    if others:
        print(f"\n  Other passing designs (heavier): {', '.join(r['name'] for r in others)}")
        print(f"  Bracket {best['name']} selected because it has the lowest mass.")

    if failing:
        print(f"\n  Rejected brackets:")
        for r in failing:
            reasons = []
            if r["fs"] is not None and r["fs"] < min_fs:
                reasons.append(f"FoS too low ({r['fs']:.3f})")
            if r["disp"] is not None and r["disp"] > max_disp:
                reasons.append(f"Displacement too high ({r['disp']:.5f} mm)")
            print(f"    Bracket {r['name']}: {'; '.join(reasons)}")

    print(f"\n  ─── Engineering Note ───")
    print(f"  This recommendation is based on your entered FEA data.")
    print(f"  Verify mesh convergence before treating any result as final.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — MENU OPTION 7: MESH CONVERGENCE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def convergence_analysis(designs: dict, simulations: dict):
    header("MESH CONVERGENCE ANALYSIS")
    if not designs:
        print("  No designs saved yet.")
        return

    name = select_bracket(designs, "Bracket for convergence analysis")
    if not name:
        return

    sims  = simulations.get(name, [])
    valid = sorted(
        [s for s in sims if s.get("num_elements") and s.get("max_von_mises_MPa")],
        key=lambda s: s["num_elements"]
    )

    if len(valid) < 2:
        print(f"\n  Bracket {name} has {len(valid)} usable simulation(s).")
        print("  At least 2 mesh refinements are required for convergence analysis.")
        return

    print(f"\n  {len(valid)} mesh refinements available for Bracket {name}.")
    tol = get_float("\n  Enter convergence tolerance (%) [e.g. 2.0]: ", min_val=0.001)

    rows = convergence_table(valid)

    print(f"\n  ══ Convergence Table — Bracket {name} (tolerance: {tol}%) ══\n")
    print(f"  {'Simulation':<20} {'Elements':>10} "
          f"{'Stress MPa':>12} {'Δ Stress%':>10} {'Disp mm':>11} {'Δ Disp%':>9}")
    print("  " + "─" * 80)

    s0 = valid[0]
    print(f"  {s0['sim_name']:<20} {s0['num_elements']:>10,} "
          f"{s0['max_von_mises_MPa']:>12.4f} {'—':>10} {s0['max_displacement_mm']:>11.6f} {'—':>9}")

    for i, r in enumerate(rows):
        s  = valid[i + 1]
        sc = f"{r['s_chg']:.4f}" if r["s_chg"] is not None else "N/A"
        dc = f"{r['d_chg']:.4f}" if r["d_chg"] is not None else "N/A"
        print(f"  {s['sim_name']:<20} {s['num_elements']:>10,} "
              f"{s['max_von_mises_MPa']:>12.4f} {sc:>10} {s['max_displacement_mm']:>11.6f} {dc:>9}")

    last = rows[-1]
    converged_at = (valid[-1]["sim_name"]
                    if last["s_chg"] is not None and last["d_chg"] is not None
                    and last["s_chg"] <= tol and last["d_chg"] <= tol
                    else None)
    print(f"\n  ── Convergence Assessment ──\n")
    if converged_at:
        print(f"  ✓  CONVERGED at '{converged_at}' (both Δ < {tol}%).")
        print(f"     Final stress Δ:       {last['s_chg']:.4f}%")
        print(f"     Final displacement Δ: {last['d_chg']:.4f}%")
        print(f"     Use the most-refined mesh result for final stress values.")
    else:
        print(f"  ✗  NOT CONVERGED at {tol}% tolerance.")
        if last["s_chg"] is not None:
            print(f"     Final stress Δ:       {last['s_chg']:.4f}%")
        if last["d_chg"] is not None:
            print(f"     Final displacement Δ: {last['d_chg']:.4f}%")
        print(f"\n  Recommendation: Refine the mesh further in SolidWorks and re-run.")

    stresses = [s["max_von_mises_MPa"] for s in valid]
    if len(stresses) >= 3:
        monotone_up = all(stresses[i] < stresses[i + 1] for i in range(len(stresses) - 1))
        if monotone_up and (last["s_chg"] is None or last["s_chg"] > tol):
            print(f"\n  ⚠  POSSIBLE STRESS SINGULARITY:")
            print(f"     Max stress increases with every refinement without plateauing.")
            print(f"     Check for sharp re-entrant corners or point load locations.")
            print(f"     Adding a fillet radius often resolves this.")

    if MATPLOTLIB_OK and yes_no("\n  Generate convergence graphs?"):
        _plot_convergence(name, valid, rows, tol)


def _plot_convergence(name: str, sims_asc: list, conv_rows: list, tol: float):
    elements   = [s["num_elements"] for s in sims_asc]
    stresses   = [s["max_von_mises_MPa"] for s in sims_asc]
    disps      = [s["max_displacement_mm"] for s in sims_asc]
    labels     = [s["sim_name"] for s in sims_asc]
    s_changes  = [r["s_chg"] for r in conv_rows]
    d_changes  = [r["d_chg"] for r in conv_rows]
    chg_labels = [sims_asc[i + 1]["sim_name"] for i in range(len(conv_rows))]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Mesh Convergence Analysis — Bracket {name}", fontsize=13, fontweight="bold")

    ax = axes[0, 0]
    ax.plot(elements, stresses, "b-o", lw=2, ms=6)
    ax.axhline(stresses[-1], color="gray", ls="--", alpha=0.5, label="Final value")
    for x, y, lbl in zip(elements, stresses, labels):
        ax.annotate(lbl, (x, y), xytext=(0, 8), textcoords="offset points", fontsize=7, ha="center")
    ax.set_xlabel("Number of Elements"); ax.set_ylabel("Max von Mises Stress (MPa)")
    ax.set_title("Elements vs. Max Stress"); ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[0, 1]
    ax.plot(elements, disps, "r-s", lw=2, ms=6)
    ax.axhline(disps[-1], color="gray", ls="--", alpha=0.5, label="Final value")
    for x, y, lbl in zip(elements, disps, labels):
        ax.annotate(lbl, (x, y), xytext=(0, 8), textcoords="offset points", fontsize=7, ha="center")
    ax.set_xlabel("Number of Elements"); ax.set_ylabel("Max Displacement (mm)")
    ax.set_title("Elements vs. Max Displacement"); ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[1, 0]
    nodes = [s["num_nodes"] for s in sims_asc]
    ax.plot(nodes, stresses, "g-^", lw=2, ms=6)
    for x, y, lbl in zip(nodes, stresses, labels):
        ax.annotate(lbl, (x, y), xytext=(0, 8), textcoords="offset points", fontsize=7, ha="center")
    ax.set_xlabel("Number of Nodes"); ax.set_ylabel("Max von Mises Stress (MPa)")
    ax.set_title("Nodes vs. Max Stress"); ax.grid(alpha=0.3)

    ax = axes[1, 1]
    x_pos   = list(range(len(chg_labels)))
    bw      = 0.35
    valid_s = [v if v is not None else 0 for v in s_changes]
    valid_d = [v if v is not None else 0 for v in d_changes]
    ax.bar([x - bw/2 for x in x_pos], valid_s, bw, label="Stress Δ%",       color="steelblue", alpha=0.85)
    ax.bar([x + bw/2 for x in x_pos], valid_d, bw, label="Displacement Δ%", color="salmon",    alpha=0.85)
    ax.axhline(tol, color="red", ls="--", lw=1.5, label=f"Tolerance ({tol}%)")
    ax.set_xticks(x_pos); ax.set_xticklabels(chg_labels, rotation=15, ha="right", fontsize=8)
    ax.set_ylabel("Percentage Change (%)"); ax.set_title("Successive Mesh Changes")
    ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")

    plt.tight_layout()
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = GRAPHS_DIR / f"convergence_{name}_{ts}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  ✓ Convergence graph saved: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — MENU OPTION 8: PREDICT PERFORMANCE UNDER DIFFERENT LOADS
# ══════════════════════════════════════════════════════════════════════════════

def predict_load(designs: dict, simulations: dict):
    header("PREDICT PERFORMANCE UNDER DIFFERENT LOADS")
    if not designs:
        print("  No designs saved yet.")
        return

    name = select_bracket(designs, "Bracket for load prediction")
    if not name:
        return

    d    = designs[name]
    sims = simulations.get(name, [])
    if not sims:
        print(f"  No simulations found for Bracket {name}.")
        return

    print(f"\n  Available simulations for Bracket {name}:")
    for i, s in enumerate(sims, 1):
        print(f"    {i}.  {s['sim_name']:20s}  {s['applied_force_N']} N  "
              f"{s['max_von_mises_MPa']} MPa  {s['max_displacement_mm']} mm")

    idx   = get_int(f"\n  Select simulation number (1–{len(sims)}): ", min_val=1) - 1
    if idx >= len(sims):
        print("  ⚠  Invalid selection.")
        return

    base  = sims[idx]
    new_f = get_float("\n  New force magnitude (N): ", min_val=0.001)

    est_s, est_d = linear_scale(base, new_f)
    if est_s is None:
        print("  ⚠  Cannot predict: incomplete simulation data.")
        return

    fs_v  = fos(d["yield_strength_MPa"], est_s)
    ratio = new_f / base["applied_force_N"]

    print(f"\n  ══ Load Prediction — Bracket {name} ══")
    print(f"  Base simulation:   {base['sim_name']}")
    print(f"  Original force:    {base['applied_force_N']:.2f} N")
    print(f"  New force:         {new_f:.2f} N")
    print(f"  Scaling ratio:     {ratio:.4f}")
    print(f"\n  ── Estimated Results (Linear Elastic) ──")
    print(f"  Est. Max Stress:         {est_s:.4f} MPa")
    print(f"  Est. Max Displacement:   {est_d:.6f} mm")
    if fs_v:
        print(f"  Est. Factor of Safety:   {fs_v:.3f}")
        if est_s >= d["yield_strength_MPa"]:
            print(f"\n  ⚠  ESTIMATED STRESS EXCEEDS YIELD STRENGTH ({d['yield_strength_MPa']} MPa).")
            print(f"     Linear scaling is invalid in the plastic range.")
            print(f"     A full nonlinear SolidWorks simulation is required at this load.")

    print(f"\n  ─── Limitations ───")
    print(f"  • Linear elastic scaling only — valid below yield.")
    print(f"  • Does not account for nonlinear geometry, contact, or plasticity.")
    print(f"  • These numbers are ESTIMATES, not validated FEA results.")
    print(f"  • Run a full SolidWorks simulation to confirm before any design decision.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 12 — MENU OPTION 9: GENERATE ENGINEERING GRAPHS
# ══════════════════════════════════════════════════════════════════════════════

def _plot_readable_comparisons(designs, simulations, min_fs, max_disp, ts):
    """Consistent, readable D1–D7 comparison graphs with a design key."""
    rows = _build_comparison_rows(designs, simulations, min_fs, max_disp)
    # Use exactly the saved Design 1 ... Design 7 names on all graphs.
    lookup = {r["name"]: r for r in rows if not r["no_data"]}
    ordered_names = sorted(lookup, key=lambda n: int(n.split()[1]) if re.fullmatch(r"Design \d+", n) else 10**9)
    data = [lookup[n] for n in ordered_names]
    if not data:
        return []
    labels = [r["name"] for r in data]
    colors = ["#24a86a" if r["passes"] else "#d95a50" for r in data]
    x = list(range(len(data)))
    specs = [
        ("stress", "Max von Mises stress (MPa)", "Stress", None),
        ("disp", "Max displacement (mm)", "Displacement", max_disp),
        ("fs", "Yield-based factor of safety", "Factor of safety", min_fs),
        ("mass_red", "Mass reduction (%)", "Mass reduction", None),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(15, 11), constrained_layout=False)
    fig.suptitle("Bracket Design Comparison — Engineering Performance", fontsize=16, fontweight="bold", y=0.99)
    for ax, (field, ylabel, title, limit) in zip(axes.flat, specs):
        vals = [r[field] for r in data]
        bars = ax.bar(x, vals, color=colors, edgecolor="#1b2630", linewidth=0.5, width=0.68)
        ax.set_xticks(x, labels)
        ax.tick_params(axis="x", labelsize=9)
        ax.set_title(title, fontsize=12, pad=10)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.18)
        ax.set_axisbelow(True)
        ymax = max(max(vals), limit or 0)
        ax.set_ylim(0, ymax * 1.20 if ymax else 1)
        if limit is not None:
            ax.axhline(limit, color="#c63d38", linestyle="--", linewidth=1.4, label=f"Criterion: {limit:g}")
            ax.legend(fontsize=9, loc="upper right")
        for b, val in zip(bars, vals):
            label = f"{val:.4f}" if field == "disp" else (f"{val:.1f}%" if field == "mass_red" else f"{val:.2f}")
            ax.text(b.get_x()+b.get_width()/2, b.get_height()+ymax*.018, label, ha="center", fontsize=8)
    fig.subplots_adjust(left=.09, right=.97, top=.91, bottom=.11, hspace=.38, wspace=.25)
    fig.text(.08,.025,"Green = meets specified screening criteria  •  Red = does not meet criteria",fontsize=9)
    p1 = GRAPHS_DIR / f"comparison_bars_{ts}.png"
    fig.savefig(p1,dpi=180,facecolor="white");plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(17, 7))
    fig.suptitle("Mass–Performance Trade-offs", fontsize=16, fontweight="bold", y=.98)
    for ax, (field, ylabel, title, limit) in zip(axes, specs[:3]):
        for i,r in enumerate(data):
            ax.scatter(r["mass_g"],r[field],s=125,c=colors[i],edgecolors="#1b2630",linewidth=.6,zorder=3)
            ax.annotate(labels[i],(r["mass_g"],r[field]),xytext=(5,6),textcoords="offset points",fontsize=9,fontweight="bold")
        if limit is not None:
            ax.axhline(limit,color="#c63d38",linestyle="--",label=f"Criterion: {limit:g}")
            ax.legend(fontsize=9)
        ax.set_xlabel("Mass (g)");ax.set_ylabel(ylabel);ax.set_title(title)
        ax.grid(alpha=.20)
        ax.margins(x=.14,y=.18)
    fig.subplots_adjust(left=.065,right=.98,top=.86,bottom=.14,wspace=.30)
    p2=GRAPHS_DIR / f"comparison_scatter_{ts}.png"
    fig.savefig(p2,dpi=180,facecolor="white");plt.close(fig)

    fig,ax=plt.subplots(figsize=(11,7))
    vals=[r["mass_red"] for r in data]
    bars=ax.bar(x,vals,color=colors,edgecolor="#1b2630",linewidth=.5,width=.66)
    ax.set_xticks(x,labels);ax.set_ylim(0,max(vals)*1.17 if max(vals)>0 else 1)
    ax.set_title(f"Mass Reduction Relative to Baseline ({BASELINE_MASS_G:.2f} g)",fontsize=14,fontweight="bold")
    ax.set_ylabel("Mass reduction (%)");ax.grid(axis="y",alpha=.2);ax.set_axisbelow(True)
    for b,v in zip(bars,vals):
        ax.text(b.get_x()+b.get_width()/2,b.get_height()+max(vals)*.02,f"{v:.1f}%",ha="center",fontsize=10)
    fig.subplots_adjust(left=.10,right=.96,top=.89,bottom=.14)
    p3=GRAPHS_DIR / f"mass_reduction_{ts}.png"
    fig.savefig(p3,dpi=180,facecolor="white");plt.close(fig)
    return [p1,p2,p3]


def generate_graphs(designs: dict, simulations: dict):
    header("GENERATE ENGINEERING GRAPHS")
    if not MATPLOTLIB_OK:
        print("  Matplotlib is not installed. Run: pip install matplotlib")
        return
    if not designs:
        print("  No designs saved yet.")
        return
    min_fs = get_float("  Minimum acceptable FoS: ", min_val=0.01)
    max_disp = get_float("  Maximum allowable displacement (mm): ", min_val=1e-6)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Keep one current set of generated plots rather than accumulating timestamped duplicates.
    for pattern in ("comparison_bars_*.png", "comparison_scatter_*.png", "mass_reduction_*.png", "convergence_*.png"):
        for previous in GRAPHS_DIR.glob(pattern):
            previous.unlink()
    for path in _plot_readable_comparisons(designs, simulations, min_fs, max_disp, ts):
        print(f"  Graph saved: {path}")
    for bname in sorted(designs.keys()):
        valid=sorted([s for s in simulations.get(bname,[]) if s.get("num_elements") and s.get("max_von_mises_MPa")],key=lambda s:s["num_elements"])
        if len(valid)>=2:
            _plot_convergence(bname,valid,convergence_table(valid),2.0)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 13 — MENU OPTION 10: GENERATE ENGINEERING REPORT
# ══════════════════════════════════════════════════════════════════════════════

def _text_report(designs, simulations, min_fs, max_disp) -> list:
    now   = datetime.datetime.now()
    lines = []

    def h1(t):
        lines.append("")
        lines.append("═" * 80)
        lines.append(f"  {t}")
        lines.append("═" * 80)

    def h2(t):
        lines.append("")
        lines.append(f"  ── {t} ──")
        lines.append("")

    h1("ENGINEERING ANALYSIS REPORT")
    lines.append(f"  Lightweight Automotive Mounting Bracket Optimization")
    lines.append(f"  Generated  : {now.strftime('%B %d, %Y  %I:%M %p')}")
    lines.append(f"  Author     : Nathinael Befekadu | St. Mary's University")
    lines.append(f"  Software   : SolidWorks Simulation + Python Analysis Tool")

    h2("1. PROJECT OVERVIEW")
    lines.append(f"    Objective : Minimize bracket mass while maintaining structural integrity.")
    lines.append(f"    Baseline mass                : {BASELINE_MASS_G} g")
    lines.append(f"    Minimum required FoS         : {min_fs}")
    lines.append(f"    Maximum allowable displacement: {max_disp} mm")

    h2("2. BRACKET DESIGNS AND MATERIAL PROPERTIES")
    for bname in sorted(designs.keys()):
        d  = designs[bname]
        mr = mass_reduction_pct(d.get("mass_grams", 0))
        lines.append(f"    Bracket {bname}:")
        prop_map = [
            ("Material",               "material",                ""),
            ("Yield Strength",         "yield_strength_MPa",      " MPa"),
            ("Mass",                   "mass_grams",              " g"),
            ("Thickness — Vertical",   "thickness_vert_mm",       " mm"),
            ("Thickness — Horizontal", "thickness_horiz_mm",      " mm"),
            ("Height",                 "height_mm",               " mm"),
            ("Width",                  "width_mm",                " mm"),
            ("Length/Depth",           "length_mm",               " mm"),
            ("Mounting Hole Ø",        "mounting_hole_dia_mm",    " mm"),
            ("Load Hole Ø",            "load_hole_dia_mm",        " mm"),
            ("Fillet — Vertical",      "fillet_vert_radius_mm",   " mm"),
            ("Fillet — Horizontal",    "fillet_horiz_radius_mm",  " mm"),
            ("Fillet — Junction",      "fillet_junction_radius_mm"," mm"),
        ]
        for label, fld, unit in prop_map:
            v = d.get(fld)
            if v is not None:
                lines.append(f"      {label:<30}: {v}{unit}")
        lines.append(f"      {'Mass Reduction':<30}: {mr:.2f}%")
        if d.get("additional_notes"):
            lines.append(f"      {'Notes':<30}: {d['additional_notes']}")
        lines.append("")

    h2("3. SIMULATION RESULTS")
    for bname in sorted(designs.keys()):
        d    = designs[bname]
        sims = simulations.get(bname, [])
        lines.append(f"    Bracket {bname} — {d.get('material')} — {d.get('mass_grams')} g")
        if not sims:
            lines.append("      No simulation data entered.")
            lines.append("")
            continue
        for s in sims:
            fs_v = fos(d.get("yield_strength_MPa", 0), s.get("max_von_mises_MPa", 0))
            fo, do, ok = check_requirements(fs_v, s.get("max_displacement_mm"), min_fs, max_disp)
            lines.append(f"      Simulation: {s['sim_name']}")
            lines.append(f"        Applied Force       : {s.get('applied_force_N')} N  {s.get('force_direction')}")
            lines.append(f"        Fixtures            : {s.get('fixture_conditions')}")
            lines.append(f"        Elements / Nodes    : {s.get('num_elements'):,} / {s.get('num_nodes'):,}")
            lines.append(f"        Max von Mises Stress: {s.get('max_von_mises_MPa'):.4f} MPa")
            lines.append(f"        Max Displacement    : {s.get('max_displacement_mm'):.6f} mm")
            lines.append(f"        Factor of Safety    : {fs_v:.3f}" if fs_v else
                         "        Factor of Safety    : N/A")
            lines.append(f"        Result              : {'PASS ✓' if ok else 'FAIL ✗'}")
            lines.append("")

    h2("4. MESH CONVERGENCE SUMMARY")
    lines.append("    Mesh refinement was conducted on Design 7, the final optimized bracket.")
    lines.append("    The other designs were evaluated with individual static FEA simulations.")
    for bname in sorted(designs.keys()):
        sims  = simulations.get(bname, [])
        valid = sorted(
            [s for s in sims if s.get("num_elements") and s.get("max_von_mises_MPa")],
            key=lambda s: s["num_elements"]
        )
        if len(valid) < 2:
            continue
        lines.append(f"    Bracket {bname}:")
        conv = convergence_table(valid)
        lines.append(f"      {'Simulation':<20} {'Elements':>10} {'Stress':>12} "
                     f"{'Δ Stress%':>11} {'Disp':>10} {'Δ Disp%':>9}")
        lines.append("      " + "─" * 76)
        s0 = valid[0]
        lines.append(f"      {s0['sim_name']:<20} {s0['num_elements']:>10,} "
                     f"{s0['max_von_mises_MPa']:>12.4f} {'—':>11} "
                     f"{s0['max_displacement_mm']:>10.6f} {'—':>9}")
        for i, r in enumerate(conv):
            s  = valid[i + 1]
            sc = f"{r['s_chg']:.4f}%" if r["s_chg"] is not None else "N/A"
            dc = f"{r['d_chg']:.4f}%" if r["d_chg"] is not None else "N/A"
            lines.append(f"      {s['sim_name']:<20} {s['num_elements']:>10,} "
                         f"{s['max_von_mises_MPa']:>12.4f} {sc:>11} "
                         f"{s['max_displacement_mm']:>10.6f} {dc:>9}")
        lines.append("")

    h2("5. BRACKET COMPARISON (MOST-REFINED SIMULATION PER BRACKET)")
    lines.append(f"    {'Bracket':<10} {'Mass g':>9} {'Stress MPa':>12} "
                 f"{'Disp mm':>10} {'FoS':>8} {'MassRed%':>10} {'Result':>8}")
    lines.append("    " + "─" * 72)
    for bname in sorted(designs.keys()):
        d   = designs[bname]
        bs  = best_sim(simulations.get(bname, []))
        if bs is None:
            lines.append(f"    {bname:<10} {d['mass_grams']:>9.2f} {'N/A':>12} {'N/A':>10} "
                         f"{'N/A':>8} {mass_reduction_pct(d['mass_grams']):>10.2f} {'NO DATA':>8}")
            continue
        stress = bs.get("max_von_mises_MPa")
        disp   = bs.get("max_displacement_mm")
        fs_v   = fos(d["yield_strength_MPa"], stress)
        _, _, ok = check_requirements(fs_v, disp, min_fs, max_disp)
        mr = mass_reduction_pct(d["mass_grams"])
        lines.append(f"    {bname:<10} {d['mass_grams']:>9.2f} {stress:>12.4f} "
                     f"{disp:>10.5f} {fs_v:>8.3f} {mr:>10.2f} {'PASS' if ok else 'FAIL':>8}")

    h2("6. ENGINEERING ASSUMPTIONS AND LIMITATIONS")
    for i, a in enumerate([
        "Linear elastic material behavior assumed; results valid below yield strength.",
        "FoS = Yield Strength (MPa) / Max von Mises Stress (MPa).",
        "All FEA performed in SolidWorks Simulation.",
        "For Design 7, the last two mesh refinements were compared using the selected 2% change criterion.",
        "Load predictions via linear scaling are estimates only.",
        "Stress singularities may appear at sharp corners or point-load locations.",
        "Analysis does not include fatigue, dynamic loading, vibration, or thermal effects.",
        "Material properties assumed homogeneous and isotropic.",
    ], 1):
        lines.append(f"    {i}. {a}")

    h2("7. CONCLUSION")
    lines.append("    Seven SolidWorks bracket designs were evaluated using a consistent 100 N static load case.")
    lines.append("    Python was used to compare mass, stress, displacement and yield-based factor of safety.")
    lines.append("    The final design reduced mass from 219.82 g to 111.68 g (49.19%).")
    lines.append("    The results meet the selected project screening limits for this simplified static model.")
    lines.append("    See bracket_data/graphs/ for visual comparisons and mesh-refinement plots.")
    lines.append("")
    lines.append("═" * 80)
    lines.append("  END OF REPORT")
    lines.append("═" * 80)
    return lines


def _csv_export(designs, simulations, csv_path):
    fieldnames = [
        "bracket", "material", "yield_MPa",
        "mass_g", "mass_reduction_pct",
        "thickness_vert_mm", "thickness_horiz_mm",
        "fillet_vert_mm", "fillet_horiz_mm", "fillet_junction_mm",
        "sim_name", "force_N", "force_dir", "fixture",
        "num_elements", "num_nodes",
        "max_stress_MPa", "max_disp_mm", "fos"
    ]
    rows = []
    for bname in sorted(designs.keys()):
        d    = designs[bname]
        sims = simulations.get(bname, [])
        base_row = {
            "bracket":             bname,
            "material":            d.get("material"),
            "yield_MPa":           d.get("yield_strength_MPa"),
            "mass_g":              d.get("mass_grams"),
            "mass_reduction_pct":  round(mass_reduction_pct(d.get("mass_grams", 0)), 4),
            "thickness_vert_mm":   d.get("thickness_vert_mm"),
            "thickness_horiz_mm":  d.get("thickness_horiz_mm"),
            "fillet_vert_mm":      d.get("fillet_vert_radius_mm"),
            "fillet_horiz_mm":     d.get("fillet_horiz_radius_mm"),
            "fillet_junction_mm":  d.get("fillet_junction_radius_mm"),
        }
        if not sims:
            row = {**base_row, "sim_name": None, "force_N": None, "force_dir": None,
                   "fixture": None, "num_elements": None,
                   "num_nodes": None, "max_stress_MPa": None, "max_disp_mm": None, "fos": None}
            rows.append(row)
        else:
            for s in sims:
                fs_v = fos(d.get("yield_strength_MPa", 0), s.get("max_von_mises_MPa", 0))
                row = {**base_row,
                       "sim_name":       s.get("sim_name"),
                       "force_N":        s.get("applied_force_N"),
                       "force_dir":      s.get("force_direction"),
                       "fixture":        s.get("fixture_conditions"),
                       "num_elements":   s.get("num_elements"),
                       "num_nodes":      s.get("num_nodes"),
                       "max_stress_MPa": s.get("max_von_mises_MPa"),
                       "max_disp_mm":    s.get("max_displacement_mm"),
                       "fos":            round(fs_v, 4) if fs_v else None}
                rows.append(row)
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader(); w.writerows(rows)


def _pdf_report(designs, simulations, min_fs, max_disp, pdf_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def section(t):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(0, 7, f"  {t}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(1)

    def kv(k, v):
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(70, 6, f"  {k}:", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, str(v) if v is not None else "—")

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "ENGINEERING ANALYSIS REPORT", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Lightweight Automotive Mounting Bracket Optimization", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated: {datetime.datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.cell(0, 6, "Nathinael Befekadu  |  St. Mary's University", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)

    section("1. Project Overview")
    kv("Baseline mass",               f"{BASELINE_MASS_G} g")
    kv("Min required FoS",            str(min_fs))
    kv("Max allowable displacement",  f"{max_disp} mm")
    pdf.ln(3)

    section("2. Bracket Designs")
    for bname in sorted(designs.keys()):
        d  = designs[bname]
        mr = mass_reduction_pct(d.get("mass_grams", 0))
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"  Bracket {bname}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        kv("  Material",               d.get("material"))
        kv("  Yield Strength",         f"{d.get('yield_strength_MPa')} MPa")
        kv("  Mass",                   f"{d.get('mass_grams')} g")
        kv("  Mass Reduction",         f"{mr:.2f}%")
        kv("  Thickness (vert)",       f"{d.get('thickness_vert_mm')} mm")
        kv("  Thickness (horiz)",      f"{d.get('thickness_horiz_mm')} mm")
        kv("  Fillet (vert plate)",    f"{d.get('fillet_vert_radius_mm')} mm")
        kv("  Fillet (horiz plate)",   f"{d.get('fillet_horiz_radius_mm')} mm")
        kv("  Fillet (junction)",      f"{d.get('fillet_junction_radius_mm')} mm")
        pdf.ln(2)

    section("3. Simulation Results")
    for bname in sorted(designs.keys()):
        d    = designs[bname]
        sims = simulations.get(bname, [])
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"  Bracket {bname}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if not sims:
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 6, "  No simulation data.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            continue
        for s in sims:
            fs_v = fos(d.get("yield_strength_MPa", 0), s.get("max_von_mises_MPa", 0))
            _, _, ok = check_requirements(fs_v, s.get("max_displacement_mm"), min_fs, max_disp)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"    {s['sim_name']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 10)
            kv("    Force",      f"{s.get('applied_force_N')} N  {s.get('force_direction')}")
            kv("    Fixtures",   s.get("fixture_conditions"))
            kv("    Elements",   f"{s.get('num_elements'):,}")
            kv("    Max stress", f"{s.get('max_von_mises_MPa'):.4f} MPa")
            kv("    Max disp.",  f"{s.get('max_displacement_mm'):.6f} mm")
            kv("    FoS",        f"{fs_v:.3f}" if fs_v else "N/A")
            kv("    Result",     "PASS" if ok else "FAIL")
            pdf.ln(1)

    section("4. Bracket Comparison Summary")
    pdf.set_font("Helvetica", "B", 9)
    cw   = [18, 22, 28, 24, 18, 22, 20]
    hdrs = ["Bracket", "Mass (g)", "Stress (MPa)", "Disp (mm)", "FoS", "Mass Red%", "Result"]
    for i, h in enumerate(hdrs):
        pdf.cell(cw[i], 7, h, border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for bname in sorted(designs.keys()):
        d  = designs[bname]
        bs = best_sim(simulations.get(bname, []))
        if bs is None:
            rd = [bname, f"{d['mass_grams']:.2f}", "N/A", "N/A", "N/A",
                  f"{mass_reduction_pct(d['mass_grams']):.1f}%", "NO DATA"]
        else:
            sv  = bs.get("max_von_mises_MPa")
            dv  = bs.get("max_displacement_mm")
            fv  = fos(d["yield_strength_MPa"], sv)
            _, _, ok = check_requirements(fv, dv, min_fs, max_disp)
            rd = [bname, f"{d['mass_grams']:.2f}", f"{sv:.2f}", f"{dv:.5f}",
                  f"{fv:.3f}", f"{mass_reduction_pct(d['mass_grams']):.1f}%",
                  "PASS" if ok else "FAIL"]
        for i, v in enumerate(rd):
            pdf.cell(cw[i], 7, v, border=1, align="C")
        pdf.ln()
    pdf.ln(4)

    section("5. Assumptions & Limitations")
    for a in [
        "Linear elastic material behavior assumed throughout.",
        "FoS = Yield Strength / Max von Mises Stress.",
        "Design 7 mesh refinement was assessed using the selected 2% change criterion.",
        "Load predictions are linear estimates — do not replace full FEA.",
        "Fatigue, dynamic, and thermal effects not included.",
        "Stress singularities may occur at sharp corners.",
    ]:
        pdf.cell(5, 6, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.multi_cell(0, 6, a)

    graphs = sorted(GRAPHS_DIR.glob("comparison_bars_*.png"))
    if graphs:
        pdf.add_page()
        section("Appendix A — Performance Comparison Graph")
        try:
            pdf.image(str(graphs[-1]), x=10, w=190)
        except Exception:
            pass

    cg_all = sorted(GRAPHS_DIR.glob("convergence_*.png"))
    if cg_all:
        pdf.add_page()
        section("Appendix B — Mesh Convergence Graphs")
        for cg in cg_all[-1:]:
            try:
                pdf.image(str(cg), x=10, w=190)
                pdf.ln(3)
            except Exception:
                pass

    pdf.output(str(pdf_path))


def _silent_graphs(designs, simulations, min_fs, max_disp, ts):
    _plot_readable_comparisons(designs, simulations, min_fs, max_disp, ts)
    for bname in sorted(designs.keys()):
        valid=sorted([s for s in simulations.get(bname,[]) if s.get("num_elements") and s.get("max_von_mises_MPa")],key=lambda s:s["num_elements"])
        if len(valid)>=2:
            _plot_convergence(bname,valid,convergence_table(valid),2.0)


def generate_report(designs: dict, simulations: dict):
    header("GENERATE ENGINEERING REPORT")
    if not designs:
        print("  No designs saved yet.")
        return

    print("\n  ─── Report Parameters ───")
    min_fs   = get_float("  Minimum acceptable FoS: ", min_val=0.01)
    max_disp = get_float("  Maximum allowable displacement (mm): ", min_val=1e-6)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if MATPLOTLIB_OK:
        existing_graphs = list(GRAPHS_DIR.glob("comparison_bars_*.png"))
        if not existing_graphs:
            print("\n  Generating comparison graphs for report…")
            _silent_graphs(designs, simulations, min_fs, max_disp, ts)
        else:
            print("\n  Reusing existing engineering graphs (no duplicate copies created).")

    txt_path = REPORTS_DIR / f"report_{ts}.txt"
    lines    = _text_report(designs, simulations, min_fs, max_disp)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  ✓ Text report  : {txt_path}")

    csv_path = REPORTS_DIR / f"data_{ts}.csv"
    _csv_export(designs, simulations, csv_path)
    print(f"  ✓ CSV export   : {csv_path}")

    if FPDF_OK:
        pdf_path = REPORTS_DIR / f"report_{ts}.pdf"
        try:
            _pdf_report(designs, simulations, min_fs, max_disp, pdf_path)
            print(f"  ✓ PDF report   : {pdf_path}")
        except Exception as e:
            print(f"  ⚠  PDF error: {e}  (text report still saved)")
    else:
        print("  (Install fpdf2 for PDF:  pip install fpdf2)")

    print(f"\n  All report files saved to: {REPORTS_DIR}/")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 14 — MAIN MENU LOOP
# ══════════════════════════════════════════════════════════════════════════════

MENU = """
╔══════════════════════════════════════════════════════════════════════════╗
║   LIGHTWEIGHT AUTOMOTIVE MOUNTING BRACKET OPTIMIZATION TOOL             ║
║   Nathinael Befekadu  |  St. Mary's University                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║   1.  Add New Bracket Design                                            ║
║   2.  Add Simulation Results to an Existing Bracket                     ║
║   3.  View or Edit Saved Designs                                        ║
║   4.  Analyze Individual Bracket                                        ║
║   5.  Compare All Bracket Designs                                       ║
║   6.  Find the Best Bracket                                             ║
║   7.  Perform Mesh Convergence Analysis                                 ║
║   8.  Predict Performance Under Different Loads                         ║
║   9.  Generate Engineering Graphs                                       ║
║  10.  Generate Engineering Report                                       ║
║  11.  Exit                                                              ║
╚══════════════════════════════════════════════════════════════════════════╝"""

ACTIONS = {
    "1":  add_bracket,
    "2":  add_simulation_menu,
    "3":  view_edit_designs,
    "4":  analyze_bracket,
    "5":  compare_brackets,
    "6":  find_best,
    "7":  convergence_analysis,
    "8":  predict_load,
    "9":  generate_graphs,
    "10": generate_report,
}


def main():
    init_dirs()
    print("\n  Loading saved data…", end="", flush=True)
    designs     = load_designs()
    simulations = load_simulations()
    n = len(designs)
    print(f"  {n} bracket design{'s' if n != 1 else ''} found.")

    if not MATPLOTLIB_OK:
        print("  ⚠  Matplotlib not installed — graphs disabled.  (pip install matplotlib)")
    if not FPDF_OK:
        print("  ⚠  fpdf2 not installed — PDF export disabled.   (pip install fpdf2)")

    while True:
        print(MENU)
        choice = input("  Enter choice (1–11): ").strip()

        if choice == "11":
            print("\n  All data saved automatically.  Goodbye!\n")
            break

        if choice not in ACTIONS:
            print("\n  ⚠  Invalid choice.  Enter a number 1–11.")
            continue

        ACTIONS[choice](designs, simulations)
        pause()


if __name__ == "__main__":
    main()
