# Package check

This edition separates all seven numbered project sections into their own Markdown cells.

| Section | Contents | Following code |
|---|---|---|
| 1 | Define where the process takes place | Parameters and grid |
| 2 | Equations and boundary conditions | Initial temperature and material properties |
| 3 | How do I calculate it? | Flow solution, conduction operator, and time-step estimate |
| 4 | Run the two cases | Full with-flow and no-flow simulation through `run_pair(p)` |
| 5 | Look at the results | Three main figures |
| 6 | Discussion | Interpretation; no calculation cell needed |
| 7 | Model limitations | Assumptions and limitations; no calculation cell needed |

Both notebooks were executed successfully, with six saved figures in total. Supporting Python modules, interface files, numerical examples, references, dependencies, and the GitHub Pages workflow are included.

The solver functions remain in `simulation.py`, as required for reuse by the application and verification. Code cells in the project notebook call those shared functions. They are not missing implementations.

The application is deployed on GitHub Pages. Basic browser testing has been completed, including fresh simulations, case switching, temperature animation, and CSV export. Numerical limitations and grid sensitivity remain documented in `Verification.ipynb`.
