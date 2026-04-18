import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Criterion pass rates read from analysis.json for both experiments.
# Exp1: C1-C6 (9 valid runs, control-1 drift excluded).
# Exp2: C1-C7 (10 runs, all valid -- ceiling effect).
# Exp1 has no C7; represented as NaN and rendered as a hatched N/A cell.

criteria = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']

rows = [
    'Exp1: FastMCP refactor\n(n=9 valid)',
    'Exp2: Tree-sitter synthesis\n(n=10)',
]

data = np.array([
    [1.0,  1.0,  1.0,  1.0,  0.67, 1.0,  np.nan],  # Exp1 C1-C6; C7 N/A
    [1.0,  1.0,  1.0,  1.0,  1.0,  1.0,  1.0   ],  # Exp2 C1-C7
])

fig, ax = plt.subplots(figsize=(9, 3))

# Mask NaN for imshow
masked = np.ma.masked_invalid(data)
cmap = plt.get_cmap('RdYlGn')
cmap.set_bad('#cccccc')
im = ax.imshow(masked, cmap=cmap, vmin=0, vmax=1, aspect='auto')

ax.set_xticks(range(len(criteria)))
ax.set_xticklabels(criteria, fontsize=11)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels(rows, fontsize=10)
ax.set_xlabel('Criterion', fontsize=11)

# Cell annotations
for i in range(len(rows)):
    for j in range(len(criteria)):
        val = data[i, j]
        if np.isnan(val):
            # Hatch over the grey bad-color cell
            ax.add_patch(mpatches.Rectangle(
                (j - 0.5, i - 0.5), 1, 1,
                fill=True, facecolor='#cccccc', edgecolor='black', hatch='//', linewidth=0
            ))
            ax.text(j, i, 'N/A', ha='center', va='center', fontsize=10, color='black')
        else:
            text_color = 'white' if val < 0.4 else 'black'
            ax.text(j, i, f'{val:.0%}', ha='center', va='center',
                    fontsize=11, color=text_color, fontweight='bold')

plt.colorbar(im, ax=ax, label='Pass rate (0.0 = never, 1.0 = always)', shrink=0.8)

ax.set_title('Criterion pass rates by experiment', fontsize=12, pad=10)

fig.text(
    0.5, -0.06,
    'Exp1 C5: 67% [35\u201388% Wilson CI]. All other non-N/A cells: 100% [\u226570% Wilson lower bound].',
    ha='center', fontsize=9, style='italic'
)

plt.tight_layout()
plt.savefig('figures/fig2-criterion-pass-rates.png', dpi=150, bbox_inches='tight')
print('Saved figures/fig2-criterion-pass-rates.png')
