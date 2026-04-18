import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Paths relative to repo root (worktree root)
exp1_path = os.path.join('experiments', 'exp1-fastmcp-refactor', 'efficiency.json')
exp2_path = os.path.join('experiments', 'exp2-treesitter-synthesis', 'efficiency.json')


def load_tokens(path):
    with open(path, 'r') as f:
        data = json.load(f)
    # data['runs'] is a list of run dicts
    control = []
    treatment = []
    for run in data['runs']:
        # treat missing valid as True
        if run.get('valid', True) is False:
            continue
        if run['group'] == 'control':
            control.append(run['total_tokens'])
        elif run['group'] == 'treatment':
            treatment.append(run['total_tokens'])
    return control, treatment

ctrl1, treat1 = load_tokens(exp1_path)
ctrl2, treat2 = load_tokens(exp2_path)

# Prepare plot
fig, axs = plt.subplots(1, 2, figsize=(10, 5), sharey=True)

# Settings
colors = {'control': '#1f77b4', 'treatment': '#ff7f0e'}

# Helper to plot strip

def plot_strip(ax, ctrl, treat, title):
    # jitter
    jitter = 0.05
    # positions
    x_ctrl = np.random.normal(0, jitter, size=len(ctrl))
    x_treat = np.random.normal(1, jitter, size=len(treat))
    ax.scatter(x_ctrl, ctrl, color=colors['control'], label='Control', alpha=0.7)
    ax.scatter(x_treat, treat, color=colors['treatment'], label='Treatment', alpha=0.7)
    # mean lines
    ax.axhline(np.mean(ctrl), color=colors['control'], linestyle='--')
    ax.axhline(np.mean(treat), color=colors['treatment'], linestyle='--')
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Control', 'Treatment'])
    ax.set_ylabel('Total tokens')
    ax.set_title(title)
    # legend only once

plot_strip(axs[0], ctrl1, treat1, 'Exp1: FastMCP refactor')
plot_strip(axs[1], ctrl2, treat2, 'Exp2: Tree-sitter synthesis')

# Adjust layout
plt.tight_layout()

# Save figure
out_path = os.path.join('figures', 'fig1-token-distribution.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight')
