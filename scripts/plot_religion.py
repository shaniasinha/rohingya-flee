import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
from scipy import stats

import matplotlib
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    "text.usetex": True,
})

def extract_muslim_data(csv_file_path):
    """
    Extract Muslim count data from agents.out.0 file
    Returns DataFrame with Date and location Muslim counts
    """
    try:
        print(f"Loading agent data from: {csv_file_path}")
        
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Clean column names (remove # prefix)
        df.columns = df.columns.str.replace('#', '')
        
        print(f"Total records: {len(df)}")
        
        # Filter for Muslim agents only
        muslim_df = df[df['religion'] == 'Muslim']
        
        print(f"Total Muslim agent records: {len(muslim_df)}")
        
        # Clean location names: if location starts with "L:", split on ":" and use last element
        def clean_location_name(location):
            if pd.isna(location):
                return location
            location_str = str(location)
            if location_str.startswith("L:"):
                parts = location_str.split(":")
                return parts[-1]  # Use the last element
            return location_str
        
        # Apply location name cleaning
        muslim_df = muslim_df.copy()
        muslim_df['current_location'] = muslim_df['current_location'].apply(clean_location_name)
        
        # Group by time and current_location to count Muslims per location per day
        muslim_counts = muslim_df.groupby(['time', 'current_location']).size().reset_index(name='muslim_count')
        
        # Rename columns to match expected format
        muslim_counts = muslim_counts.rename(columns={
            'time': 'Day',
            'current_location': 'Place',
            'muslim_count': 'Muslim'
        })
        
        return muslim_counts
    
    except Exception as e:
        print(f"Error reading {csv_file_path}: {e}")
        return None

def collect_all_runs_data(instance_name, base_path):
    """
    Collect Muslim count data from all runs for a given instance
    Returns DataFrame with all runs combined
    """
    all_runs = []
    
    for run_num in range(1, 11):  # runs 1-10
        folder_name = f"{instance_name}_run_{run_num}"
        agents_path = os.path.join(base_path, folder_name, "agents.out.0")
        
        if os.path.exists(agents_path):
            df = extract_muslim_data(agents_path)
            if df is not None:
                df['run'] = run_num
                all_runs.append(df)
                print(f"Loaded data for {folder_name}")
            else:
                print(f"Failed to load data for {folder_name}")
        else:
            print(f"File not found: {agents_path}")
    
    if all_runs:
        combined_df = pd.concat(all_runs, ignore_index=True)
        
        # Save raw combined data
        raw_data_path = os.path.join(DATA_DIR, f"{instance_name}_raw_muslim_data.csv")
        combined_df.to_csv(raw_data_path, index=False)
        print(f"Saved raw data: {raw_data_path}")
        
        return combined_df
    else:
        return None

# Instances to process
INSTANCES = ["myanmar2017_demo", "myanmar2017_network"]

# Base path for data files
BASE_PATH = "/Users/shaniasinha/Desktop/UvA/Academics/IndividualProject/rohingya-flee/results"

# Output dirs
PLOT_DIR = "plots/png"
DATA_DIR = "plots/data"
os.makedirs(PLOT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Camps
CAMP = ["Cox's Bazar"]
IDP_CAMPS = ["Sittwe", "Pauktaw", "Myebon", "Maungdaw",
             "Kyauktaw", "Kyaukpyu", "Rathedaung", "Ramree"]

# ------------------------------------------------------------
# 1. Time series of top-5 places by Muslim population
# ------------------------------------------------------------
def plot_top5_timeseries(instance_name, df):
    """
    Plot time series for top-5 places by Muslim population for a single instance
    """
    # Aggregate by day, place, run
    grouped = df.groupby(["Day", "Place", "run"])["Muslim"].sum().reset_index()

    # Find top-5 places by last day average
    last_day = grouped["Day"].max()
    last_day_means = grouped[grouped["Day"] == last_day].groupby("Place")["Muslim"].mean()
    top5_places = last_day_means.sort_values(ascending=False).head(5).index.tolist()

    # Compute mean + stderr
    summary = grouped[grouped["Place"].isin(top5_places)]
    stats = summary.groupby(["Day", "Place"])["Muslim"].agg(["mean", "std", "count"]).reset_index()
    stats["stderr"] = stats["std"] / np.sqrt(stats["count"])

    # Save aggregated data used for plotting
    aggregated_data_path = os.path.join(DATA_DIR, f"{instance_name}_top5_aggregated_data.csv")
    grouped[grouped["Place"].isin(top5_places)].to_csv(aggregated_data_path, index=False)
    print(f"Saved aggregated data: {aggregated_data_path}")

    # Save summary statistics used for plotting
    csv_path = os.path.join(DATA_DIR, f"{instance_name}_top5_timeseries_stats.csv")
    stats.to_csv(csv_path, index=False)
    print(f"Saved plotting stats: {csv_path}")

    # Save list of top 5 places
    top5_path = os.path.join(DATA_DIR, f"{instance_name}_top5_places.csv")
    top5_df = pd.DataFrame({'Place': top5_places, 'Final_Day_Mean': [last_day_means[place] for place in top5_places]})
    top5_df.to_csv(top5_path, index=False)
    print(f"Saved top 5 places: {top5_path}")

    # Plot
    plt.figure(figsize=(8, 5))
    for place in top5_places:
        subset = stats[stats["Place"] == place]
        plt.plot(subset["Day"], subset["mean"], label=place)
        plt.fill_between(subset["Day"], subset["mean"] - subset["stderr"],
                         subset["mean"] + subset["stderr"], alpha=0.2)

    plt.xlabel("Day")
    plt.ylabel("Muslim Population")
    plt.title(f"Top 5 Places by Muslim Population ({instance_name})")
    plt.legend()
    plt.tight_layout()

    plot_path = os.path.join(PLOT_DIR, f"{instance_name}_top5_timeseries.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Saved plot: {plot_path}")

# ------------------------------------------------------------
# 2. Camp vs IDP camps (across all instances)
# ------------------------------------------------------------
def plot_camp_vs_idpcamps(all_instance_data):
    """
    Plot comparison of camp vs IDP camps across all instances
    """
    all_data = []
    all_aggregated = []
    
    for instance_name, df in all_instance_data.items():
        grouped = df.groupby(["Day", "Place", "run"])["Muslim"].sum().reset_index()
        subset = grouped[grouped["Place"].isin(CAMP + IDP_CAMPS)]
        
        # Store aggregated data for each instance
        subset_copy = subset.copy()
        subset_copy["Instance"] = instance_name
        all_aggregated.append(subset_copy)
        
        stats = subset.groupby(["Day", "Place"])["Muslim"].agg(["mean", "std", "count"]).reset_index()
        stats["stderr"] = stats["std"] / np.sqrt(stats["count"])
        stats["Instance"] = instance_name
        all_data.append(stats)

    if not all_data:
        print("No data available for camp vs IDP camps comparison")
        return

    # Save all aggregated data (before computing statistics)
    all_aggregated_df = pd.concat(all_aggregated, ignore_index=True)
    aggregated_path = os.path.join(DATA_DIR, "camp_vs_idpcamps_aggregated_data.csv")
    all_aggregated_df.to_csv(aggregated_path, index=False)
    print(f"Saved aggregated data: {aggregated_path}")

    # Save statistics used for plotting
    all_stats = pd.concat(all_data, ignore_index=True)
    csv_path = os.path.join(DATA_DIR, "camp_vs_idpcamps_stats.csv")
    all_stats.to_csv(csv_path, index=False)
    print(f"Saved plotting stats: {csv_path}")

    # Save summary of places found in each instance
    summary_data = []
    for instance_name, df in all_instance_data.items():
        available_places = df['Place'].unique()
        camp_places = [place for place in CAMP if place in available_places]
        idp_places = [place for place in IDP_CAMPS if place in available_places]
        summary_data.append({
            'Instance': instance_name,
            'Available_Camps': ', '.join(camp_places),
            'Available_IDP_Camps': ', '.join(idp_places),
            'Total_Available_Places': len(available_places)
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_path = os.path.join(DATA_DIR, "camp_vs_idpcamps_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"Saved summary: {summary_path}")

    # Create color mapping for consistent colors across subplots
    all_places = CAMP + IDP_CAMPS
    colors = plt.cm.tab10(np.linspace(0, 1, len(all_places)))
    color_map = {place: colors[i] for i, place in enumerate(all_places)}
    
    # Plot with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    axes = [ax1, ax2]
    
    for i, instance_name in enumerate(INSTANCES):
        ax = axes[i]
        
        for place in all_places:
            subset = all_stats[(all_stats["Instance"] == instance_name) & (all_stats["Place"] == place)]
            if subset.empty:
                continue
            
            # Use consistent color for each place across subplots
            color = color_map[place]
            linestyle = '-' if place in CAMP else '--'  # Solid for camps, dashed for IDP camps
            
            ax.plot(subset["Day"], subset["mean"], 
                   label=place, linewidth=2, color=color, linestyle=linestyle)
            ax.fill_between(subset["Day"], 
                           subset["mean"] - subset["stderr"],
                           subset["mean"] + subset["stderr"], 
                           alpha=0.2, color=color)

        ax.set_xlabel("Day", fontsize=12)
        ax.set_ylabel("Muslim Population", fontsize=12)
        ax.set_title(f"{instance_name}", fontsize=14)
        ax.legend(fontsize=9, loc='upper left')
        ax.grid(True, alpha=0.3)
    
    # Add overall title
    fig.suptitle("Camp vs IDP Camps Comparison", fontsize=16, y=1.02)
    plt.tight_layout()

    plot_path = os.path.join(PLOT_DIR, "camp_vs_idpcamps.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved plot: {plot_path}")

# ------------------------------------------------------------
# Main function
# ------------------------------------------------------------
def main():
    """
    Main function to process all instances and generate plots
    """
    print("Starting Muslim population analysis...")
    
    all_instance_data = {}
    
    for instance in INSTANCES:
        print(f"\nProcessing instance: {instance}")
        
        # Collect data from all runs for this instance
        instance_df = collect_all_runs_data(instance, BASE_PATH)
        
        if instance_df is None or instance_df.empty:
            print(f"No data found for {instance}, skipping.")
            continue
        
        print(f"Loaded {len(instance_df)} records for {instance}")
        all_instance_data[instance] = instance_df
        
        # Generate top-5 timeseries plot for this instance
        plot_top5_timeseries(instance, instance_df)

    # Generate camp vs idpcamps comparison across all instances
    if all_instance_data:
        print(f"\nGenerating comparison plot across {len(all_instance_data)} instances...")
        plot_camp_vs_idpcamps(all_instance_data)
        
        # Save a master dataset with all instances combined
        all_combined = []
        for instance_name, df in all_instance_data.items():
            df_copy = df.copy()
            df_copy['Instance'] = instance_name
            all_combined.append(df_copy)
        
        master_df = pd.concat(all_combined, ignore_index=True)
        master_path = os.path.join(DATA_DIR, "all_instances_master_dataset.csv")
        master_df.to_csv(master_path, index=False)
        print(f"Saved master dataset: {master_path}")
        
    else:
        print("No instance data available for comparison plots")
    
    print(f"\nAnalysis complete! All data files saved in: {DATA_DIR}")
    print(f"All plots saved in: {PLOT_DIR}")

if __name__ == "__main__":
    main()