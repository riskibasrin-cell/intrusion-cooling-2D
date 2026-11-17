## Final results and how I read them

At 5,000 years, the results for an exact 200 × 400 m intrusion are:

| Check | Center without flow (°C) | Center with flow (°C) | Difference (°C) |
|---|---:|---:|---:|
| 20 m grid | 140.416354 | 140.080860 | 0.335494 |
| 20 m grid, dt/2 | 140.416354 | 140.080831 | 0.335523 |
| 10 m grid | 140.413347 | 140.131174 | 0.282174 |

Halving dt on the same grid changes the difference between the cases by 0.000029°C. Refining the grid from 20 m to 10 m changes that difference by 0.053321°C, approximately 15.9% of the 20 m result. On the 10 m grid, dt is also adjusted using the same selection rule.

At both tested resolutions, the center is slightly cooler with flow, and the cooling curves nearly overlap. I do not claim that a particular difference is a converged physical effect. Upwind advection adds numerical diffusion.

The effect in the surrounding rock is different from the center effect. The largest difference between the final maps is approximately 2.838°C on the 20 m grid and 2.830°C on the 10 m grid. This compares the two cases; it is not an error against an exact solution.
