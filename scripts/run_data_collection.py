import sys
import os
import subprocess
import numpy as np
import joblib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from hw_nas.search_space import get_random_architecture
from hw_nas.predictor import featurize
from hw_nas.cpp_generator import generate_cpp_from_architecture
from hw_nas.data_collector import collect_single_datapoint
from hw_nas.predictor_trainer import train_predictors, test_trained_predictors

# config
NUM_DATAPOINTS_TO_GATHER = 1 # maybe 100? for demo, keep it small
VIVADO_SCRIPT = "hls_vivado/run_synthesis.sh" # Vivado setup script
TIMING_PREDICTOR_PATH = "data/saved_models/timing_predictor.joblib" # saved time predictor path
POWER_PREDICTOR_PATH = "data/saved_models/power_predictor.joblib" # saved power predictor path

CONFIG = {
    "VIVADO_SCRIPT": VIVADO_SCRIPT,
    "GENERATED_CPP_FILE": "hls_vivado/src/generated_design.cpp",
    "BUILD_DIR": "build",
    "RESULTS_FILE": "build/results.txt",
    "VIVADO_LOG": "build/vivado.log",         
    "VIVADO_JOU": "build/vivado.jou",         
    "HLS_OUTPUT_DIR": "build/top_function" 
}

def main():
    # database for real data
    real_data_X = [] # feature vectors
    real_data_y_timing = [] # WNS values
    real_data_y_power = [] # Power values 

    # --- main data collection loop ---
    print(f"start data collection for {NUM_DATAPOINTS_TO_GATHER} architectures")

    for i in range(NUM_DATAPOINTS_TO_GATHER):
        # pass the config and data lists to the collector function
        features, wns, power = collect_single_datapoint(
            i + 1, 
            NUM_DATAPOINTS_TO_GATHER, 
            CONFIG
        )
        
        if features is not None and wns is not None and power is not None:
            # for valid data point save features + wns + power
            print(f"SUCCESS: Real WNS: {wns:.2f} ns, Real Power: {power:.4f} W")
            real_data_X.append(features)
            real_data_y_timing.append(wns)
            real_data_y_power.append(power)
        else:
            print("Skipping this data point due to error.")


    print("\n\n--- FINISHED DATA COLLECTION ---")
    print(f"COLLECTED {len(real_data_y_timing)} VALID DATA POINTS FROM {NUM_DATAPOINTS_TO_GATHER} RUNS.")

    # --- predictor training with real data ---
    timing_predictor, power_predictor = train_predictors(
        real_data_X,
        real_data_y_timing,
        real_data_y_power,
        TIMING_PREDICTOR_PATH,
        POWER_PREDICTOR_PATH
    )

    # --- testing ---
    test_trained_predictors(timing_predictor, power_predictor)

if __name__ == "__main__":
    os.makedirs(os.path.dirname(TIMING_PREDICTOR_PATH), exist_ok=True)
    main()



