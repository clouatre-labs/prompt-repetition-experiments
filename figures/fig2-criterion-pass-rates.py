import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Exp1 data
criteria_exp1 = ["C1", "C2", "C3", "C4", "C5", "C6"]
rates_exp1 = [1.0, 1.0, 1.0, 1.0, 0.67, 1.0]
colors_exp1 = ["#2ca02c", "#2ca02c", "#2ca02c", "#2ca02c", "#1f77b4", "#2ca02c"]

# Exp2 data -- complete ceiling, all 7 criteria at 100%
criteria_exp2 = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
rates_exp2 = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
colors_exp2 = ["#2ca02c"] * 7

# Exp3 data
criteria_exp3 = ["C1\u2020", "C2", "C3", "C4", "C5\u2020", "C6\u2020", "C7"]
rates_exp3 = [0.0, 0.10, 0.80, 0.30, 0.0, 0.0, 1.0]
colors_exp3 = ["#aaaaaa", "#9467bd", "#2ca02c", "#9467bd", "#aaaaaa", "#aaaaaa", "#2ca02c"]

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 13))

# Panel 1: Exp1
bars1 = ax1.bar(range(6), rates_exp1, color=colors_exp1, width=0.6, zorder=3)
ax1.set_ylabel('Pass rate', fontsize=11)
ax1.set_title('Exp1: FastMCP refactor (n=9 valid runs)', fontsize=11)
ax1.set_ylim(0, 1.15)
ax1.yaxis.grid(True, linestyle='--', alpha=0.4, zorder=0)
ax1.set_axisbelow(True)
ax1.set_xticks(range(6))
ax1.set_xticklabels(criteria_exp1, fontsize=10)
for i, bar in enumerate(bars1):
    r = rates_exp1[i]
    ax1.text(bar.get_x() + bar.get_width() / 2, r + 0.02,
             f"{r:.0%}", ha='center', va='bottom', fontsize=10, fontweight='bold')

# Panel 2: Exp2
bars2 = ax2.bar(range(7), rates_exp2, color=colors_exp2, width=0.6, zorder=3)
ax2.set_ylabel('Pass rate', fontsize=11)
ax2.set_title('Exp2: Tree-sitter AST scanner (n=10) -- complete ceiling', fontsize=11)
ax2.set_ylim(0, 1.15)
ax2.yaxis.grid(True, linestyle='--', alpha=0.4, zorder=0)
ax2.set_axisbelow(True)
ax2.set_xticks(range(7))
ax2.set_xticklabels(criteria_exp2, fontsize=10)
for i, bar in enumerate(bars2):
    r = rates_exp2[i]
    ax2.text(bar.get_x() + bar.get_width() / 2, r + 0.02,
             f"{r:.0%}", ha='center', va='bottom', fontsize=10, fontweight='bold')

# Panel 3: Exp3
bars3 = ax3.bar(range(7), rates_exp3, color=colors_exp3, width=0.6, zorder=3)
ax3.set_ylabel('Pass rate', fontsize=11)
ax3.set_title('Exp3: Kotlin grammar synthesis (n=10)', fontsize=11)
ax3.set_ylim(0, 1.15)
ax3.yaxis.grid(True, linestyle='--', alpha=0.4, zorder=0)
ax3.set_axisbelow(True)
ax3.set_xticks(range(7))
ax3.set_xticklabels(criteria_exp3, fontsize=10)
for i, bar in enumerate(bars3):
    r = rates_exp3[i]
    ax3.text(bar.get_x() + bar.get_width() / 2, r + 0.02,
             f"{r:.0%}", ha='center', va='bottom', fontsize=10, fontweight='bold')
ax3.text(0.01, -0.12, '\u2020 Structurally excluded (rubric-runner misalignment; 0/10 both groups)',
         transform=ax3.transAxes, fontsize=9, style='italic')

fig.suptitle('Criterion pass rates by experiment', fontsize=13, fontweight='bold')
plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig('figures/fig2-criterion-pass-rates.png', dpi=300, bbox_inches='tight')
print('Saved figures/fig2-criterion-pass-rates.png')
