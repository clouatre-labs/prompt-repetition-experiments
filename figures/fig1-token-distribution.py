import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Data
labels = ["Exp1\nControl", "Exp1\nTreatment", "Exp2\nControl", "Exp2\nTreatment"]
values = [1068182, 732257, 740362, 737331]
colors = ["#1f77b4", "#ff7f0e", "#1f77b4", "#ff7f0e"]

fig, ax = plt.subplots(figsize=(9, 5))

bars = ax.bar(range(4), values, color=colors, width=0.6, zorder=3)

# Y-axis label and title
ax.set_ylabel("Mean total tokens (valid runs)", fontsize=11)
ax.set_title("Token usage by group -- Exp1 (FastMCP refactor) and Exp2 (tree-sitter synthesis)", fontsize=12)
# Y limits and grid
ax.set_ylim(0, 1.3e6)
ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
ax.set_axisbelow(True)
# X ticks
ax.set_xticks(range(4))
ax.set_xticklabels(labels, fontsize=10)

# Value labels on bars
for i, bar in enumerate(bars):
    v = values[i]
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20000,
            f"{v/1e6:.2f}M", ha="center", va="bottom", fontsize=10, fontweight="bold")

# Delta annotations (treatment bars)
# Exp1 Treatment (index 1)
ax.text(1, values[1] + 50000, "-31.4% vs control", ha="center", va="bottom", fontsize=9, color="#555555")
# Exp2 Treatment (index 3)
ax.text(3, values[3] + 50000, "-0.4% vs control", ha="center", va="bottom", fontsize=9, color="#555555")

# Reference lines
ax.axhline(1068182, color="#1f77b4", linestyle="--", linewidth=1, alpha=0.5)
ax.axhline(740362, color="#1f77b4", linestyle=":", linewidth=1, alpha=0.5)

# Legend using Line2D squares
legend_elements = [
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#1f77b4', markersize=9, label='Control'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#ff7f0e', markersize=9, label='Treatment')
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

plt.tight_layout()
plt.savefig('figures/fig1-token-distribution.png', dpi=150, bbox_inches='tight')
print('Saved figures/fig1-token-distribution.png')