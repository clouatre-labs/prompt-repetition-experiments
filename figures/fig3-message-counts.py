import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Sorted data
labels_sorted = ["Exp1\nTreatment", "Exp2\nTreatment", "Exp2\nControl", "Exp1\nControl"]
values_sorted = [137.6, 138.6, 151.6, 209.25]
colors_sorted = ["#ff7f0e", "#ff7f0e", "#1f77b4", "#1f77b4"]

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.barh(range(4), values_sorted, color=colors_sorted, height=0.6)

# Axis labels and title
ax.set_xlabel('Mean messages per run (valid runs)', fontsize=11)
ax.set_title('Message count by group -- Exp1 (FastMCP refactor) and Exp2 (tree-sitter synthesis)', fontsize=12)
ax.set_xlim(0, 260)
ax.xaxis.grid(True, linestyle='--', alpha=0.4, zorder=0)
ax.set_axisbelow(True)

# Y ticks
ax.set_yticks(range(4))
ax.set_yticklabels(labels_sorted, fontsize=10)

# Value labels
for i, bar in enumerate(bars):
    v = values_sorted[i]
    ax.text(v + 3, bar.get_y() + bar.get_height() / 2, f"{v:.1f}", va='center', fontsize=10)

# Legend
legend_elements = [
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#1f77b4', markersize=9, label='Control'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#ff7f0e', markersize=9, label='Treatment')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

plt.tight_layout()
plt.savefig('figures/fig3-message-counts.png', dpi=150, bbox_inches='tight')
print('Saved figures/fig3-message-counts.png')