import subprocess
import os
from search_space import get_random_architecture
from predictor import featurize
from generate_cpp import generate_cpp_from_architecture

from sklearn.ensemble import RandomForestRegressor
import numpy as np
import joblib

# config
NUM_DATAPOINTS_TO_GATHER = 1 # maybe 100? for demo, keep it small
VIVADO_SCRIPT = "./run_synthesis.sh" # Vivado setup script
TIMING_PREDICTOR_PATH = "timing_predictor.joblib" # saved time predictor path
POWER_PREDICTOR_PATH = "power_predictor.joblib" # saved power predictor path

# database for real data
real_data_X = [] # feature vectors
real_data_y_timing = [] # WNS values
real_data_y_power = [] # Power values 

# --- helper functions ---
def read_vivado_results(results_file_path='./build/results.txt'):
    """reads WNS, WHS, and power from the Vivado generated results.txt file."""
    wns = None
    whs = None # currently unused
    power = None
    try:
        with open(results_file_path, 'r') as f:
            for line in f:
                if line.startswith('WNS:'):
                    wns_str = line.split(':')[1].strip()
                    if wns_str != "N/A":
                        wns = float(wns_str)
                elif line.startswith('WHS:'):
                    whs_str = line.split(':')[1].strip()
                    if whs_str != "N/A":
                        whs = float(whs_str) 
                elif line.startswith('Power:'):
                    power_str = line.split(':')[1].strip()
                    if power_str != "N/A":
                        power = float(power_str)
        
        # error handling for missing values
        if wns is None:
            print(f"WARN: WNS not found or N/A in {results_file_path}")
        if power is None:
            print(f"WARN: Power not found or N/A in {results_file_path}")

        return wns, power

    except FileNotFoundError:
        print(f"ERROR: File {results_file_path} not found")
        return None, None
    except Exception as e:
        print(f"ERROR reading results file: {e}")
        return None, None

# --- main data collection loop ---
print(f"start data collection for {NUM_DATAPOINTS_TO_GATHER} architectures")

for i in range(NUM_DATAPOINTS_TO_GATHER):
    print(f"\n--- run {i+1}/{NUM_DATAPOINTS_TO_GATHER} ---")

    # 1. define random architecture and featurize it
    arch = get_random_architecture()
    features = featurize(arch)

    # 2. generate c++ code from architecture
    print(f"Architecture: {arch}")
    print(f"Features: {features}")
    print("Generating C++ code from architecture...")
    generate_cpp_from_architecture(arch)

    # 3. hardware run (HLS + Vivado synthesis)
    print("starting HLS + Vivado synthesis...")

    # cleanup old synthesis files
    if os.path.exists("vivado.log"): os.remove("vivado.log")
    if os.path.exists("build/"):
        subprocess.run(["rm", "-rf", "build/"])

    # start HLS + Vivado synthesis using shell script
    # catch errors if synthesis fails, and skip data point
    try:
        subprocess.run(["bash", VIVADO_SCRIPT], check=True) # print logs directly to console
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Synthesis script failed with return code {e.returncode}!")
        continue # skip data point
    print("Synthesis finished.")

    # 4. read results file and extract WNS and Power
    print("reading synthesis results.")
    wns, power = read_vivado_results('./build/results.txt')

    # error handling for missing/invalid results
    if wns is not None and power is not None:
        # for valid data point save features + wns + power
        print(f"SUCCESS: Real WNS: {wns:.2f} ns, Real Power: {power:.4f} W")
        real_data_X.append(features)
        real_data_y_timing.append(wns)
        real_data_y_power.append(power)
    else:
        print("ERROR: Failed to read valid WNS or Power from results file. Skipping data point.")
        if wns is None:
            print(" - WNS read failed or was N/A.")
        if power is None:
            print(" - Power read failed or was N/A.")


print("\n\n--- FINISHED DATA COLLECTION ---")
print(f"COLLECTED {len(real_data_y_timing)} VALID DATA POINTS FROM {NUM_DATAPOINTS_TO_GATHER} RUNS.")

# --- predictor training with real data ---
timing_predictor = None
power_predictor = None

# training with colected data
if not real_data_X:
    print("NO VALID DATA POINTS COLLECTED. SKIPPING PREDICTOR TRAINING.")
else:
    X_train = np.array(real_data_X)

    # train timing predictor
    if real_data_y_timing:
        print("start predictor training for TIMING (WNS) with REAL data.")
        y_timing_train = np.array(real_data_y_timing)
        timing_predictor = RandomForestRegressor()
        timing_predictor.fit(X_train, y_timing_train)
        print("Timing predictor successfully trained.")
        
        # saving 
        try:
            joblib.dump(timing_predictor, TIMING_PREDICTOR_PATH)
            print(f"Timing predictor saved to {TIMING_PREDICTOR_PATH}")
        except Exception as e:
            print(f"ERROR: Failed to save timing predictor: {e}")

    else:
        print("NO TIMING DATA POINTS. SKIPPING TIMING PREDICTOR TRAINING.")

    # train power predictor
    if real_data_y_power:
        print("start predictor training for POWER with REAL data.")
        y_power_train = np.array(real_data_y_power)
        power_predictor = RandomForestRegressor()
        power_predictor.fit(X_train, y_power_train)
        print("Power predictor successfully trained.")
        
        # saving
        try:
            joblib.dump(power_predictor, POWER_PREDICTOR_PATH)
            print(f"Power predictor saved to {POWER_PREDICTOR_PATH}")
        except Exception as e:
            print(f"ERROR: Failed to save power predictor: {e}")
        
    else:
        print("NO POWER DATA POINTS. SKIPPING POWER PREDICTOR TRAINING.")


# testing
if timing_predictor is not None or power_predictor is not None:
    print("\n--- TESTING PREDICTORS ---")
    print("testing predictor(s) with new random architecture.")
    test_arch = get_random_architecture()
    test_features = featurize(test_arch).reshape(1, -1)

    print(f"test architecture: {test_arch}")
    print(f"test features: {test_features}")

    # timing predictor
    if timing_predictor:
        predicted_wns = timing_predictor.predict(test_features)
        print(f"predicted timing (WNS): {predicted_wns[0]:.2f} ns")
    else:
        print("Timing predictor was not trained.")

    # power predictor
    if power_predictor:
        predicted_power = power_predictor.predict(test_features)
        print(f"predicted power: {predicted_power[0]:.4f} W")
    else:
        print("Power predictor was not trained.")
else:
    if not real_data_X:
        pass
    else:
        print("\nNo predictors were successfully trained, skipping test.")