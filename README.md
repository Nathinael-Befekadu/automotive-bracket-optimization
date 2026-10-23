Lightweight Automotive Mounting Bracket Optimization
SolidWorks | Finite Element Analysis (FEA) | Python | Structural Optimization

An independent mechanical engineering project focused on designing, analyzing, and optimizing a lightweight automotive mounting bracket through iterative CAD modifications, finite element simulations, mesh refinement, and Python-based engineering analysis.

The project achieved a 49.19% mass reduction while satisfying the selected structural strength and stiffness criteria under a 100 N static loading condition.

Project Highlights
Performance Metric	Baseline Design	Final Design
Mass	219.82 g	111.68 g
Maximum von Mises Stress	12.75 MPa	32.37 MPa
Maximum Displacement	0.02114 mm	0.09300 mm
Yield-Based Factor of Safety	21.57	8.50


Key achievement: Reduced bracket mass by 108.14 g (49.19%) while maintaining a factor of safety above 3 and maximum displacement below 0.10 mm for the analyzed loading condition.
1. Project Objectives
The primary objectives of this project were to:
- Design a functional automotive mounting bracket using SolidWorks.
- Perform static structural analysis using SolidWorks Simulation.
- Reduce bracket mass through iterative geometric optimization.
- Evaluate von Mises stress, displacement, and factor of safety.
- Perform mesh-refinement analysis to assess numerical sensitivity.
- Compare material alternatives.
- Develop a Python program to organize simulation results, perform engineering calculations, and visualize design trade-offs.
2. Engineering Design and FEA
The bracket was modeled using Aluminum 6061-T6, with an assumed yield strength of 275 MPa.

The static simulation used the following conditions:
Parameter	Value
Material	Aluminum 6061-T6
Applied Force	100 N downward
Fixtures	Fixed inner surfaces of two lower mounting holes
Minimum Factor of Safety	3.0
Maximum Allowable Displacement	0.10 mm
Analysis Type	Linear static FEA


The 100 N loading condition was selected as a representative design-study load. The safety factor and displacement thresholds were project-defined screening criteria rather than automotive certification requirements.
Final CAD Model

Von Mises Stress Distribution

The final design recorded a maximum von Mises stress of 32.37 MPa.
Displacement Distribution

The maximum resultant displacement was 0.09300 mm, satisfying the selected 0.10 mm displacement limit.
3. Design Optimization
Seven design iterations were evaluated through progressive geometric modifications, including plate-thickness adjustments, width reduction, and material-removal cutouts.

The objective was to minimize mass while maintaining acceptable structural performance.
Mass Reduction Across Design Iterations

The final design achieved a 49.19% reduction in mass, from 219.82 g to 111.68 g.
Engineering Performance Comparison

Mass–Performance Trade-Offs

These comparisons illustrate how reducing material affects maximum stress, displacement, and factor of safety.
4. Mesh-Refinement Analysis
A mesh-refinement study was performed on the final optimized bracket to evaluate the sensitivity of the numerical results to mesh density.

The final simulation contained:
- 64,851 elements
- 100,892 nodes
- 32.37 MPa maximum von Mises stress
- 0.09300 mm maximum displacement
Mesh-Convergence Results

Between the final two mesh levels, the maximum stress changed by approximately 1.92%, while displacement changed by approximately 0.0215%.

Both changes were below the selected 2% comparison tolerance.
5. Python Engineering Analysis Tool
A Python-based engineering analysis program was developed to support the bracket optimization process.

The program organizes SolidWorks simulation data and provides the following functionality:
- Store and manage bracket design configurations.
- Record structural simulation results.
- Calculate yield-based factors of safety.
- Compare mass, stress, and displacement across designs.
- Identify designs satisfying specified engineering constraints.
- Analyze mesh-refinement results.
- Generate engineering comparison graphs.
- Produce engineering reports.
- Estimate performance under alternative loads using simplified linear-elastic scaling assumptions.
Python is used for engineering data processing and comparison. Structural simulation results originate from SolidWorks FEA.
Technologies Used
- SolidWorks: 3D CAD modeling and engineering drawings
- SolidWorks Simulation: Static FEA and mesh refinement
- Python: Engineering calculations and automated analysis
- NumPy: Numerical operations
- Matplotlib: Engineering data visualization
- JSON: Structured storage of design and simulation data
Running the Python Program
Install the required dependencies:
pip install -r requirements.txt
Run the program:
python main.py
The program provides a menu-driven interface for accessing the design database, analyzing results, comparing configurations, generating graphs, and producing reports.
6. Engineering Drawing

The final drawing documents the optimized bracket geometry, principal dimensions, mounting-hole arrangement, and material specification.

[View Engineering Drawing — AMB-001](documentation/AMB-001_Drawing.pdf)
7. Engineering Report
The complete technical report includes the design methodology, simulation setup, optimization results, mesh-refinement analysis, material comparison, sample calculations, engineering drawings, and study limitations.

[View Full Engineering Report (PDF)](documentation/Engineering_Report.pdf)
8. Study Limitations
This project evaluates the bracket under a simplified linear-static loading condition with idealized fixed supports.

The analysis does not include fatigue, vibration, impact loading, bolt preload, detailed contact behavior, or physical prototype testing.

Further validation would be required before applying the design to an actual automotive assembly.
9. Conclusion
This project demonstrates the application of mechanical design, finite element analysis, and Python-based engineering analysis to a structural optimization problem.

Through seven design iterations, the bracket mass was reduced by 49.19% while maintaining the selected strength and stiffness requirements under the assumed static load.

The project strengthened practical skills in CAD modeling, structural simulation, mesh refinement, engineering decision-making, Python programming, and technical documentation.
Project Type: Independent Mechanical Engineering Project

Engineering Tools: SolidWorks, SolidWorks Simulation, Python

Author: Nathinael Solomon Befekadu

St. Mary's University — Mechanical Engineering
