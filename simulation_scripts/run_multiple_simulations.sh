#!/bin/bash

# Bash job file to run FabSim3 simulations 10 times for each instance
# Usage: ./run_multiple_simulations.sh

# Configuration
SIMULATION_PERIOD=15
NUM_RUNS=10
TIMING_CSV="simulation_timing.csv"

# Instance names to run
INSTANCES=(
    "myanmar2017"
    "myanmar2017_demo"
    "myanmar2017_network"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

print_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to initialize timing CSV
initialize_timing_csv() {
    echo "instance_name,run_number,real_time,user_time,sys_time" > "$TIMING_CSV"
    print_status "Created timing CSV file: $TIMING_CSV"
}

# Function to parse time output and append to CSV
record_timing() {
    local instance_name=$1
    local run_number=$2
    local time_output=$3
    
    # Parse the time output (format: real 1m23.456s user 0m12.345s sys 0m1.234s)
    local real_time=$(echo "$time_output" | grep -o 'real[[:space:]]*[0-9]*m[0-9]*\.[0-9]*s' | grep -o '[0-9]*m[0-9]*\.[0-9]*s')
    local user_time=$(echo "$time_output" | grep -o 'user[[:space:]]*[0-9]*m[0-9]*\.[0-9]*s' | grep -o '[0-9]*m[0-9]*\.[0-9]*s')
    local sys_time=$(echo "$time_output" | grep -o 'sys[[:space:]]*[0-9]*m[0-9]*\.[0-9]*s' | grep -o '[0-9]*m[0-9]*\.[0-9]*s')
    
    # Convert to seconds for easier analysis
    real_seconds=$(convert_time_to_seconds "$real_time")
    user_seconds=$(convert_time_to_seconds "$user_time")
    sys_seconds=$(convert_time_to_seconds "$sys_time")
    
    # Append to CSV
    echo "$instance_name,$run_number,$real_seconds,$user_seconds,$sys_seconds" >> "$TIMING_CSV"
    print_info "Recorded timing: Real=${real_seconds}s, User=${user_seconds}s, Sys=${sys_seconds}s"
}

# Function to convert time format (1m23.456s) to seconds
convert_time_to_seconds() {
    local time_str=$1
    if [[ $time_str =~ ([0-9]+)m([0-9]+\.[0-9]+)s ]]; then
        local minutes=${BASH_REMATCH[1]}
        local seconds=${BASH_REMATCH[2]}
        # Convert using bash arithmetic (multiply minutes by 60 and add seconds)
        local total_seconds=$(awk "BEGIN {printf \"%.3f\", $minutes * 60 + $seconds}")
        echo "$total_seconds"
    else
        echo "0"
    fi
}

# Function to check if directory exists and delete it
cleanup_localhost_exe() {
    local target_dir="FabSim3/localhost_exe/FabSim"
    
    if [ -d "$target_dir" ]; then
        print_status "Cleaning up $target_dir..."
        rm -rf "$target_dir"
        print_status "Cleanup completed."
    else
        print_info "Directory $target_dir does not exist, skipping cleanup."
    fi
}

# Function to run simulation
run_simulation() {
    local instance_name=$1
    local run_number=$2
    
    print_status "Starting simulation for $instance_name (Run $run_number/$NUM_RUNS)..."
    
    # Change to FabSim3 directory
    cd FabSim3 || {
        print_error "Failed to change to FabSim3 directory"
        return 1
    }
    
    # Run the simulation with timing
    print_info "Running: fabsim localhost pflee:$instance_name,simulation_period=$SIMULATION_PERIOD"
    
    # Capture timing information
    local temp_time_file=$(mktemp)
    { time fabsim localhost pflee:"$instance_name",simulation_period=$SIMULATION_PERIOD; } 2> "$temp_time_file"
    local sim_exit_code=$?
    local time_output=$(cat "$temp_time_file")
    rm "$temp_time_file"
    
    if [ $sim_exit_code -ne 0 ]; then
        print_error "Simulation failed for $instance_name (Run $run_number)"
        cd ..
        return 1
    fi
    
    print_status "Simulation completed successfully."
    
    # Record timing information
    record_timing "$instance_name" "$run_number" "$time_output"
    
    # Fetch results
    print_info "Fetching results..."
    fabsim localhost fetch_results
    
    if [ $? -ne 0 ]; then
        print_error "Failed to fetch results for $instance_name (Run $run_number)"
        cd ..
        return 1
    fi
    
    print_status "Results fetched successfully."
    
    # Change back to parent directory
    cd ..
    
    return 0
}

# Function to rename results folder
rename_results() {
    local instance_name=$1
    local run_number=$2
    local results_dir="FabSim3/results"
    local target_name="${instance_name}_run_${run_number}"
    
    if [ -d "$results_dir" ]; then
        # Find the most recently created directory in results
        local latest_dir=$(ls -t "$results_dir" | head -n 1)
        
        if [ -n "$latest_dir" ] && [ -d "$results_dir/$latest_dir" ]; then
            print_status "Renaming $results_dir/$latest_dir to $target_name..."
            mv "$results_dir/$latest_dir" "$results_dir/$target_name"
            print_status "Results folder renamed successfully."
        else
            print_error "No simulation results found in $results_dir!"
            return 1
        fi
    else
        print_error "Results directory $results_dir not found!"
        return 1
    fi
}

# Function to run all simulations for one instance
run_instance_simulations() {
    local instance_name=$1
    
    print_status "Starting simulations for instance: $instance_name"
    print_status "Will run $NUM_RUNS simulations with simulation_period=$SIMULATION_PERIOD"
    
    for ((i=1; i<=NUM_RUNS; i++)); do
        print_status "=== Starting Run $i/$NUM_RUNS for $instance_name ==="
        
        # Step 1: Cleanup
        cleanup_localhost_exe
        
        # Step 2: Run simulation
        if ! run_simulation "$instance_name" "$i"; then
            print_error "Simulation $i failed for $instance_name. Continuing with next run..."
            continue
        fi
        
        # Step 3: Rename results
        if ! rename_results "$instance_name" "$i"; then
            print_error "Failed to rename results for $instance_name run $i. Continuing..."
            continue
        fi
        
        print_status "=== Completed Run $i/$NUM_RUNS for $instance_name ==="
        
        # Brief pause between runs
        sleep 2
    done
    
    print_status "All simulations completed for instance: $instance_name"
}

# Move the FabSim3/results folder to a new location
move_results() {
    local results_dir="FabSim3/results"
    local target_dir="rohingya-flee/results"

    if [ -d "$results_dir" ]; then
        print_status "Moving results from $results_dir to $target_dir..."
        mv "$results_dir" "$target_dir"
        print_status "Results moved successfully."
    else
        print_error "Results directory $results_dir not found!"
        return 1
    fi
}

# Main execution
main() {
    print_status "Starting FabSim3 multiple simulation job"
    print_info "Instances to run: ${INSTANCES[*]}"
    print_info "Number of runs per instance: $NUM_RUNS"
    print_info "Simulation period: $SIMULATION_PERIOD days"
    
    # Check if we're in the right directory
    if [ ! -d "FabSim3" ]; then
        print_error "FabSim3 directory not found. Please run this script from the IndividualProject directory."
        exit 1
    fi
    
    # Initialize timing CSV
    initialize_timing_csv
    
    # Record start time
    START_TIME=$(date +%s)
    
    # Run simulations for each instance
    for instance in "${INSTANCES[@]}"; do
        print_status "Processing instance: $instance"
        run_instance_simulations "$instance"
        print_status "Finished processing instance: $instance"
        echo ""
    done
    
    # Calculate total runtime
    END_TIME=$(date +%s)
    TOTAL_TIME=$((END_TIME - START_TIME))
    HOURS=$((TOTAL_TIME / 3600))
    MINUTES=$(((TOTAL_TIME % 3600) / 60))
    SECONDS=$((TOTAL_TIME % 60))
    
    print_status "All simulations completed!"
    print_info "Total runtime: ${HOURS}h ${MINUTES}m ${SECONDS}s"
    print_info "Timing data saved to: $TIMING_CSV"
    print_info "Results folders created:"
    
    # List all created result folders
    for instance in "${INSTANCES[@]}"; do
        for ((i=1; i<=NUM_RUNS; i++)); do
            result_folder="${instance}_run_${i}"
            if [ -d "$result_folder" ]; then
                print_info "  - $result_folder"
            fi
        done
    done

    # Move the results to a new location
    move_results
}

# Trap to handle script interruption
trap 'print_warning "Script interrupted by user. Cleaning up..."; exit 1' INT TERM

# Run main function
main "$@"
