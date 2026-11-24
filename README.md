# 2D Modeling of Magmatic Intrusion Cooling with Groundwater Flow

**Riski Basrin — 10973593 - GPGN 536**

## Run the application

[Open the interactive simulation](https://riskibasrin-cell.github.io/intrusion-cooling-2D/)

The application runs Python directly in the browser using Pyodide in a Web Worker. No backend server is required.

Choose the model parameters and click **Run both cases**, or click **View saved example** to inspect the default results.

A hot intrusion → heat spreads into the surrounding rock → water carries heat → the temperature pattern and cooling change.

I want to understand how groundwater flow changes intrusion cooling and heat spreading in the surrounding rock. I compare two cases, with and without flow, using the same initial temperature and thermal properties.

## Where should I start?

1. Open `Intrusion_2D_Project.ipynb` to follow the project and inspect the results.
2. Open `Verification.ipynb` to see the analytical comparison and error analysis.
3. Launch the web application to change parameters and view the animation.
4. The geophysical calculations that I need to explain are in `simulation.py`.

This package is entirely in English. The earlier Indonesian archive is omitted, so this ZIP contains only the current solver and the English project files.

## Install and run locally

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment: on Windows, use `.venv\Scripts\activate`; on macOS/Linux, use `source .venv/bin/activate`.

```bash
python -m pip install -r requirements.txt
python -m http.server 8000
```

Open `http://localhost:8000`. Use HTTP rather than opening `index.html` through `file://`, because the worker and source-code requests need an HTTP server.

The interface uses HTML/JavaScript. The calculations run in Python through **Pyodide 0.27.7 inside a Web Worker**, without a backend. Internet access is needed to download Pyodide, NumPy, and SciPy from the CDN on the first load. The Stop button terminates the worker.

To open the notebooks:

```bash
jupyter lab
```

To run the basic numerical checks:

```bash
python checks.py
```

To rebuild the English notebooks and plots, rerunning the default intrusion and analytical checks while reusing saved refinement summaries:

```bash
python build_deliverables.py
```

To recompute all intrusion simulations as well, including the half-time-step and 10 m grid comparisons:

```bash
python build_deliverables.py --recompute
```

The full recomputation takes longer than a single simulation. Launch notebooks with the project folder as the kernel working directory. Keep all supporting files together after extracting the ZIP.

## Geophysical model

The local domain is 2,000 × 2,000 m. An impermeable intrusion lies at its center, with default dimensions of 200 × 400 m. The vertical coordinate z increases downward. It is a local coordinate, not an absolute emplacement depth.

Steady groundwater flow:

$$\nabla\cdot(K\nabla h)=0,\qquad \mathbf q=-K\nabla h,\qquad K=k\rho_wg/\mu_w.$$

The left head is 20 m and the right head is 0 m. The top and bottom boundaries have no water flux. Intrusion permeability is zero. Here, q is Darcy flux, not pore velocity; the energy equation uses Darcy flux directly.

Heat transfer:

$$C\frac{\partial T}{\partial t}=\nabla\cdot(\lambda\nabla T)-\rho_wc_{p,w}\nabla\cdot(\mathbf qT).$$

The initial intrusion temperature is 1,000°C. The surrounding rock and all four thermal boundaries are at 100°C. Water and rock are assumed to be in local thermal equilibrium. The no-flow case retains the same saturated-rock heat capacity.

| Parameter | Default value | Unit |
|---|---:|---|
| Intrusion density | 2700 | kg/m³ |
| Intrusion specific heat | 1046 | J/(kg K) |
| Intrusion thermal conductivity | 3.0 | W/(m K) |
| Rock density | 2300 | kg/m³ |
| Rock specific heat | 1000 | J/(kg K) |
| Effective host-rock thermal conductivity | 2.5 | W/(m K) |
| Porosity | 0.01 | fraction |
| Host-rock permeability | 10⁻¹⁵ | m² |
| Water density | 1000 | kg/m³ |
| Water specific heat | 4180 | J/(kg K) |
| Water dynamic viscosity | 2.82 × 10⁻⁴ | Pa s |
| Gravitational acceleration | 9.8 | m/s² |
| Simulation duration | 5000 | years |

**Parameter source:** material properties, porosity, permeability, gravity, and initial intrusion temperature match Table 2 of Fu et al. (2010). The table was checked using the [available manuscript text](https://www.academia.edu/20722067/Numerical_modeling_of_magmatic_hydrothermal_systems_constrained_by_U_Th_Pb_He_time_temperature_histories). Rock conductivity is used as an approximation to the effective conductivity of saturated rock. Domain size, geometry, head, background temperature, duration, and grid are project choices. This model does not reproduce the full physics or boundary conditions of that paper. No observational data are used.

## Numerical method

- Grid points lie at cell centers, with domain and intrusion boundaries at cell faces. Incompatible intrusion dimensions are rejected.
- Arrays retain the order `T[j, i]`: vertical row first, horizontal column second.
- Conservative intercell fluxes use four neighbors and harmonic means at material interfaces. This is a control-volume form of centered differences.
- Head is obtained from a sparse linear system. At a Dirichlet boundary, the distance from the outermost cell center to the boundary is half the grid spacing.
- Conduction uses Crank–Nicolson. The sparse matrix is factorized once per time step size.
- Advection uses explicit upwinding according to the sign of Darcy flux at each face.
- Conduction and advection are applied sequentially. The combined method is generally first-order in time. Upwind advection is first-order in space; second-order spatial convergence in the conduction test does not apply automatically to the full model.
- The time step is selected from the conduction rate and the advective CFL limit, then adjusted to reach the requested final time exactly. The conservative conduction restriction also helps control early oscillations caused by the initial temperature jump.
- Reported center temperature is the average of the cells closest to the geometric center. It is not a value at a single node located exactly at the center.

## Three main outputs

1. A hydraulic-head map and arrows showing flow around the intrusion.
2. Temperature maps and an animation with a fixed color scale; both flow cases can be selected.
3. Center-temperature cooling curves for both cases, the final difference, and a CSV download.

The computed default example is stored in `results/example.json`. The **View saved example** button displays those saved results, rather than recalculating newly edited controls. Expected numerical summaries are in `results/summary.json`. English figures are `flow.png`, `temperature_maps.png`, and `cooling_curves.png`.

At 5,000 years, the 20 m grid gives approximately 140.081°C with flow and 140.416°C without flow. Their difference is 0.335°C. The 10 m grid gives a difference of 0.282°C. The center effect is small, and its exact magnitude remains grid-sensitive. See `results/interpretation.md` for the full comparison.

## Verification and interpretation

`Verification.ipynb` imports checks from `checks.py`. These call `conduction_operator` and `prepare_conduction`, the same functions used by the application.

The analytical test uses a decaying 2D sinusoidal temperature field in homogeneous rock without flow. The boundary temperature is 100°C and the initial amplitude is 100°C. The notebook includes numerical/analytical plots, an error map, RMSE, maximum error, grid refinement, and time-step refinement. The time analysis also uses the exact semidiscrete solution to separate temporal and spatial errors.

Additional checks examine uniform temperature, water-flux balance, an impermeable intrusion, geometry, and the sensitivity of the actual intrusion comparison to dt/2 and a 10 m grid.

The full intrusion model has no analytical comparison here. The conduction test does not establish advection accuracy or accuracy at material interfaces. Two intrusion grids provide a sensitivity check, not proof of asymptotic convergence. Upwinding adds numerical diffusion, so a small flow effect must be interpreted together with grid sensitivity.

## Model limitations

Flow is fixed and independent of temperature. Water and material properties are constant. Latent heat, boiling, phase changes, fractures, and buoyancy-driven flow are omitted. The intrusion loses heat through conduction at its edges; water does not pass through magma. Fixed-temperature boundaries can remove heat. This is an idealized experiment, not a field reconstruction or a complete hydrothermal prediction.

## Files

| File | Purpose |
|---|---|
| `simulation.py` | Parameters, initial/boundary conditions, head, fluxes, and heat solver |
| `plots.py` | Plotting functions used by the project notebook |
| `checks.py` | Verification cases using the application solver |
| `Intrusion_2D_Project.ipynb` | Project explanation and main results |
| `Verification.ipynb` | Executed verification notebook |
| `index.html`, `app.js` | Browser interface |
| `worker.js` | Pyodide initialization and Python execution in a worker |
| `build_deliverables.py` | Rebuild notebooks, figures, and optionally all simulations |
| `finalize_notes.py` | Generate interpretation from the computed summaries |
| `.github/workflows/pages.yml` | GitHub Pages deployment through GitHub Actions |
| `requirements.txt` | Local Python dependencies |
| `AI_USE.md` | AI-use statement |
| `START_HERE.md` | Short opening instructions and completion status |

## Deploy to GitHub Pages

1. Create a GitHub repository and upload the **contents** of this project folder, including `.github/workflows/pages.yml`. Use `main` as the default branch, or change the branch in the workflow.
2. Open **Settings → Pages → Source → GitHub Actions**.
3. Run the workflow or push to `main`. Wait for deployment to finish.
4. Open the URL shown by the `deploy` job. Test a new simulation, parameter changes, animation, the saved example, and CSV download in the browser.
5. Add the application URL near the top of the repository README. Provide the repository link and application URL according to the instructor's latest submission instructions.

**Current status:** The application is deployed on GitHub Pages. Basic browser functionality has been tested: loading the saved example, running a new 100-year simulation, displaying results, playing the temperature animation, switching between flow cases, and downloading the CSV summary.

These functional checks do not establish scientific accuracy for every parameter combination. Numerical verification and grid sensitivity are discussed in `Verification.ipynb`.

## References and external code

- Fu, F.Q., McInnes, B.I.A., Evans, N.J., & Davies, P.J. (2010). *Numerical modeling of magmatic–hydrothermal systems constrained by U–Th–Pb–He time–temperature histories*. Journal of Geochemical Exploration, 106(1–3), 90–109. https://doi.org/10.1016/j.gexplo.2009.09.001. Parameter reference: Table 2. The present model uses simplified physics.
- Jin, G. *Geophysics Computing, GPGN 436/536*, especially [05_Parabolic_PDEs.ipynb](https://github.com/jinwar/GeophysicsComputing_GPGN436536/blob/main/05_Parabolic_PDEs.ipynb). Course-method reference; this package is not a copy of that notebook's code.
- Jin, G. [Final Project Demo](https://github.com/jinwar/GPGN436_FinalProject_Demo), an example of application development instructions.
- *GPGN 436/536 — Final Project Instructions and Grading Policy, Fall 2026*, provided PDF, and the additional message about Pyodide, Web Workers, and GitHub Pages.
- Pyodide contributors. [Using Pyodide in a web worker, version 0.27.7](https://pyodide.org/en/0.27.7/usage/webworker.html).
- NumPy, SciPy, and Matplotlib provide standard numerical and plotting functionality.
