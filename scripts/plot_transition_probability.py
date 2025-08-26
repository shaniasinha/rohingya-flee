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
    plt.plot(x, mean, label='Mean Transition Probability', color='blue')
    plt.fill_between(x, mean - std, mean + std, color='blue', alpha=0.2, label='Standard Deviation')

    # Add labels, title, and legend
    plt.xlabel('Model', fontsize=14)
    plt.ylabel('Transition Probability', fontsize=14)
    # plt.title('Transition Probability')
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend()

    # Save or show the plot
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('plots/png/transition_probability_plot.png', dpi=300, bbox_inches='tight')  # Save the plot
    plt.show()  # Show the plot

def main():
    # Load your data
    data = pd.read_csv('plots/data/transition_probability_summary.csv')
    plot_transition_probability(data)

if __name__ == "__main__":
    main()