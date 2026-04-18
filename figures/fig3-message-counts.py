import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

exp1_path = os.path.join('experiments', 'exp1-fastmcp-refactor', 'efficiency.json')
exp2_path = os.path.join('experiments', 'exp2-treesitter-synthesis', 'efficiency.json')


def load_messages(path):
    with open(path, 'r') as f:
        data = json.load(f)
    ctrl = []
    treat = []
    for run in data['runs']:
        if run.get('valid', True) is False:
            continue
        if run['group'] == 'control':
            ctrl.append(run['messages'])
        elif run['group'] == 'treatment':
            treat.append(run['messages'])
    return ctrl, treat

ctrl1, treat1 = load_messages(exp1_path)
ctrl2, treat2 = load_messages(exp2_path)

fig, axs = plt.subplots(1, 2, figsize=(10,5), sharey=True)
colors = {'control': '#1f77b4', 'treatment': '#ff7f0e'}


def plot(ax, ctrl, treat, title, outlier=None):
    jitter = 0.05
    x_ctrl = np.random.normal(0, jitter, size=len(ctrl))
    x_treat = np.random.normal(1, jitter, size=len(treat))
    ax.scatter(x_ctrl, ctrl, color=colors['control'], label='Control', alpha=0.7)
    ax.scatter(x_treat, treat, color=colors['treatment'], label='Treatment', alpha=0.7)
    # mean lines
    ax.axhline(np.mean(ctrl), color=colors['control'], linestyle='--')
    ax.axhline(np.mean(treat), color=colors['treatment'], linestyle='--')
    ax.set_xticks([0,1])
    ax.set_xticklabels(['Control','Treatment'])
    ax.set_ylabel('Messages per run')
    ax.set_title(title)
    if outlier is not None:
        # outlier is (value, index) within control list
        val, idx = outlier
        # find x position for that point (first control point)
        x_pos = x_ctrl[idx]
        ax.scatter(x_pos, val, color='red', marker='x', s=80, zorder=5)
        ax.text(x_pos, val, 'drift failure', color='red', fontsize=8, ha='center', va='bottom')

# Identify outlier index (first control entry is drift failure 93)
outlier_idx = 0  # assuming ctrl1[0] is 93
plot(axs[0], ctrl1, treat1, 'Exp1: FastMCP refactor', outlier=(ctrl1[outlier_idx], outlier_idx))
plot(axs[1], ctrl2, treat2, 'Exp2: Tree-sitter synthesis')

plt.tight_layout()
out_path = os.path.join('figures', 'fig3-message-counts.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight')
