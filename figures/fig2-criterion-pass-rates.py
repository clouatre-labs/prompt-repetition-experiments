import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Data
criteria = ["C1", "C2", "C3", "C4", "C5", "C6"]
rates = [1.0, 1.0, 1.0, 1.0, 0.67, 1.0]
colors = ["#2ca02c", "#2ca02c", "#2ca02c", "#2ca02c", "#d62728", "#2ca02c"]

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(range(6), rates, color=colors, width=0.6, zorder=3)

# Axis labels and title
ax.set_ylabel('Pass rate', fontsize=11)
ax.set_title('Criterion pass rates -- FastMCP refactor (n=9 valid runs)', fontsize=12)
ax.set_ylim(0, 1.15)
ax.yaxis.grid(True, linestyle='--', alpha=0.4, zorder=0)
ax.set_axisbelow(True)
# X ticks
ax.set_xticks(range(6))
ax.set_xticklabels(criteria, fontsize=11)

# Value labels on bars
for i, bar in enumerate(bars):
    r = rates[i]
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
            f"{r:.0%}", ha='center', va='bottom', fontsize=10, fontweight='bold')

# Legend
legend_elements = [
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#2ca02c', markersize=9, label='Pass (100%)'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#d62728', markersize=9, label='Partial')
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

plt.tight_layout()
plt.savefig('figures/fig2-criterion-pass-rates.png', dpi=150, bbox_inches='tight')
print('Saved figures/fig2-criterion-pass-rates.png')