import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

exp1_path = os.path.join('experiments', 'exp1-fastmcp-refactor', 'efficiency.json')
exp2_path = os.path.join('experiments', 'exp2-treesitter-synthesis', 'efficiency.json')


def load_messages(path):
    """Load messages from the given efficiency.json file.
    Returns three lists:
        ctrl_valid: messages from valid control runs
        ctrl_invalid: messages from invalid control runs (e.g., drift failures)
        treat_valid: messages from valid treatment runs
    """
    with open(path, 'r') as f:
        data = json.load(f)
    ctrl_valid = []
    ctrl_invalid = []
    treat_valid = []
    for run in data['runs']:
        group = run.get('group')
        valid = run.get('valid', True)
        msgs = run.get('messages')
        if group == 'control':
            if valid:
                ctrl_valid.append(msgs)
            else:
                ctrl_invalid.append(msgs)
        elif group == 'treatment':
            if valid:
                treat_valid.append(msgs)
            # Invalid treatment runs are ignored
    return ctrl_valid, ctrl_invalid, treat_valid

ctrl1_valid, ctrl1_invalid, treat1 = load_messages(exp1_path)
ctrl2_valid, ctrl2_invalid, treat2 = load_messages(exp2_path)

fig, axs = plt.subplots(1, 2, figsize=(10,5), sharey=True)
colors = {'control': '#1f77b4', 'treatment': '#ff7f0e'}


def plot(ax, ctrl_valid, ctrl_invalid, treat, title):
    jitter = 0.05
    # Jitter for valid control points
    x_ctrl = np.random.normal(0, jitter, size=len(ctrl_valid))
    # Jitter for treatment points
    x_treat = np.random.normal(1, jitter, size=len(treat))
    # Plot valid control runs
    ax.scatter(x_ctrl, ctrl_valid, color=colors['control'], label='Control', alpha=0.7)
    # Plot treatment runs
    ax.scatter(x_treat, treat, color=colors['treatment'], label='Treatment', alpha=0.7)
    # Plot invalid control runs (outliers) as red X
    if ctrl_invalid:
        # Position them at x=0 with a small jitter
        x_invalid = np.random.normal(0, jitter, size=len(ctrl_invalid))
        ax.scatter(x_invalid, ctrl_invalid, color='red', marker='x', s=80, zorder=5, label='Invalid')
        for xv, yv in zip(x_invalid, ctrl_invalid):
            ax.text(xv, yv, 'drift failure', color='red', fontsize=8, ha='center', va='bottom')
    # Mean lines for valid runs only
    if ctrl_valid:
        ax.axhline(np.mean(ctrl_valid), color=colors['control'], linestyle='--')
    if treat:
        ax.axhline(np.mean(treat), color=colors['treatment'], linestyle='--')
    ax.set_xticks([0,1])
    ax.set_xticklabels(['Control','Treatment'])
    ax.set_ylabel('Messages per run')
    ax.set_title(title)

# Plot experiments1 with both valid and invalid control runs
plot(axs[0], ctrl1_valid, ctrl1_invalid, treat1, 'Exp1: FastMCP refactor')
# Plot experiment2 (no invalid control runs)
plot(axs[1], ctrl2_valid, ctrl2_invalid, treat2, 'Exp2: Tree-sitter synthesis')

plt.tight_layout()
out_path = os.path.join('figures', 'fig3-message-counts.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight')
