import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

# Data: Exp1, Exp2, Exp3 (paper.tex Table 3)
exp_labels = ["Exp1\nFastMCP", "Exp2\nTree-sitter", "Exp3\nKotlin"]
control_values = [1032363, 703993, 41570]
treatment_values = [716275, 755029, 50418]

fig, ax = plt.subplots(figsize=(10, 5))

x = np.arange(len(exp_labels))
bar_width = 0.35
offset = 0.2

bars_control = ax.bar(x - offset, control_values, bar_width, label='Control', color='#1f77b4', zorder=3)
bars_treatment = ax.bar(x + offset, treatment_values, bar_width, label='Treatment', color='#ff7f0e', zorder=3)

ax.set_ylabel('Mean total tokens (valid runs)', fontsize=11)
ax.set_title('Token usage by group -- all three experiments', fontsize=12)
ax.set_ylim(0, 1.25e6)
ax.yaxis.grid(True, linestyle='--', alpha=0.4, zorder=0)
ax.set_axisbelow(True)

ax.set_xticks(x)
ax.set_xticklabels(exp_labels, fontsize=10)

def format_value(v):
    if v >= 1e6:
        return f"{v/1e6:.2f}M"
    elif v >= 1e3:
        return f"{v/1e3:.0f}K"
    else:
        return f"{v:.0f}"

for bar in bars_control:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height + 18000,
            format_value(height), ha='center', va='bottom', fontsize=9, fontweight='bold')

for bar in bars_treatment:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height + 18000,
            format_value(height), ha='center', va='bottom', fontsize=9, fontweight='bold')

legend_elements = [
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#1f77b4', markersize=9, label='Control'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#ff7f0e', markersize=9, label='Treatment')
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

plt.tight_layout()
plt.savefig('figures/fig1-token-distribution.png', dpi=150, bbox_inches='tight')
print('Saved figures/fig1-token-distribution.png')
