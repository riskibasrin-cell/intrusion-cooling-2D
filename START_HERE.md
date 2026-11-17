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

## What remains before submission?

1. Upload the project contents to GitHub and enable GitHub Pages through GitHub Actions. See the README.
2. Test the browser application, including a new simulation and the animation. Direct browser testing has not been completed because the development preview browser could not reach the session's local server. Python outputs and JavaScript syntax have been checked.
3. Study the simulation code and verification notebook for an independent presentation.

This session is not connected to a GitHub account. There is no verified public application URL yet, so this package alone is not a complete final submission.

**No additional physical processes or new scenarios are needed to complete this version.**
