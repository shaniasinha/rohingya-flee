import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

import matplotlib
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    "text.usetex": True,
})

def plot_coxs_bazar_comparison():
    """
    Plot Cox's Bazar population comparison between myanmar2017_demo and myanmar2017_network
    with standard deviation shading and save to plots/png directory.
    """
    # Read the CSV file
    df = pd.read_csv('plots/data/camp_vs_idpcamps_stats.csv')
    
    # Filter for Cox's Bazar only
    coxs_bazar_data = df[df['Place'] == "Cox's Bazar"]
    
    # Separate data by instance
    demo_data = coxs_bazar_data[coxs_bazar_data['Instance'] == 'myanmar2017_demo']
    network_data = coxs_bazar_data[coxs_bazar_data['Instance'] == 'myanmar2017_network']
    
    # Create the plot
    plt.figure(figsize=(6, 4))
    
    # Plot demo data with shading
    plt.plot(demo_data['Day'], demo_data['mean'], 
             label='myanmar2017_demo', linewidth=1, color='blue')
    plt.fill_between(demo_data['Day'], 
                     demo_data['mean'] - demo_data['std'],
                     demo_data['mean'] + demo_data['std'],
                     alpha=0.3, color='blue')
    
    # Plot network data with shading
    plt.plot(network_data['Day'], network_data['mean'], 
             label='myanmar2017_network', linewidth=1, color='red')
    plt.fill_between(network_data['Day'], 
                     network_data['mean'] - network_data['std'],
                     network_data['mean'] + network_data['std'],
                     alpha=0.3, color='red')
    
    # Customize the plot
    plt.xlabel('Day', fontsize=12)
    plt.ylabel('Population', fontsize=12)
    # plt.title("Cox's Bazar Population Comparison: Demo vs Network", fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Format y-axis to show thousands
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))
    
    # Adjust layout
    plt.tight_layout()
    
    # Create directory if it doesn't exist
    os.makedirs('plots/png', exist_ok=True)
    
    # Save the plot
    plt.savefig('plots/png/coxs_bazar_comparison.png', dpi=300, bbox_inches='tight')
    
    # Show the plot
    plt.show()
    
    print("Plot saved to plots/png/coxs_bazar_comparison.png")

def plot_camp_vs_all_idpcamps():
    # Read the CSV file
    df = pd.read_csv('plots/data/camp_vs_idpcamps_stats.csv')
    
    # Filter for Cox's Bazar only
    cb_data = df[df['Place'] == "Cox's Bazar"]
    
    # Separate Cox's Bazar data by instance
    cb_demo_data = cb_data[cb_data['Instance'] == 'myanmar2017_demo']
    cb_network_data = cb_data[cb_data['Instance'] == 'myanmar2017_network']

    # Filter for all IDP camps (exclude Cox's Bazar)
    idp_camps_data = df[df['Place'] != "Cox's Bazar"]

    # Remove outliers Kyauktaw and Ramree
    # idp_camps_data = idp_camps_data[~idp_camps_data['Place'].isin(['Kyauktaw', 'Ramree'])]

    # Aggregate IDP camp data: sum population across all camps for each day and instance
    # First, reconstruct individual run data from mean/std/count
    idp_aggregated = []
    
    for _, row in idp_camps_data.iterrows():
        # For each camp-day-instance combination, we have mean, std, count
        # We'll use the mean as representative value for aggregation
        for run in range(int(row['count'])):
            idp_aggregated.append({
                'Day': row['Day'],
                'Instance': row['Instance'],
                'run': run,
                'Population': row['mean']  # Using mean as proxy for individual run values
            })
    
    idp_df = pd.DataFrame(idp_aggregated)
    
    # Sum across all camps for each day, run, and instance
    idp_daily_totals = idp_df.groupby(['Day', 'Instance', 'run'])['Population'].sum().reset_index()
    
    # Calculate statistics for each day and instance
    idp_stats = idp_daily_totals.groupby(['Day', 'Instance'])['Population'].agg(['mean', 'std', 'count']).reset_index()
    idp_stats['stderr'] = idp_stats['std'] / np.sqrt(idp_stats['count'])
    
    # Separate IDP data by instance
    idp_demo_stats = idp_stats[idp_stats['Instance'] == 'myanmar2017_demo']
    idp_network_stats = idp_stats[idp_stats['Instance'] == 'myanmar2017_network']

    # Create the plot
    plt.figure(figsize=(6, 4))

    # Plot Cox's Bazar data with shading
    plt.plot(cb_demo_data['Day'], cb_demo_data['mean'], 
             label="Cox's Bazar (Demo)", linewidth=1, color='blue', linestyle='-')
    plt.fill_between(cb_demo_data['Day'], 
                     cb_demo_data['mean'] - cb_demo_data['std'],
                     cb_demo_data['mean'] + cb_demo_data['std'],
                     alpha=0.5, color='blue')
    
    plt.plot(cb_network_data['Day'], cb_network_data['mean'], 
             label="Cox's Bazar (Network)", linewidth=1, color='red', linestyle='-')
    plt.fill_between(cb_network_data['Day'], 
                     cb_network_data['mean'] - cb_network_data['std'],
                     cb_network_data['mean'] + cb_network_data['std'],
                     alpha=0.5, color='red')

    # Plot aggregated IDP camps data with shading
    plt.plot(idp_demo_stats['Day'], idp_demo_stats['mean'], 
             label='All IDP Camps (Demo)', linewidth=1, color='darkorange', linestyle='-')
    plt.fill_between(idp_demo_stats['Day'], 
                     idp_demo_stats['mean'] - idp_demo_stats['std'],
                     idp_demo_stats['mean'] + idp_demo_stats['std'],
                     alpha=0.5, color='darkorange')

    plt.plot(idp_network_stats['Day'], idp_network_stats['mean'], 
             label='All IDP Camps (Network)', linewidth=1, color='green', linestyle='-')
    plt.fill_between(idp_network_stats['Day'], 
                     idp_network_stats['mean'] - idp_network_stats['std'],
                     idp_network_stats['mean'] + idp_network_stats['std'],
                     alpha=0.5, color='green')

    # Customize the plot
    plt.xlabel('Day', fontsize=12)
    plt.ylabel('Population', fontsize=12)
    # plt.title("Refugee Camp vs IDP Camps Population Comparison", fontsize=14)
    plt.legend(fontsize=8, loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # Format y-axis to show thousands
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))

    # Adjust layout
    plt.tight_layout()
    
    # Create directory if it doesn't exist
    os.makedirs('plots/png', exist_ok=True)
    
    # Save the plot
    plt.savefig('plots/png/refugee_vs_idp_comparison.png', dpi=300, bbox_inches='tight')
    
    # Show the plot
    plt.show()
    
    print("Plot saved to plots/png/refugee_vs_idp_comparison.png")

def plot_camp_vs_idpcamps():
    """
    Plot comparison of camp vs IDP camps across all instances
    Reads data from plots/data and saves plot to plots/png
    """
    # Define camps and IDP camps
    CAMP = ["Cox's Bazar"]
    IDP_CAMPS = ["Sittwe", "Pauktaw", "Myebon", "Maungdaw",
                 "Kyauktaw", "Kyaukpyu", "Rathedaung", "Ramree"]
    INSTANCES = ["myanmar2017_demo", "myanmar2017_network"]
    
    # Read the statistics data
    try:
        all_stats = pd.read_csv('plots/data/camp_vs_idpcamps_stats.csv')
        print("Loaded camp vs IDP camps statistics data")
    except FileNotFoundError:
        print("Error: camp_vs_idpcamps_stats.csv not found in plots/data/")
        print("Please run plot_religion.py first to generate the data files")
        return

    # Create color mapping for consistent colors across subplots
    all_places = CAMP + IDP_CAMPS
    colors = plt.cm.tab10(np.linspace(0, 1, len(all_places)))
    color_map = {place: colors[i] for i, place in enumerate(all_places)}
    
    # Plot with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    axes = [ax1, ax2]
    
    # Track legend elements for shared legend
    legend_elements = []
    legend_labels_added = set()
    
    for i, instance_name in enumerate(INSTANCES):
        ax = axes[i]
        
        for place in all_places:
            subset = all_stats[(all_stats["Instance"] == instance_name) & (all_stats["Place"] == place)]
            if subset.empty:
                continue
            
            # Use consistent color for each place across subplots
            color = color_map[place]
            linestyle = '-' if place in CAMP else '--'  # Solid for camps, dashed for IDP camps
            
            line = ax.plot(subset["Day"], subset["mean"], 
                          linewidth=0.9, color=color, linestyle=linestyle)
            ax.fill_between(subset["Day"], 
                           subset["mean"] - subset["std"],
                           subset["mean"] + subset["std"], 
                           alpha=0.4, color=color)
            
            # Add to legend elements only once per place
            if place not in legend_labels_added:
                legend_elements.append(line[0])
                legend_labels_added.add(place)
        
        if i != 0:
            ax.set_ylabel("Population", fontsize=16)
        
        ax.set_xlabel("Day", fontsize=16)
        ax.set_title(f"{instance_name}", fontsize=18)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', labelsize=14)
        ax.tick_params(axis='y', labelsize=14)

    # Create shared legend positioned outside the plots
    # plt.legend(legend_elements, all_places, 
    #            loc='lower right', fontsize=12, bbox_to_anchor=(0.7, 0.8))
    fig.legend(legend_elements, all_places,
               loc="center right", fontsize=12)

    # Add overall title
    # fig.suptitle("Camp vs IDP Camps Comparison", fontsize=18, y=0.98)
    # Adjust layout to make room for legend
    plt.subplots_adjust(right=0.85,wspace=0.3)
    
    # Apply tight layout after adjusting for legend
    plt.tight_layout()

    # Create directory if it doesn't exist
    os.makedirs('plots/png', exist_ok=True)
    
    # Save the plot
    plot_path = os.path.join('plots/png', "camp_vs_idpcamps_subplots.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Saved plot: {plot_path}")



# Run the function
if __name__ == "__main__":
    # plot_coxs_bazar_comparison()
    plot_camp_vs_all_idpcamps()
    # plot_camp_vs_idpcamps()