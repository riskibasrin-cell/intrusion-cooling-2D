"""Update the interpretation from computed results without rerunning the solver."""
from pathlib import Path
import json


def finalize():
    root = Path(__file__).resolve().parent
    summary = json.loads((root / 'results/summary.json').read_text())
    base = summary['grid_20m']
    half = summary['grid_20m_dt_half']
    fine = summary['grid_10m']
    text = '''## Final results and how I read them

At 5,000 years, the results for an exact 200 × 400 m intrusion are:

| Check | Center without flow (°C) | Center with flow (°C) | Difference (°C) |
|---|---:|---:|---:|
'''
    for label, r in [('20 m grid', base), ('20 m grid, dt/2', half), ('10 m grid', fine)]:
        text += f"| {label} | {r['center_no_flow']:.6f} | {r['center_flow']:.6f} | {r['delta']:.6f} |\n"
    text += f'''
Halving dt on the same grid changes the difference between the cases by {abs(half['delta']-base['delta']):.6f}°C. Refining the grid from 20 m to 10 m changes that difference by {abs(fine['delta']-base['delta']):.6f}°C, approximately {100*abs(fine['delta']-base['delta'])/abs(base['delta']):.1f}% of the 20 m result. On the 10 m grid, dt is also adjusted using the same selection rule.

At both tested resolutions, the center is slightly cooler with flow, and the cooling curves nearly overlap. I do not claim that a particular difference is a converged physical effect. Upwind advection adds numerical diffusion.

The effect in the surrounding rock is different from the center effect. The largest difference between the final maps is approximately {base['max_final_map_difference']:.3f}°C on the 20 m grid and {fine['max_final_map_difference']:.3f}°C on the 10 m grid. This compares the two cases; it is not an error against an exact solution.
'''
    for name in ['Intrusion_2D_Project.ipynb', 'Verification.ipynb']:
        path = root / name
        notebook = json.loads(path.read_text())
        notebook['cells'] = [c for c in notebook['cells']
                            if not ''.join(c['source']).startswith('## Final results and how I read them')]
        notebook['cells'].append({'cell_type': 'markdown', 'metadata': {},
                                  'source': text.splitlines(True)})
        for i, cell in enumerate(notebook['cells']):
            cell['id'] = f'cell-{i:03d}'
        path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1))
    (root / 'results/interpretation.md').write_text(text)


if __name__ == '__main__':
    finalize()
