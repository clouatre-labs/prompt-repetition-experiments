import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

analysis_path = os.path.join('experiments', 'exp1-fastmcp-refactor', 'analysis.json')

with open(analysis_path, 'r') as f:
    data = json.load(f)

criterion_data = data['criterion_pass_rates']
labels = []
rates = []
err_low = []
err_high = []
colors = []
for crit_key in sorted(criterion_data.keys()):
    crit = criterion_data[crit_key]
    labels.append(crit_key)
    rate = crit['pass_rate']
    rates.append(rate)
    low = crit['wilson_low']
    high = crit['wilson_high']
    err_low.append(rate - low)
    err_high.append(high - rate)
    # color green for perfect, orange otherwise
    colors.append('#2ca02c' if rate == 1.0 else '#ff7f0e')

fig, ax = plt.subplots(figsize=(8, 6))

bars = ax.bar(labels, rates, color=colors, edgecolor='black')
# add error bars
ax.errorbar(labels, rates, yerr=[err_low, err_high], fmt='none', ecolor='black', capsize=5)

ax.set_ylabel('Pass rate (0-1)')
ax.set_ylim(0, 1.15)
ax.set_title('Exp1 criterion pass rates with 95% Wilson CIs')
# annotation for Exp2 ceiling effect
ax.text(0.5, 1.05, 'Exp2: All 7 criteria at 100% pass rate (ceiling effect, n=10)',
        transform=ax.transAxes, ha='center', va='center')

plt.tight_layout()
out_path = os.path.join('figures', 'fig2-criterion-pass-rates.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight')
