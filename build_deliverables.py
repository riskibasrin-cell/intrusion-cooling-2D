"""Build the English notebooks and plots. Use --recompute to refresh refinement runs."""
import argparse
import base64
import contextlib
import io
import json
import os
from pathlib import Path

os.environ['MPLBACKEND'] = 'Agg'
import matplotlib.pyplot as plt
import numpy as np
from simulation import Parameters, run_pair
from plots import plot_results
from finalize_notes import finalize

ROOT = Path(__file__).resolve().parent


def plain(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def write_notebook(name, cells, initial_namespace=None):
    # Execute each cell and save its actual text and figure outputs.
    namespace = {'__name__': '__main__'}
    namespace.update(initial_namespace or {})
    output_cells = []
    count = 0
    for kind, source in cells:
        cell = {'id': f'cell-{len(output_cells):03d}', 'cell_type': kind,
                'metadata': {}, 'source': source.splitlines(True)}
        if kind == 'code':
            count += 1
            outputs = []
            text = io.StringIO()

            def show():
                for number in plt.get_fignums():
                    figure = plt.figure(number)
                    buffer = io.BytesIO()
                    figure.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                    outputs.append({'output_type': 'display_data', 'metadata': {},
                                    'data': {'image/png': base64.b64encode(buffer.getvalue()).decode()}})
                plt.close('all')

            plt.show = show
            with contextlib.redirect_stdout(text):
                exec(compile(source, name, 'exec'), namespace)
            if text.getvalue():
                outputs.insert(0, {'output_type': 'stream', 'name': 'stdout',
                                   'text': text.getvalue().splitlines(True)})
            cell.update(execution_count=count, outputs=outputs)
        output_cells.append(cell)
    notebook = {'cells': output_cells,
                'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                             'language_info': {'name': 'python', 'version': '3.12'}},
                'nbformat': 4, 'nbformat_minor': 5}
    (ROOT / name).write_text(json.dumps(notebook, ensure_ascii=False, indent=1))
    return namespace


PROJECT_CELLS = [
('markdown', r'''# 2D Modeling of Magmatic Intrusion Cooling with Groundwater Flow
**Riski Basrin — GPGN 536**

## What do I want to understand?
A hot intrusion → heat spreads into the surrounding rock → water flows through the rock → water carries heat → the temperature pattern and cooling change.

My question is: **how does groundwater flow change intrusion cooling and heat spreading in the surrounding rock?**

I compare two cases with the same initial temperature and thermal properties: with flow and without flow. In the no-flow case, water remains in the pores but does not move.

## 1. Define where the process takes place
The domain is 2,000 × 2,000 m, with a 200 × 400 m intrusion at the center. The vertical coordinate z increases downward. It is a local coordinate, not an absolute depth.

Arrays still use **T[j, i]**: vertical row first, horizontal column second. Grid points are at cell centers. Intrusion boundaries lie at cell faces, so its area is exactly 80,000 m².

Keep this notebook in the same folder as `simulation.py` and `plots.py`.
'''),
('code', r'''import numpy as np
import matplotlib.pyplot as plt
from simulation import Parameters, make_grid, run_pair
from plots import plot_results

# Keep the project parameters visible here. Full defaults are in simulation.py.
p = Parameters(spacing=20.0, width=200.0, height=400.0,
               Tm=1000.0, Tb=100.0, k_host=1.e-15,
               head_left=20.0, head_right=0.0, years=5000.0)
x, z, X, Z, intrusion = make_grid(p)
print("Grid spacing:", p.spacing, "m")
print("Array shape:", intrusion.shape)
print("Intrusion area:", intrusion.sum() * p.spacing**2, "m²")
'''),
('markdown', r'''## 2. Equations and boundary conditions
Steady groundwater flow is calculated from
$$
\nabla\cdot(K\nabla h)=0,\qquad \mathbf q=-K\nabla h,
\qquad K=\frac{k\rho_w g}{\mu_w}.
$$
The head is 20 m at the left boundary and 0 m at the right boundary. Water cannot cross the top or bottom boundary. Intrusion permeability is zero, so water flows around it.

Heat transfer is calculated from
$$
C\frac{\partial T}{\partial t}=\nabla\cdot(\lambda\nabla T)
-\rho_w c_{p,w}\nabla\cdot(\mathbf qT).
$$
The intrusion starts at 1,000°C. The surrounding rock and all four thermal boundaries are at 100°C.

The heat capacity per unit volume of saturated host rock is
$$
C_h=(1-\phi)\rho_r c_{p,r}+\phi\rho_w c_{p,w}.
$$
Inside the intrusion, heat capacity per unit volume is intrusion density multiplied by its specific heat.

'''),
('code', r'''# Set the same initial temperature and material properties for both cases.
T_initial = np.full(X.shape, p.Tb, dtype=float)
T_initial[intrusion] = p.Tm

C = np.where(intrusion, p.rho_intrusion * p.cp_intrusion, p.C_host)
lam = np.where(intrusion, p.lambda_intrusion, p.lambda_host)

print("Initial intrusion temperature:", p.Tm, "°C")
print("Initial host-rock temperature:", p.Tb, "°C")
print("Temperature on all four domain boundaries:", p.Tb, "°C")
print("Left/right hydraulic head:", p.head_left, "/", p.head_right, "m")
print("Top/bottom flow boundaries: no water flux")
print("Intrusion permeability: 0 m² (impermeable)")
print("Host-rock volumetric heat capacity:", p.C_host, "J/(m³ K)")
'''),
('markdown', r'''## 3. How do I calculate it?
Intercell fluxes connect four neighbors, using harmonic means at material interfaces. Conduction uses **Crank–Nicolson**. After conduction, advection uses **explicit upwinding**. The time step is limited to keep the update controlled.

Crank–Nicolson is second-order in time for smooth conduction. The combination with upwind advection and sequential splitting is generally first-order in time. Centered conduction is second-order in space for a homogeneous smooth case; upwind advection is first-order in space.


The code below prepares the flow field, the conduction matrix, and the time-step estimate. The functions are defined in `simulation.py`, which is also used by the browser application and verification tests.

Inside the time loop, `run_pair` repeats these steps: conduction → advection for the flow case; conduction alone for the no-flow case. The detailed loop is visible in `simulation.py`.
'''),
('code', r'''from simulation import solve_flow, conduction_operator, SECONDS_PER_YEAR

# Solve groundwater flow. The intrusion blocks water but conducts heat.
head, qx, qz = solve_flow(p, intrusion)

# Assemble the same conduction operator used by run_pair and verification.
L, b_boundary = conduction_operator(C, lam, p.spacing, p.spacing, p.Tb)

# Inspect the rates used to select the time step.
rate_conduction = np.max(-L.diagonal())
outflow = (
    (np.maximum(qx[:, 1:], 0.0) + np.maximum(-qx[:, :-1], 0.0)) / p.spacing
    + (np.maximum(qz[1:, :], 0.0) + np.maximum(-qz[:-1, :], 0.0)) / p.spacing
)
rate_advection = np.max(p.rho_water * p.cp_water * outflow / C)
dt_conduction = 0.5 / rate_conduction
dt_advection = 0.5 / rate_advection if rate_advection > 0 else np.inf
dt_selected = min(dt_conduction, dt_advection)

print("Conduction matrix shape:", L.shape)
print("Largest horizontal Darcy-flux magnitude:", np.max(np.abs(qx)), "m/s")
print("Largest vertical Darcy-flux magnitude:", np.max(np.abs(qz)), "m/s")
print("Selected time step before final-time adjustment:",
      dt_selected / SECONDS_PER_YEAR, "years")
print("Advective CFL before final-time adjustment:", dt_selected * rate_advection)
'''),
('markdown', r'''## 4. Run the two cases
Both cases start from the same initial temperature. Do not use the final temperature of one case as the initial temperature of the other.

The saved outputs below come from the already computed default example. Running this cell in Jupyter performs a fresh simulation.

**Run the code cell immediately below.** It starts both cases from the original temperature, performs all time steps through `run_pair`, and saves the histories and temperature maps in `r`. The next section uses this result to make the figures.
'''),
('code', r'''# Run until both cases are complete.
r = run_pair(p)
print("Simulation completed.")
print("Number of time steps:", r["n_steps"])
print("Actual dt:", r["dt_years"], "years")
print("Center without flow:", r["center_no_flow"][-1], "°C")
print("Center with flow:", r["center_flow"][-1], "°C")
print("Difference (no flow − with flow):",
      r["center_no_flow"][-1] - r["center_flow"][-1], "°C")
print("Largest difference between the final maps:",
      r["max_final_map_difference"], "°C")
'''),
('markdown', r'''## 5. Look at the results
My three main outputs are the flow map, the temperature maps, and the cooling curves.

Arrows show water flowing around the intrusion. The temperature maps use the same color scale. Darker colors at late times show cooling, but they do not mean the whole domain is exactly 100°C.

On a cell-centered grid, the geometric center lies between four cells. The reported center temperature is the average of those nearest cells, rather than the old [50, 50] node value.
'''),
('code', r'''figures = plot_results(r)
plt.show()
'''),
('markdown', r'''## 6. Discussion
For the default parameters, I read the center-temperature effect from the numerical difference because the curves can nearly overlap. The effect at the center is not automatically the same as the effect across the whole surrounding rock.

These results replace the earlier oversized-grid geometry results. The old values of 146.212°C and a 0.361°C difference are not used as results for the corrected geometry.

Differences between cases include physical advection and numerical effects from upwinding. Actual intrusion refinement results are stored in `results/summary.json`. I compare the grid sensitivity with the size of the flow effect.

'''),
('markdown', r'''## 7. Model limitations
I use fixed background flow. Temperature does not change density, viscosity, or permeability. I omit latent heat, water phase changes, and buoyancy-driven convection. This is an idealized model for understanding a mechanism, rather than a field prediction.

Material properties, porosity, permeability, and initial intrusion temperature match Table 2 of Fu et al. (2010). Rock conductivity of 2.5 W/(m K) is used as an effective saturated-rock approximation. Geometry, background temperature, duration, and head are my scenario choices. Full references are in the README.

## Where does this project end?
My final outputs are the three figures above, the comparison between cases, and verification in a separate notebook. The browser interface calls the same Python solver. No additional physical processes are needed to run this version.
'''),
]


VERIFICATION_CELLS = [
('markdown', r'''# Numerical Verification — Riski Basrin

## Why am I doing these checks?
I compare the numerical calculation with known answers. These tests use **the same functions as the application**, imported from `simulation.py`. There is no second matrix solver written only for verification.

## 1. Uniform temperature and groundwater flow
Set the entire domain to 100°C. The exact answer is that temperature remains 100°C. I also check intrusion area, inflow/outflow balance, and the absence of water flux through the intrusion.
'''),
('code', '''import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path
from checks import basic_checks, sine_test

print(basic_checks())
'''),
('markdown', r'''## 2. A case with an analytical solution
For this test, the material is homogeneous and there is no flow. All four boundaries remain at 100°C. The initial temperature is
$$
T(x,z,0)=T_b+100\sin(\pi x/L_x)\sin(\pi z/L_z).
$$
The analytical solution is
$$
T(x,z,t)=T_b+100\sin(\pi x/L_x)\sin(\pi z/L_z)
\exp[-\alpha\pi^2(L_x^{-2}+L_z^{-2})t],
\qquad \alpha=\lambda_h/C_h.
$$
The 100°C amplitude is deliberately chosen for a mathematical test. It is not a field observation or a replacement for the intrusion temperature.

Numerical and analytical parameters, initial conditions, and boundary conditions match. The comparison time is 1,000 years. `sine_test` calls `conduction_operator` and `prepare_conduction` from the application module.
'''),
('code', '''test = sine_test(spacing=20., dt_years=5.)
print("Maximum error:", test["max_error"], "°C")
print("RMSE:", test["rmse"], "°C")

j = len(test["x"]) // 2
fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
axes[0].plot(test["x"], test["exact"][j], "k-", label="Analytical")
axes[0].plot(test["x"][::5], test["numerical"][j, ::5], "ro", label="Numerical")
axes[0].set(xlabel="x (m)", ylabel="Temperature (°C)",
            title="Section near the center, 1,000 years")
axes[0].legend()
im = axes[1].imshow(test["error"], extent=[0, 2000, 2000, 0], cmap="RdBu_r")
axes[1].set(xlabel="x (m)", ylabel="Local z (m)", title="Numerical − analytical")
fig.colorbar(im, ax=axes[1], label="Error (°C)")
plt.show()
'''),
('markdown', '''## 3. What happens when I refine the grid?
I use dt = 5 years for all three grids. For smooth conduction in homogeneous material, I expect spatial error to decrease by approximately a factor of four when grid spacing is halved.
'''),
('code', '''spacings = [40., 20., 10.]
grid_errors = [sine_test(h, 5.)["max_error"] for h in spacings]
for h, error in zip(spacings, grid_errors):
    print(f"Grid {h:.0f} m | maximum error {error:.8f} °C")
print("Ratios:", np.array(grid_errors[:-1]) / grid_errors[1:])
fig, ax = plt.subplots(figsize=(6, 4))
ax.loglog(spacings, grid_errors, "o-", label="Numerical results")
ax.loglog(spacings, grid_errors[-1] * (np.array(spacings) / spacings[-1])**2,
          "k--", label="Second-order reference")
ax.set(xlabel="Grid spacing (m)", ylabel="Maximum error (°C)")
ax.legend(); ax.grid(alpha=.3)
plt.show()
'''),
('markdown', r'''## 4. What happens when I refine the time step?
Spatial error can hide temporal error. I therefore also compare with the exact decay of the **spatially discrete system** on a fixed square grid:
$$
\beta_h=\frac{8\alpha}{\Delta x^2}\sin^2\left(\frac{\pi\Delta x}{2L}\right),
\qquad T_h=T_b+100\sin(\pi x/L)\sin(\pi z/L)e^{-\beta_h t}.
$$
This additional reference isolates time error. The continuous PDE comparison remains above. Large time steps here are used only for the smooth conduction test, not for the intrusion project.
'''),
('code', '''steps = [500., 250., 125.]
time_errors = [sine_test(40., dt)["time_error"] for dt in steps]
for dt, error in zip(steps, time_errors):
    print(f"dt {dt:.0f} years | error against the semidiscrete system {error:.8f} °C")
print("Ratios:", np.array(time_errors[:-1]) / time_errors[1:])
fig, ax = plt.subplots(figsize=(6, 4))
ax.loglog(steps, time_errors, "o-")
ax.set(xlabel="Time step (years)", ylabel="Maximum temporal error (°C)")
ax.grid(alpha=.3)
plt.show()
'''),
('markdown', '''## 5. Check the actual intrusion model
The following table comes from repeated intrusion runs with the same geometry: a 20 m grid, half the time step on that grid, and a 10 m grid. `build_deliverables.py --recompute` recalculates this table by calling `run_pair` from the application solver.

This checks sensitivity. It does not provide an analytical solution for the intrusion.
'''),
('code', '''summary = json.loads(Path("results/summary.json").read_text())
print("Case | center without flow | center with flow | difference (°C)")
for name, item in summary.items():
    print(name, item["center_no_flow"], item["center_flow"], item["delta"])
delta = summary["grid_20m"]["delta"]
print("Change in the difference from dt/2:",
      abs(summary["grid_20m_dt_half"]["delta"]-delta), "°C")
print("Change in the difference from the 10 m grid:",
      abs(summary["grid_10m"]["delta"]-delta), "°C")
'''),
('markdown', '''## 6. What can I conclude?
The sinusoidal test checks homogeneous conduction using the same implementation as the application. Error ratios near four support second-order convergence for that smooth test. Uniform temperature and flow balance check basic states, but do not establish full advection accuracy.

Material interfaces, upwind advection, and sequential conduction–advection splitting introduce additional errors. A small difference between cases must be interpreted together with grid sensitivity. Two intrusion resolutions alone do not demonstrate asymptotic convergence or a definitive physical effect.

Heat can leave through the fixed-temperature boundaries, so total heat inside the domain is not expected to remain constant.
''')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recompute', action='store_true',
                        help='Recalculate every intrusion scenario rather than reuse computed examples.')
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.recompute:
        print('Recomputing the default intrusion and refinement cases…', flush=True)
        r = run_pair(Parameters())
        half = run_pair(Parameters(), dt_scale=.5)
        fine = run_pair(Parameters(spacing=10.))
        summary = {}
        for key, item in [('grid_20m', r), ('grid_20m_dt_half', half), ('grid_10m', fine)]:
            summary[key] = {k: plain(item[k]) for k in
                            ['dt_years', 'n_steps', 'effective_area', 'max_flow_divergence',
                             'max_final_map_difference']}
            summary[key].update(center_flow=float(item['center_flow'][-1]),
                                center_no_flow=float(item['center_no_flow'][-1]),
                                delta=float(item['center_no_flow'][-1]-item['center_flow'][-1]))
        (ROOT / 'results/summary.json').write_text(json.dumps(summary, indent=2))
        (ROOT / 'results/example.json').write_text(
            json.dumps({k: plain(v) for k, v in r.items()}, allow_nan=True).replace('NaN', 'null'))
    else:
        print('Reusing saved refinement summaries; rerunning the default intrusion and analytical checks.', flush=True)
        saved = json.loads((ROOT / 'results/example.json').read_text())
        r = {key: np.asarray(value) if isinstance(value, list) else value
             for key, value in saved.items()}
        # JSON null denotes head inside the intrusion; use NaN for plotting.
        r['head'] = np.asarray(saved['head'], dtype=float)

    # Execute the project notebook normally so every saved output matches its code.
    write_notebook('Intrusion_2D_Project.ipynb', PROJECT_CELLS)
    figures = plot_results(r)
    for figure, name in zip(figures, ['flow', 'temperature_maps', 'cooling_curves']):
        figure.savefig(ROOT / f'results/{name}.png', dpi=130, bbox_inches='tight')
    plt.close('all')
    write_notebook('Verification.ipynb', VERIFICATION_CELLS)
    finalize()
    print('English notebooks and figures completed.', flush=True)


if __name__ == '__main__':
    main()
