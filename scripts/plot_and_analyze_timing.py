import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import matplotlib
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    "text.usetex": True,
})

def analyze_simulation_timing():
    # Read the CSV file
    df = pd.read_csv('results/simulation_timing.csv', 
                     names=['instance', 'run', 'real_time', 'user_time', 'sys_time'])
    
    # Calculate average times and standard deviations for each instance
    avg_times = df.groupby('instance')[['real_time', 'user_time', 'sys_time']].mean()
    std_times = df.groupby('instance')[['real_time', 'user_time', 'sys_time']].std()
    
    print("Average Execution Times by Instance:")
    print("=" * 50)
    for instance in avg_times.index:
        print(f"\n{instance}:")
        print(f"  Real Time: {avg_times.loc[instance, 'real_time']:.2f} seconds")
        print(f"  User Time: {avg_times.loc[instance, 'user_time']:.2f} seconds")
        print(f"  Sys Time: {avg_times.loc[instance, 'sys_time']:.2f} seconds")
        
        # Calculate total average time
        total_avg = avg_times.loc[instance].sum()
        print(f"  Total Average: {total_avg:.2f} seconds")
    
    # Create comparison visualization
    plt.figure(figsize=(5, 3))
    
    # Bar chart of individual timing components with error bars
    x = np.arange(len(avg_times.index))
    width = 0.25

    plt.bar(x - width, avg_times['real_time'], width, label='Real Time', alpha=0.8,
            yerr=std_times['real_time'], capsize=3)
    plt.bar(x, avg_times['user_time'], width, label='User Time', alpha=0.8,
            yerr=std_times['user_time'], capsize=3)
    plt.bar(x + width, avg_times['sys_time'], width, label='Sys Time', alpha=0.8,
            yerr=std_times['sys_time'], capsize=3)

    plt.xlabel('Instance', fontsize=12)
    plt.ylabel('Time (seconds)', fontsize=12)
    # plt.title('Average Execution Times by Component', fontsize=14)
    plt.xticks(x, avg_times.index, rotation=0, fontsize=10)
    plt.yticks(fontsize=10)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/png/timing_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Statistical summary
    print("\n" + "=" * 50)
    print("SUMMARY STATISTICS:")
    print("=" * 50)
    
    total_times = avg_times.sum(axis=1)
    total_times_sorted = total_times.sort_values()
    fastest = total_times_sorted.index[0]
    slowest = total_times_sorted.index[-1]
    
    print(f"Fastest instance: {fastest} ({total_times_sorted.iloc[0]:.2f}s)")
    print(f"Slowest instance: {slowest} ({total_times_sorted.iloc[-1]:.2f}s)")
    print(f"Speed difference: {total_times_sorted.iloc[-1] / total_times_sorted.iloc[0]:.2f}x")
    
    # Standard deviation analysis
    print(f"\nVariability (Standard Deviation):")
    for instance in avg_times.index:
        instance_data = df[df['instance'] == instance]
        total_std = instance_data[['real_time', 'user_time', 'sys_time']].sum(axis=1).std()
        print(f"  {instance}: ±{total_std:.2f}s")

if __name__ == "__main__":
    analyze_simulation_timing()