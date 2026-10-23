# Lightweight Automotive Mounting Bracket Optimization

**SolidWorks | Finite Element Analysis (FEA) | Python | Structural Optimization**

An independent mechanical engineering project focused on designing, analyzing, and optimizing a lightweight automotive mounting bracket through iterative CAD modifications, finite element simulations, mesh refinement, and Python-based engineering analysis.

The final design achieved a **49.19% mass reduction** while meeting the selected structural strength and stiffness criteria under an assumed **100 N static load**.

![Final Automotive Mounting Bracket](figures/final_bracket_cad.png)

## Project Highlights

| Performance Metric | Baseline Design | Final Design |
|---|---:|---:|
| Mass | 219.82 g | 111.68 g |
| Maximum von Mises Stress | 12.75 MPa | 32.37 MPa |
| Maximum Displacement | 0.02114 mm | 0.09300 mm |
| Yield-Based Factor of Safety | 21.57 | 8.50 |
| Mass Reduction | — | **49.19%** |

**Key result:** Reduced bracket mass by **108.14 g (49.19%)**, while maintaining a yield-based factor of safety above 3.0 and maximum displacement below 0.10 mm for the analyzed loading conditions.

## 1. Project Objectives

- Design an automotive mounting bracket using SolidWorks.
- Perform static structural analysis using SolidWorks Simulation.
- Reduce bracket mass through iterative geometric optimization.
- Evaluate von Mises stress, displacement, and yield-based factor of safety.
- Assess mesh sensitivity through a mesh-refinement study.
- Evaluate material alternatives.
- Develop a Python engineering tool for calculations, design comparisons, data visualization, and automated reporting.

## 2. CAD Design and FEA Setup

The bracket was modeled using **Aluminum 6061-T6**, with an assumed yield strength of **275 MPa**.

| Parameter | Value |
|---|---|
| Material | Aluminum 6061-T6 |
| Applied Load | 100 N downward |
| Fixtures | Fixed inner surfaces of two lower mounting holes |
| Minimum Factor of Safety | 3.0 |
| Maximum Allowable Displacement | 0.10 mm |
| Analysis Type | Linear Static FEA |

The loading conditions and performance limits were selected for this engineering study rather than taken from specific vehicle manufacturer requirements.

### Final CAD Model

![Final Bracket CAD](figures/final_bracket_cad.png)

### Von Mises Stress Distribution

![SolidWorks Stress Results](figures/solidworks_stress.png)

**Maximum von Mises stress:** 32.37 MPa

### Displacement Distribution

![SolidWorks Displacement Results](figures/solidworks_displacement.png)

**Maximum resultant displacement:** 0.09300 mm

## 3. Design Optimization

Seven bracket designs were evaluated through iterative modifications involving plate thickness, bracket width, geometric features, and material removal.

The objective was to minimize mass while satisfying the selected structural performance constraints.

### Design Iteration Results

| Design | Mass (g) | Stress (MPa) | Displacement (mm) | FoS | Mass Reduction |
|---|---:|---:|---:|---:|---:|
| Design 1 | 219.82 | 12.75 | 0.02114 | 21.569 | 0.00% |
| Design 2 | 188.26 | 20.79 | 0.04660 | 13.228 | 14.36% |
| Design 3 | 167.76 | 32.88 | 0.09242 | 8.364 | 23.68% |
| Design 4 | 150.62 | 34.27 | 0.09819 | 8.025 | 31.48% |
| Design 5 | 142.10 | 31.67 | 0.08747 | 8.683 | 35.36% |
| Design 6 | 124.08 | 31.94 | 0.09317 | 8.610 | 43.55% |
| **Design 7** | **111.68** | **32.37** | **0.09300** | **8.496** | **49.19%** |

All seven designs satisfied the selected strength and displacement criteria under the assumed loading conditions.

### Mass Reduction Across Designs

![Mass Reduction](figures/mass_reduction.png)

### Design Performance Comparison

![Design Comparison](figures/design_comparison.png)

### Mass–Performance Trade-Offs

![Mass Performance](figures/mass_performance.png)

These graphs were generated using Python to compare structural performance and mass across the design iterations.

## 4. Mesh-Refinement Analysis

A mesh-refinement study was performed on the final optimized bracket (Design 7) to evaluate the sensitivity of the calculated stress and displacement to mesh density.

| Final Mesh Metric | Value |
|---|---:|
| Elements | 64,851 |
| Nodes | 100,892 |
| Maximum von Mises Stress | 32.37 MPa |
| Maximum Displacement | 0.09300 mm |

### Mesh-Refinement Results

![Mesh Convergence](figures/mesh_convergence.png)

Between the final two mesh levels:

- Maximum stress changed by approximately **1.92%**.
- Maximum displacement changed by approximately **0.0215%**.

Both changes were below the selected 2% comparison tolerance. This provides evidence of reduced mesh sensitivity between those two levels, but does not establish complete mesh independence.

## 5. Python Engineering Analysis Tool

I developed a Python program to organize SolidWorks FEA results and support the engineering optimization workflow.

### Program Capabilities

- Store and manage bracket design information.
- Organize simulation results using JSON files.
- Calculate yield-based factors of safety.
- Compare bracket mass, stress, displacement, and structural performance.
- Identify designs satisfying selected engineering constraints.
- Analyze mesh-refinement results.
- Generate engineering graphs.
- Automatically generate engineering analysis reports.
- Estimate stress, displacement, and factor of safety under different loads using simplified linear-elastic scaling assumptions.

**Important:** SolidWorks Simulation provides the finite element results. The Python program processes, compares, and presents these results; its load predictions are estimates rather than new FEA simulations.

### Tools and Technologies

| Technology | Application |
|---|---|
| SolidWorks | 3D CAD modeling and engineering drawings |
| SolidWorks Simulation | Static FEA and mesh refinement |
| Python | Engineering calculations and automation |
| NumPy | Numerical calculations |
| Matplotlib | Engineering graphs and data visualization |
| JSON | Design and simulation data storage |
| fpdf2 | Automated PDF report generation |

### Running the Python Program

**1. Clone the repository**

```bash
git clone https://github.com/Nathinael-Befekadu/automotive-bracket-optimization.git
```

**2. Open the project directory**

```bash
cd automotive-bracket-optimization
```

**3. Install the dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the program**

```bash
python main.py
```

The program reads design and simulation records from the `data/` directory. Generated graphs and reports are saved locally in the corresponding output directories.

## 6. Engineering Drawing

![Final Engineering Drawing](figures/final_bracket_drawing.png)

The drawing documents the final bracket geometry, principal dimensions, mounting-hole locations, and design designation **AMB-001**.

[View Final Engineering Drawing (PDF)](documentation/AMB-001_Drawing.pdf)

## 7. Engineering Documentation

### Full Engineering Report

The full engineering report describes the design methodology, FEA setup, optimization iterations, mesh-refinement results, material comparison, engineering calculations, and study limitations.

[View Full Engineering Report (PDF)](documentation/Engineering_Report.pdf)

### Python-Generated Engineering Analysis Report

The Python program automatically generates a separate analysis report using the recorded design and simulation data.

The report includes design properties, FEA results, factor-of-safety calculations, mesh-refinement comparisons, performance tables, and engineering assumptions.

[View Python-Generated Analysis Report (TXT)](documentation/engineering_analysis_report.txt)

## 8. Study Limitations

This project represents a simplified linear-static structural analysis with idealized fixed supports.

The analysis does not include:

- Fatigue or cyclic loading.
- Vibration and dynamic loading.
- Impact loading.
- Bolt preload and detailed contact behavior.
- Manufacturing tolerances.
- Physical prototype testing.

The results are appropriate for evaluating the selected educational design case. Additional engineering analysis, realistic boundary conditions, and experimental validation would be necessary before considering the bracket for an actual automotive application.

## 9. Conclusion

The final bracket achieved a **49.19% reduction in mass**, decreasing from 219.82 g to 111.68 g.

Under the assumed 100 N static load, the final design recorded:

- **Maximum von Mises stress:** 32.37 MPa
- **Maximum displacement:** 0.09300 mm
- **Yield-based factor of safety:** 8.50

The project demonstrates an integrated engineering workflow combining CAD design, finite element simulation, structural optimization, mesh refinement, Python-based data analysis, and technical documentation.

---

**Project Type:** Independent Mechanical Engineering Project

**Tools:** SolidWorks, SolidWorks Simulation, Python

**Author:** Nathinael Solomon Befekadu

**Institution:** St. Mary's University — Mechanical Engineering
