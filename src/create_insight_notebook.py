"""Create the public decision-focused insight notebook."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
nb = nbf.v4.new_notebook()
nb["metadata"]["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb["cells"] = [
    nbf.v4.new_markdown_cell("""# Road Collision Risk & Spatial Inequality — Decision Analysis

## tl;dr

Collision burden is approximately twice as high in the most deprived English neighbourhoods as in the least deprived, and the gap persists in every study year. This inequality is driven more by collision occurrence than by conditional severity. Rural collisions form a separate high-severity problem, so urban inequality and rural severity should not be collapsed into one intervention ranking."""),
    nbf.v4.new_markdown_cell("""## Context & Methods

- Resident-normalised rates describe community burden, not road-use exposure.
- Adjusted expected KSI accounts for changes associated with injury-based reporting.
- Results are descriptive associations and do not establish causality.
- Small-area comparisons should be accompanied by uncertainty and disclosure controls before operational use."""),
    nbf.v4.new_code_cell("""from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
PUBLIC = ROOT / 'data' / 'public'
plt.rcParams.update({'figure.figsize': (9, 5), 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': .2, 'font.size': 10})
BLUE = '#2563EB'; ORANGE = '#D97706'; GREY = '#6B7280'"""),
    nbf.v4.new_markdown_cell("""## 1. Persistent deprivation gap

The chart uses a fixed mid-2022 resident population as a contextual denominator across the five study years. Decile 1 is the most deprived and decile 10 the least deprived."""),
    nbf.v4.new_code_cell("""deprivation = pd.read_csv(PUBLIC / 'deprivation_decile_summary.csv')
deprivation['imd_decile'] = deprivation.imd_decile.astype(int)
ax = deprivation.plot.bar(x='imd_decile', y='collisions_per_100k_resident_years', color=BLUE, legend=False)
ax.set(title='Collision burden falls sharply in less deprived areas', xlabel='Index of Multiple Deprivation decile (1 = most deprived)', ylabel='Collisions per 100,000 residents per year')
plt.tight_layout(); plt.show()
deprivation.round(2)"""),
    nbf.v4.new_code_cell("""gap = pd.read_csv(PUBLIC / 'deprivation_gap_by_year.csv')
ax = gap.plot(x='collision_year', y='most_to_least_ratio', marker='o', color=ORANGE, legend=False)
ax.axhline(1, color=GREY, linestyle='--', linewidth=1)
ax.set(title='The deprivation gap persists in every year', xlabel='Collision year', ylabel='Most-to-least-deprived rate ratio', xticks=gap.collision_year, ylim=(0, 2.4))
plt.tight_layout(); plt.show()
gap.round(2)"""),
    nbf.v4.new_markdown_cell("""## 2. Rural collisions have greater conditional severity

This comparison asks how severe collisions are after they occur. It does not compare exposure-adjusted collision frequency."""),
    nbf.v4.new_code_cell("""area = pd.read_csv(PUBLIC / 'severity_by_urban_rural.csv')
latest = area[(area.collision_year == area.collision_year.max()) & area.area_type.isin(['Urban', 'Rural'])]
ax = latest.plot.bar(x='area_type', y='adjusted_ksi_per_100_collisions', color=[BLUE, ORANGE], legend=False, rot=0)
ax.set(title='Rural collisions were more severe in 2025', xlabel='', ylabel='Adjusted expected KSI per 100 collisions')
plt.tight_layout(); plt.show()
latest.round(2)"""),
    nbf.v4.new_markdown_cell("""## 3. Speed environment requires contextual interpretation

The relationship is not monotonic: 70 mph roads have lower conditional severity than 60 mph roads. This pattern is consistent with road design and traffic separation acting alongside speed, but it does not identify their causal effects."""),
    nbf.v4.new_code_cell("""speed = pd.read_csv(PUBLIC / 'severity_by_speed_limit.csv')
ax = speed.plot.bar(x='speed_limit', y='adjusted_ksi_per_100_collisions', color=BLUE, legend=False, rot=0)
ax.set(title='Conditional severity peaks on 60 mph roads', xlabel='Speed limit (mph)', ylabel='Adjusted expected KSI per 100 collisions')
plt.tight_layout(); plt.show()
speed.round(2)"""),
    nbf.v4.new_markdown_cell("""## Decision implications

1. Prioritise deprived urban communities for collision-occurrence diagnosis and place-based prevention.
2. Treat rural severity as a separate intervention track focused on road geometry, speed environment, emergency response, and collision type.
3. Use adjusted KSI per billion vehicle miles for local-authority risk comparisons; keep the raw measure visible for transparency.
4. Do not use the resident-normalised deprivation result as an exposure-adjusted road-risk measure.
5. Extend the analysis with road segment geometry and multivariable modelling before making causal or site-specific investment claims.""")
]

out = ROOT / "notebooks" / "04_decision_insights.ipynb"
nbf.write(nb, out)
print("Created the decision-insight notebook")
