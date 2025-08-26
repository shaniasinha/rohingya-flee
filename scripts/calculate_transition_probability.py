#!/usr/bin/env python3
"""
Script to calculate transition probability for refugee movement patterns.
Transition probability is defined as the proportion of agents that went to an IDP camp first
and then went to Cox's Bazar across space and time.
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import glob
from collections import defaultdict

def parse_agents_file(file_path):
    """
    Parse agents.out.0 file to track agent movements over time.
    Returns a dictionary with agent movement history.
    """
    print(f"Parsing agents file: {file_path}")
    
    try:
        # Read the CSV file in chunks to handle large files
        chunk_size = 50000  # Process 50k rows at a time
        agent_movements = defaultdict(list)
        
        print("Reading file in chunks...")
        chunk_count = 0
        
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            chunk_count += 1
            print(f"  Processing chunk {chunk_count} ({len(chunk)} rows)")
            
            # Clean column names (remove # prefix)
            chunk.columns = chunk.columns.str.replace('#', '')
            
            # Use all agents (no religion filtering)
            agents_chunk = chunk.copy()
            
            # Clean location names
            def clean_location_name(location):
                if pd.isna(location):
                    return location
                location_str = str(location)
                if location_str.startswith("L:"):
                    parts = location_str.split(":")
                    return parts[-1]
                return location_str
            
            agents_chunk['current_location'] = agents_chunk['current_location'].apply(clean_location_name)
            
            # Track agent movements for this chunk
            for _, row in agents_chunk.iterrows():
                # Handle different column naming conventions
                agent_id = row.get('rank-agentid', row.get('agent_id', None))
                day = row.get('time', row.get('timestep', None))
                location = row['current_location']
                
                if agent_id is None or day is None:
                    continue
                
                agent_movements[agent_id].append({
                    'day': day,
                    'location': location
                })
        
        print(f"Processed {chunk_count} chunks, found {len(agent_movements)} unique agents")
        
        # Sort movements by day for each agent
        for agent_id in agent_movements:
            agent_movements[agent_id] = sorted(agent_movements[agent_id], key=lambda x: x['day'])
        
        return agent_movements
        
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return {}

def calculate_transition_probability(agent_movements):
    """
    Calculate transition probability: proportion of agents that went to IDP camp first,
    then to Cox's Bazar.
    """
    # Define IDP camps (excluding Cox's Bazar which is the refugee camp)
    IDP_CAMPS = {'Sittwe', 'Pauktaw', 'Myebon', 'Maungdaw', 
                 'Kyauktaw', 'Kyaukpyu', 'Rathedaung', 'Ramree', 'Buthidaung', 'Paletwa'}
    
    COXS_BAZAR = "Cox's Bazar"
    
    total_agents = len(agent_movements)
    transition_agents = 0
    
    for agent_id, movements in agent_movements.items():
        # Track if agent went to IDP camp first, then to Cox's Bazar
        went_to_idp_first = False
        went_to_coxs_after_idp = False
        
        for movement in movements:
            location = movement['location']
            
            # Check if agent went to IDP camp
            if location in IDP_CAMPS and not went_to_idp_first:
                went_to_idp_first = True
            
            # Check if agent went to Cox's Bazar after being in IDP camp
            elif location == COXS_BAZAR and went_to_idp_first:
                went_to_coxs_after_idp = True
                break
        
        if went_to_coxs_after_idp:
            transition_agents += 1
    
    # Calculate transition probability
    if total_agents > 0:
        transition_probability = transition_agents / total_agents
    else:
        transition_probability = 0.0
    
    return transition_probability, transition_agents, total_agents

def process_instance_type(instance_type, results_dir):
    """
    Process all runs for a given instance type and calculate transition probabilities.
    """
    print(f"\nProcessing instance type: {instance_type}")
    
    # Find all run directories for this instance type
    pattern = os.path.join(results_dir, f"{instance_type}_run_*")
    run_dirs = glob.glob(pattern)
    
    if not run_dirs:
        print(f"No run directories found for {instance_type}")
        return None, None, None
    
    print(f"Found {len(run_dirs)} runs for {instance_type}")
    
    transition_probabilities = []
    
    for run_dir in sorted(run_dirs):
        run_number = os.path.basename(run_dir).split('_')[-1]
        agents_file = os.path.join(run_dir, 'agents.out.0')
        
        if not os.path.exists(agents_file):
            print(f"Warning: agents.out.0 not found in {run_dir}")
            continue
        
        print(f"Processing run {run_number}...")
        
        # Parse agent movements
        agent_movements = parse_agents_file(agents_file)
        
        if not agent_movements:
            print(f"Warning: No agent movements found in run {run_number}")
            continue
        
        # Calculate transition probability for this run
        transition_prob, transition_count, total_count = calculate_transition_probability(agent_movements)
        transition_probabilities.append(transition_prob)
        
        print(f"  Run {run_number}: {transition_count}/{total_count} = {transition_prob:.4f}")
    
    if not transition_probabilities:
        print(f"No valid transition probabilities calculated for {instance_type}")
        return None, None, None
    
    # Calculate statistics
    mean_prob = np.mean(transition_probabilities)
    std_prob = np.std(transition_probabilities, ddof=1) if len(transition_probabilities) > 1 else 0.0
    
    return mean_prob, std_prob, transition_probabilities

def main():
    """
    Main function to calculate transition probabilities for all instance types.
    """
    # Set up paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    results_dir = project_dir / 'results'
    
    # Check if results directory exists
    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)
    
    # Define instance types to process
    instance_types = ['myanmar2017', 'myanmar2017_demo', 'myanmar2017_network']
    
    print("Calculating Transition Probabilities")
    print("="*50)
    print("Transition probability is defined as the proportion of agents that")
    print("went to an IDP camp first and then went to Cox's Bazar.")
    print()
    
    # Results storage
    results = {}
    
    # Process each instance type
    for instance_type in instance_types:
        mean_prob, std_prob, all_probs = process_instance_type(instance_type, results_dir)
        
        if mean_prob is not None:
            results[instance_type] = {
                'mean': mean_prob,
                'std': std_prob,
                'all_probabilities': all_probs,
                'num_runs': len(all_probs)
            }
    
    # Display results
    print("\n" + "="*50)
    print("TRANSITION PROBABILITY RESULTS")
    print("="*50)
    
    for instance_type, result in results.items():
        print(f"\n{instance_type.upper()}:")
        print(f"  Mean Transition Probability: {result['mean']:.4f} ({result['mean']*100:.2f}%)")
        print(f"  Standard Deviation:          {result['std']:.4f}")
        print(f"  Number of Runs:              {result['num_runs']}")
        print(f"  Individual Run Values:       {[f'{p:.4f}' for p in result['all_probabilities']]}")
    
    # Save results to CSV
    output_dir = project_dir / 'plots' / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create summary DataFrame
    summary_data = []
    for instance_type, result in results.items():
        summary_data.append({
            'Instance': instance_type,
            'Mean_Transition_Probability': result['mean'],
            'Std_Transition_Probability': result['std'],
            'Number_of_Runs': result['num_runs']
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = output_dir / 'transition_probability_summary.csv'
    summary_df.to_csv(summary_file, index=False)
    print(f"\nSummary saved to: {summary_file}")
    
    # Create detailed DataFrame with all individual run results
    detailed_data = []
    for instance_type, result in results.items():
        for i, prob in enumerate(result['all_probabilities'], 1):
            detailed_data.append({
                'Instance': instance_type,
                'Run': i,
                'Transition_Probability': prob
            })
    
    detailed_df = pd.DataFrame(detailed_data)
    detailed_file = output_dir / 'transition_probability_detailed.csv'
    detailed_df.to_csv(detailed_file, index=False)
    print(f"Detailed results saved to: {detailed_file}")
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
