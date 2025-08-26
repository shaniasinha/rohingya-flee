import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

import matplotlib
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    "text.usetex": True,
})

def plot_transition_probability(data):
    # Extract data
    x = data['Instance']
    mean = data['Mean_Transition_Probability']
    std = data['Std_Transition_Probability']

    # Create the plot
    plt.figure(figsize=(8, 5))
    
    # Create bar plot with error bars
    bars = plt.bar(x, mean, yerr=std, capsize=5, color='skyblue', 
                   edgecolor='navy', linewidth=1.2, alpha=1)
    
    # Add value labels on top of bars
    for i, (bar, mean_val, std_val) in enumerate(zip(bars, mean, std)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + std_val + 0.0005,
                f'{mean_val:.4f}', ha='center', va='bottom', fontsize=15, fontweight='bold')

    # Add labels, title, and formatting
    plt.xlabel('Model', fontsize=17)
    plt.ylabel('Transition Probability', fontsize=17)
    # plt.title('Transition Probability')
    plt.xticks(fontsize=15, rotation=0)
    plt.yticks(fontsize=15)

    # Set y-axis limits to better show the differences
    y_min = min(mean - std) * 0.995
    y_max = max(mean + std) * 1.01
    plt.ylim(y_min, y_max)

    # Save or show the plot
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('plots/png/transition_probability_plot.png', dpi=300, bbox_inches='tight')  # Save the plot
    plt.show()  # Show the plot

def main():
    # Load your data
    data = pd.read_csv('plots/data/transition_probability_summary.csv')
    plot_transition_probability(data)

if __name__ == "__main__":
    main()