# Start here, Riski

**Open `Intrusion_2D_Project.ipynb` first.** It already contains the computed results, so you do not need to run everything immediately.

The explanations remain simple and step by step, now entirely in English. Arrays still use `T[j, i]`. Keep the notebook and Python modules together after extracting this ZIP.

## Project notebook sections

Sections 1–7 are separate Markdown cells. Sections 1–5 each have their own following code cell. Section 4 runs both simulations. See `PACKAGE_CHECK.md` for the checked contents.

## What has been organized?

- Exact intrusion dimensions of 200 × 400 m, with an area of 80,000 m².
- Identical initial conditions for the two flow cases.
- Three main plots, regenerated with English labels.
- Separate simulation and interface code.
- A verification notebook using the same solver as the application.
- Material parameters checked against Table 2 of Fu et al. (2010).
- Browser controls, animation, CSV export, and GitHub Actions deployment files.

This ZIP includes only the English project files. It does not include the earlier Indonesian archive.

## What do the results show?

At 5,000 years, the 20 m grid gives a center temperature of approximately 140.081°C with flow and 140.416°C without flow. The difference is approximately 0.335°C. On the 10 m grid, the difference is approximately 0.282°C. The center effect is small, and its precise magnitude is still grid-sensitive.

These results replace the earlier oversized-grid geometry results. Both notebooks explain the interpretation and its limits.

## Current status

The application is deployed on GitHub Pages:

[Open the interactive simulation](https://riskibasrin-cell.github.io/intrusion-cooling-2D/)

The saved example, fresh simulations, case switching, temperature animation, and CSV download have been tested.

Both notebooks have been rerun successfully from the GitHub repository. The small center-temperature difference remains grid-sensitive, as explained in `Verification.ipynb`.

## What remains before submission?

1. Study the simulation code and verification notebook.
2. Practice explaining the physics, numerical methods, results, and limitations independently.
3. Prepare the software demonstration and submit the required links.

No additional physical processes are required for the current project scope.
