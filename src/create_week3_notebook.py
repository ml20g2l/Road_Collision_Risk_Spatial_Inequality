"""Create exposure sensitivity and Power BI semantic-model notebook."""

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
nb = nbf.v4.new_notebook()
nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb["cells"] = [
    nbf.v4.new_markdown_cell(
        """# Exposure Sensitivity & Power BI Model\n\n## tl;dr\n\n- Local-authority vehicle miles cover 99.98% of collisions and support absolute risk rates.\n- The AADF 100-metre sample covers about 11% of numbered-road collisions, while the Counted-only sample covers about 3%; both are therefore limited to sensitivity diagnostics.\n- Injury-based reporting adjustment raises the KSI rate by 6.0% in 2021 and 2.1% in 2025.\n- The 2025 Spearman correlation between raw and adjusted local-authority risk ranks is about 0.991: the broad spatial pattern is stable, although metric levels change."""
    ),
    nbf.v4.new_markdown_cell(
        """## Context & Methods\n\n### Key Assumptions\n\n- Only DfT annual vehicle miles are used as the denominator for absolute risk rates.\n- Adjusted expected KSI adds the DfT probability-based serious-injury estimate to fatal collisions.\n- AADF analysis compares sample coverage under same-year, same-road, and distance-threshold rules.\n- AADF geometry represents count points, so it is not treated as full road-link exposure."""
    ),
    nbf.v4.new_code_cell(
        """from pathlib import Path\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom scipy.stats import spearmanr\nROOT=Path.cwd()\nplt.rcParams.update({'figure.figsize':(9,5),'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2,'font.size':10})\nBLUE='#2563EB'; ORANGE='#D97706'; GREY='#6B7280'"""
    ),
    nbf.v4.new_markdown_cell("## Data"),
    nbf.v4.new_code_cell(
        """risk=pd.read_parquet(ROOT/'data/powerbi/fact_local_authority_year_risk.parquet')\nsensitivity=pd.read_parquet(ROOT/'data/powerbi/fact_exposure_sensitivity.parquet')\n{'risk_rows':len(risk),'sensitivity_rows':len(sensitivity),'years':sorted(risk.collision_year.unique())}"""
    ),
    nbf.v4.new_markdown_cell("## Results\n\n### 1. Raw vs adjusted KSI rate"),
    nbf.v4.new_code_cell(
        """covered=risk[risk.exposure_available]\nannual=covered.groupby('collision_year').agg(raw_ksi=('raw_ksi','sum'),adjusted_ksi=('adjusted_expected_ksi','sum'),vehicle_miles=('annual_vehicle_miles','sum')).reset_index()\nannual['raw_rate']=annual.raw_ksi/annual.vehicle_miles*1e9\nannual['adjusted_rate']=annual.adjusted_ksi/annual.vehicle_miles*1e9\nannual['adjustment_pct']=(annual.adjusted_rate/annual.raw_rate-1)*100\nannual.round(2)"""
    ),
    nbf.v4.new_code_cell(
        """ax=annual.plot(x='collision_year',y=['raw_rate','adjusted_rate'],marker='o',color=[GREY,BLUE])\nax.set(title='KSI collisions per billion vehicle miles',xlabel='Collision year',ylabel='KSI per billion vehicle miles',xticks=annual.collision_year)\nax.legend(['Raw reported severity','Adjusted expected severity'],frameon=False)\nplt.tight_layout(); plt.show()"""
    ),
    nbf.v4.new_markdown_cell("### 2. Exposure scenario coverage"),
    nbf.v4.new_code_cell(
        """plot=sensitivity[sensitivity.scenario_key!='la_vehicle_miles'].pivot(index='collision_year',columns='scenario_key',values='coverage_rate')\nax=plot.plot(marker='o',color=[BLUE,ORANGE,'#9CA3AF'])\nax.set(title='AADF sensitivity sample coverage',xlabel='Collision year',ylabel='Coverage of numbered-road collisions',ylim=(0,.3),xticks=plot.index)\nax.yaxis.set_major_formatter(lambda x,pos:f'{x:.0%}')\nax.legend(['AADF <=100m, all','AADF <=100m, Counted','AADF <=250m, all'],frameon=False)\nplt.tight_layout(); plt.show()"""
    ),
    nbf.v4.new_markdown_cell("### 3. Local-authority ranking stability"),
    nbf.v4.new_code_cell(
        """latest=covered[covered.collision_year==2025].copy()\nrho=spearmanr(latest.raw_ksi_per_billion_vehicle_miles,latest.adjusted_ksi_per_billion_vehicle_miles).statistic\nax=latest.plot.scatter(x='raw_ksi_per_billion_vehicle_miles',y='adjusted_ksi_per_billion_vehicle_miles',color=BLUE,alpha=.55)\nlo=min(ax.get_xlim()[0],ax.get_ylim()[0]); hi=max(ax.get_xlim()[1],ax.get_ylim()[1]); ax.plot([lo,hi],[lo,hi],color=GREY,linestyle='--')\nax.set(title=f'2025 local-authority KSI risk: raw vs adjusted (Spearman {rho:.3f})',xlabel='Raw KSI per billion vehicle miles',ylabel='Adjusted expected KSI per billion vehicle miles')\nplt.tight_layout(); plt.show()\n{'authorities':len(latest),'spearman_rank_correlation':round(rho,4)}"""
    ),
    nbf.v4.new_markdown_cell(
        """## Takeaways\n\n1. The Power BI model provides raw and adjusted KSI rates based on local-authority vehicle miles.\n2. The adjusted metric is the default comparison measure, with the raw metric retained for transparency and sensitivity checks.\n3. AADF contributes sample-coverage and quality flags only; no absolute link-level risk measure is created before road-segment geometry is available.\n4. The star schema contains `fact_collision`, `fact_local_authority_year_risk`, `fact_exposure_sensitivity`, and conformed date, LSOA, local-authority, and scenario dimensions."""
    ),
]
out = ROOT / "notebooks/03_exposure_sensitivity_powerbi_model.ipynb"
nbf.write(nb, out)
print("created notebook")
