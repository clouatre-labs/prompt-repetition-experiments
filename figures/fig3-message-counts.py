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

# Value labels and delta annotations
for i, bar in enumerate(bars):
    v = values_sorted[i]
    label = f"{v:.1f}"
    if i < 2:  # treatment bars
        delta = "-34.2% vs ctrl" if i == 0 else "-8.6% vs ctrl"
        label = f"{label}  ({delta})"
        color = "#555555"
    else:
        color = "black"
    ax.text(v + 3, bar.get_y() + bar.get_height() / 2, label, va='center', fontsize=10, color=color)

# Annotation for Exp1 control note
ax.annotate('Exp1 control: 1 drift run excluded (93 msgs)', xy=(209.25, 3), xytext=(130, 3.35),
            fontsize=8, color='#888888', arrowprops=dict(arrowstyle='->', color='#888888', lw=0.8))

# Legend
legend_elements = [
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#1f77b4', markersize=9, label='Control'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#ff7f0e', markersize=9, label='Treatment')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

plt.tight_layout()
plt.savefig('figures/fig3-message-counts.png', dpi=150, bbox_inches='tight')
print('Saved figures/fig3-message-counts.png')