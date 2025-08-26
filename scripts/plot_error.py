import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from pathlib import Path

import matplotlib
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    "text.usetex": True,
})

def extract_error_data(csv_file_path):
    """
    Extract error columns from out.csv file
    Returns DataFrame with Date and location error columns
    """
    try:
        df = pd.read_csv(csv_file_path)
        
        # Extract error columns (columns ending with 'error')
        # error_columns = [col for col in df.columns if col.endswith('error') and col != 'Total error']
        error_columns = [col for col in df.columns if col.endswith('error')]
        
        # Create a clean DataFrame with Date and error columns
        result_df = df[['Date'] + error_columns].copy()
        
        # Clean location names (remove ' error' suffix)
        cleaned_columns = ['Date'] + [col.replace(' error', '') for col in error_columns]
        result_df.columns = cleaned_columns
        
        return result_df
    
    except Exception as e:
        print(f"Error reading {csv_file_path}: {e}")
        return None

def collect_all_runs_data(instance_name, base_path):
    """
    Collect error data from all runs for a given instance
    Returns a dictionary with run numbers as keys and DataFrames as values
    """
    runs_data = {}
    
    for run_num in range(1, 11):  # runs 1-10
        folder_name = f"{instance_name}_run_{run_num}"
        csv_path = os.path.join(base_path, folder_name, "out.csv")
        
        if os.path.exists(csv_path):
            df = extract_error_data(csv_path)
            if df is not None:
                runs_data[run_num] = df
                print(f"Loaded data for {folder_name}")
            else:
                print(f"Failed to load data for {folder_name}")
        else:
            print(f"File not found: {csv_path}")
    
    return runs_data

def calculate_statistics(runs_data):
    """
    Calculate mean and standard deviation across all runs
    Returns mean_df and std_df
    """
    if not runs_data:
        return None, None
    
    # Get all location columns (excluding Date)
    first_df = list(runs_data.values())[0]
    location_columns = [col for col in first_df.columns if col != 'Date']
    
    # Initialize arrays to store all run data
    all_runs_array = []
    dates = first_df['Date'].values
    
    for run_num in sorted(runs_data.keys()):
        df = runs_data[run_num]
        # Extract just the error values for locations
        error_values = df[location_columns].values
        all_runs_array.append(error_values)
    
    # Convert to numpy array (runs, days, locations)
    all_runs_array = np.array(all_runs_array)
    
    # Calculate mean and std across runs (axis=0)
    mean_errors = np.mean(all_runs_array, axis=0)
    std_errors = np.std(all_runs_array, axis=0)
    
    # Create DataFrames
    mean_df = pd.DataFrame(mean_errors, columns=location_columns)
    mean_df['Date'] = dates
    
    std_df = pd.DataFrame(std_errors, columns=location_columns)
    std_df['Date'] = dates
    
    return mean_df, std_df

def create_heatmap(data_df, title, instance_name, metric_type, save_path):
    """
    Create and save heatmap
    """
    # Prepare data for heatmap (locations on y-axis, dates on x-axis)
    location_columns = [col for col in data_df.columns if col != 'Date']
    
    # Create matrix with locations as rows and dates as columns
    heatmap_data = data_df[location_columns].T  # Transpose to get locations on y-axis
    
    # Set up the plot
    plt.figure(figsize=(16, 10))

    # Create heatmap with fixed scale for 0-1 values
    if metric_type == 'mean':
        # For mean errors, use full 0-1 scale
        vmin, vmax = 0, heatmap_data.values.max()
        cmap = 'RdYlBu_r'  # Red = high error, Blue = low error
        # cmap = None  # Use default seaborn colormap
    else:
        # For std deviation, use 0 to max std value
        vmin, vmax = 0, heatmap_data.values.max()
        # vmin, vmax = 0, 1
        cmap = 'RdYlBu_r'  # Use red scale for standard deviation
        # cmap = None  # Use default seaborn colormap
    
    # Create heatmap
    ax = sns.heatmap(heatmap_data,
                     xticklabels=data_df['Date'],
                     yticklabels=location_columns,
                     cmap=cmap,
                     vmin=vmin,
                     vmax=vmax,
                     cbar_kws={'label': f'{metric_type.title()} Error'},
                     annot=False,  # Set to True if you want values displayed
                     fmt='.3f')

    # Increase label font size
    ax.figure.axes[-1].yaxis.label.set_size(14)

    # plt.title(f'{title}\n{instance_name} - {metric_type.title()}', fontsize=14)
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Location', fontsize=14)
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(rotation=0, fontsize=12)
    plt.tight_layout()
    
    # Save the plot
    filename = f"{instance_name}_{metric_type}_error_heatmap.png"
    full_path = os.path.join(save_path, "png", filename)
    plt.savefig(full_path, dpi=300, bbox_inches='tight')
    print(f"Saved heatmap: {full_path}")

    # Save as PGF
    pgf_filename = f"{instance_name}_{metric_type}_error_heatmap.pgf"
    pgf_path = os.path.join(save_path, "pgf", pgf_filename)
    plt.savefig(pgf_path, format='pgf', bbox_inches='tight')
    print(f"Saved PGF: {pgf_path}")
    
    plt.show()

def analyze_instance(instance_name, base_path, output_path):
    """
    Analyze all runs for a given instance and create heatmaps
    """
    print(f"\n{'='*50}")
    print(f"Analyzing instance: {instance_name}")
    print(f"{'='*50}")
    
    # Collect data from all runs
    runs_data = collect_all_runs_data(instance_name, base_path)
    
    if not runs_data:
        print(f"No data found for {instance_name}")
        return
    
    print(f"Found data for {len(runs_data)} runs")
    
    # Calculate statistics
    mean_df, std_df = calculate_statistics(runs_data)
    
    if mean_df is None:
        print(f"Failed to calculate statistics for {instance_name}")
        return
    
    # Create heatmaps
    create_heatmap(mean_df, f"Mean Error Heatmap", instance_name, "mean", output_path)
    create_heatmap(std_df, f"Standard Deviation Error Heatmap", instance_name, "std", output_path)
    
    # Save summary statistics
    summary_file = os.path.join(output_path, "data", f"{instance_name}_error_summary.csv")
    
    # Calculate overall statistics
    location_columns = [col for col in mean_df.columns if col != 'Date']
    
    summary_stats = []
    for location in location_columns:
        location_mean = mean_df[location].mean()
        location_std = std_df[location].mean()
        location_max_mean = mean_df[location].max()
        location_min_mean = mean_df[location].min()
        
        summary_stats.append({
            'Location': location,
            'Mean_Error': location_mean,
            'Mean_Std': location_std,
            'Max_Mean_Error': location_max_mean,
            'Min_Mean_Error': location_min_mean
        })
    
    summary_df = pd.DataFrame(summary_stats)
    summary_df.to_csv(summary_file, index=False)
    print(f"Saved summary statistics: {summary_file}")
    
    return mean_df, std_df

def main():
    """
    Main function to analyze all instances
    """
    # Configuration
    base_path = "/Users/shaniasinha/Desktop/UvA/Academics/IndividualProject/rohingya-flee/results"
    output_path = "/Users/shaniasinha/Desktop/UvA/Academics/IndividualProject/rohingya-flee/plots"
    
    instance_names = ["myanmar2017", "myanmar2017_demo", "myanmar2017_network"]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    print("Starting simulation results analysis...")
    print(f"Looking for results in: {base_path}")
    print(f"Output will be saved to: {output_path}")
    
    # Check if base path exists
    if not os.path.exists(base_path):
        print(f"Results directory not found: {base_path}")
        print("Please check the path and make sure simulation results exist.")
        return
    
    all_results = {}
    
    # Analyze each instance
    for instance_name in instance_names:
        try:
            mean_df, std_df = analyze_instance(instance_name, base_path, output_path)
            if mean_df is not None:
                all_results[instance_name] = {
                    'mean': mean_df,
                    'std': std_df
                }
        except Exception as e:
            print(f"Error analyzing {instance_name}: {e}")
            continue
    
    # Create comparison summary
    if all_results:
        print(f"\n{'='*50}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*50}")
        print(f"Successfully analyzed {len(all_results)} instances")
        print(f"Results saved to: {output_path}")
        
        # Print summary of which instances were analyzed
        for instance_name in all_results.keys():
            print(f"  - {instance_name}: Mean and std deviation heatmaps created")
    
    else:
        print("No instances were successfully analyzed")

if __name__ == "__main__":
    main()