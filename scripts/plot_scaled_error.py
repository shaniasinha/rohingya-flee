import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

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

def scale_errors_to_01(data_array, location_names=None):
    """
    Scale error values to be between 0 and 1 using Min-Max scaling
    Input: numpy array of shape (runs, days, locations)
    Output: scaled array with same shape, values between 0 and 1
    Each location is scaled independently across all days and runs
    """
    scaled_array = np.zeros_like(data_array)
    
    # Scale each location independently (across all runs and days)
    for location_idx in range(data_array.shape[2]):  # locations dimension
        # Get all values for this location across all runs and days
        location_data = data_array[:, :, location_idx]
        
        # Remove any NaN or infinite values
        valid_values = location_data[np.isfinite(location_data)]
        
        location_name = location_names[location_idx] if location_names else f"Location {location_idx}"
        
        if len(valid_values) == 0:
            print(f"Warning: No valid error values found for {location_name}")
            scaled_array[:, :, location_idx] = location_data
            continue
        
        # Get min and max for this specific location
        location_min = np.min(valid_values)
        location_max = np.max(valid_values)
        
        print(f"{location_name}: min={location_min:.4f}, max={location_max:.4f}")
        
        # Apply Min-Max scaling for this location: (x - min) / (max - min)
        if location_max == location_min:
            # All values are the same, set to 0.5
            scaled_array[:, :, location_idx] = np.full_like(location_data, 0.5)
        else:
            scaled_array[:, :, location_idx] = (location_data - location_min) / (location_max - location_min)
    
    # Ensure values are between 0 and 1
    scaled_array = np.clip(scaled_array, 0, 1)
    
    return scaled_array

def calculate_statistics(runs_data):
    """
    Calculate mean and standard deviation across all runs
    Returns mean_df and std_df with errors scaled to 0-1
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
    
    # Scale all errors to 0-1 range (per location)
    print("Scaling error values to 0-1 range for each location individually...")
    print(f"Processing {len(location_columns)} locations: {location_columns}")
    scaled_array = scale_errors_to_01(all_runs_array, location_columns)
    
    # Calculate mean and std across runs (axis=0) using scaled values
    mean_errors = np.mean(scaled_array, axis=0)
    std_errors = np.std(scaled_array, axis=0)
    
    # Create DataFrames
    mean_df = pd.DataFrame(mean_errors, columns=location_columns)
    mean_df['Date'] = dates
    
    std_df = pd.DataFrame(std_errors, columns=location_columns)
    std_df['Date'] = dates
    
    return mean_df, std_df

def create_heatmap(data_df, title, instance_name, metric_type, save_path):
    """
    Create and save heatmap with scaled 0-1 error values
    """
    # Prepare data for heatmap (locations on y-axis, dates on x-axis)
    location_columns = [col for col in data_df.columns if col != 'Date']

    # Only have locations where location name is not "Ramree"
    # location_columns = [col for col in location_columns if col != "Ramree" and col != "Kyauktaw"]

    # Create matrix with locations as rows and dates as columns
    heatmap_data = data_df[location_columns].T  # Transpose to get locations on y-axis
    
    # Set up the plot
    plt.figure(figsize=(8, 6))
    
    # Create heatmap with fixed scale for 0-1 values
    if metric_type == 'mean':
        # For mean errors, use full 0-1 scale
        vmin, vmax = 0, 1
        cmap = 'RdYlBu_r'  # Red = high error, Blue = low error
        # cmap = None  # Use default seaborn colormap
    else:
        # For std deviation, use 0 to max std value
        vmin, vmax = 0, heatmap_data.values.max()
        # vmin, vmax = 0, 1
        cmap = 'RdYlBu_r'  # Use red scale for standard deviation
        # cmap = None  # Use default seaborn colormap

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

    # plt.title(f'{title}\n{instance_name} - {metric_type.title()} Error Across Locations and Time\n(Errors scaled to 0-1 range)')
    plt.xlabel('Date', fontsize=14, fontweight='bold')
    plt.ylabel('Location', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(rotation=0, fontsize=12)
    plt.tight_layout()
    
    # Save the plot
    filename = f"{instance_name}_{metric_type}_error_heatmap_scaled.png"
    full_path = os.path.join(save_path, "png", filename)
    plt.savefig(full_path, dpi=300, bbox_inches='tight')
    print(f"Saved scaled heatmap: {full_path}")
    
    plt.show()

def analyze_instance(instance_name, base_path, output_path):
    """
    Analyze all runs for a given instance and create heatmaps with scaled errors
    """
    print(f"\n{'-'*40}")
    print(f"Analyzing instance: {instance_name}")
    print(f"{'-'*40}")
    
    # Collect data from all runs
    runs_data = collect_all_runs_data(instance_name, base_path)
    
    if not runs_data:
        print(f"No data found for {instance_name}")
        return
    
    print(f"Found data for {len(runs_data)} runs")
    
    # Calculate statistics with scaling
    mean_df, std_df = calculate_statistics(runs_data)
    
    if mean_df is None:
        print(f"Failed to calculate statistics for {instance_name}")
        return
    
    # Print scaling information
    location_columns = [col for col in mean_df.columns if col != 'Date']
    mean_range = [mean_df[location_columns].min().min(), mean_df[location_columns].max().max()]
    std_range = [std_df[location_columns].min().min(), std_df[location_columns].max().max()]
    
    print(f"Scaled mean error range: {mean_range[0]:.4f} to {mean_range[1]:.4f}")
    print(f"Scaled std error range: {std_range[0]:.4f} to {std_range[1]:.4f}")
    
    # Create heatmaps
    create_heatmap(mean_df, f"Mean Error Heatmap (Scaled)", instance_name, "mean", output_path)
    create_heatmap(std_df, f"Standard Deviation Error Heatmap (Scaled)", instance_name, "std", output_path)
    
    # Save summary statistics with scaling information
    summary_file = os.path.join(output_path, "data", f"{instance_name}_error_summary_scaled.csv")
    
    # Calculate overall statistics
    summary_stats = []
    for location in location_columns:
        location_mean = mean_df[location].mean()
        location_std = std_df[location].mean()
        location_max_mean = mean_df[location].max()
        location_min_mean = mean_df[location].min()
        
        summary_stats.append({
            'Location': location,
            'Mean_Error_Scaled': location_mean,
            'Mean_Std_Scaled': location_std,
            'Max_Mean_Error_Scaled': location_max_mean,
            'Min_Mean_Error_Scaled': location_min_mean
        })
    
    summary_df = pd.DataFrame(summary_stats)
    summary_df.to_csv(summary_file, index=False)
    print(f"Saved scaled summary statistics: {summary_file}")
    
    return mean_df, std_df

def main():
    """
    Main function to analyze all instances with error scaling
    """
    # Configuration
    base_path = "/Users/shaniasinha/Desktop/UvA/Academics/IndividualProject/rohingya-flee/results"
    output_path = "/Users/shaniasinha/Desktop/UvA/Academics/IndividualProject/rohingya-flee/plots"
    
    instance_names = ["myanmar2017", "myanmar2017_demo", "myanmar2017_network"]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    print("Starting simulation results analysis with location-specific error scaling...")
    print(f"Looking for results in: {base_path}")
    print(f"Output will be saved to: {output_path}")
    print("Each location's errors will be scaled to 0-1 range independently")
    
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
        print(f"\n{'-'*40}")
        print("ANALYSIS COMPLETE")
        print(f"{'-'*40}")
        print(f"Successfully analyzed {len(all_results)} instances")
        print(f"Results saved to: {output_path}")
        print("All heatmaps use location-specific scaled errors (0-1 range per location)")
        
        # Print summary of which instances were analyzed
        for instance_name in all_results.keys():
            print(f"  - {instance_name}: Mean and std deviation heatmaps created (location-specific scaling)")
    
    else:
        print("No instances were successfully analyzed")

if __name__ == "__main__":
    main()