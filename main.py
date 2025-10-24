import subprocess # runs shell commands
import os # file operations
from search_space import get_random_architecture
from predictor import featurize

from sklearn.ensemble import RandomForestRegressor
import numpy as np
from generate_cpp import generate_cpp_from_architecture

# config
NUM_DATAPOINTS_TO_GATHER = 1 # maybe 100? For demo, keep it small
VIVADO_SCRIPT = "./run_synthesis.sh" # Vivado setup script

# database for real data
real_data_X = [] # feature vectors
real_data_y_timing = [] # WNS values +-  <-- Renamed from real_data_y
real_data_y_power = [] # Power values <-- New list

# Modified function to read WNS and Power from results.txt
def read_vivado_results(results_file_path='./build/results.txt'):
    """Reads WNS, WHS, and Power from the Vivado generated results.txt file."""
    wns = None
    whs = None # You can store/use WHS if needed
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
                         whs = float(whs_str) # Store WHS if needed, currently unused
                elif line.startswith('Power:'): # <-- Read Power
                    power_str = line.split(':')[1].strip()
                    if power_str != "N/A":
                        power = float(power_str)

        # Add warnings if values couldn't be parsed (optional but helpful)
        if wns is None:
            print(f"WARN: WNS not found or N/A in {results_file_path}")
        if power is None:
            print(f"WARN: Power not found or N/A in {results_file_path}")

        return wns, power # Return both values

    except FileNotFoundError:
        print(f"ERROR: File {results_file_path} not found")
        return None, None
    except Exception as e:
        print(f"ERROR reading results file: {e}")
        return None, None

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

    # log cleanup - Modified to remove build directory entirely for cleaner runs
    if os.path.exists("vivado.log"): os.remove("vivado.log")
    if os.path.exists("build/"):
        subprocess.run(["rm", "-rf", "build/"]) # Ensures clean state

    # start HLS + Vivado synthesis using shell script
    # catch errors if synthesis fails, and skip data point
    try:
        # Removed capture_output=True to show logs directly
        subprocess.run(["bash", VIVADO_SCRIPT], check=True) # Logs will print here
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Synthesis script failed with return code {e.returncode}!")
        # The script's error output should appear directly in the console now.
        continue # Skip this data point

    print("Synthesis finished.")

    # 4. read results file and extract WNS and Power
    print("reading synthesis results.")
    wns, power = read_vivado_results('./build/results.txt')

    # Check if *both* values were successfully read before appending
    if wns is not None and power is not None:
        # for valid data point, save features + wns + power
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

# Initialize predictors outside the conditional block
timing_predictor = None
power_predictor = None

# 5. predictor training with real data
if not real_data_X:
    print("NO VALID DATA POINTS COLLECTED. SKIPPING PREDICTOR TRAINING.")
else:
    X_train = np.array(real_data_X)

    # Train timing predictor
    if real_data_y_timing:
        print("start predictor training for TIMING (WNS) with REAL data.")
        y_timing_train = np.array(real_data_y_timing)
        timing_predictor = RandomForestRegressor()
        timing_predictor.fit(X_train, y_timing_train)
        print("Timing predictor successfully trained.")
    else:
        print("NO TIMING DATA POINTS. SKIPPING TIMING PREDICTOR TRAINING.")

    # Train power predictor
    if real_data_y_power:
        print("start predictor training for POWER with REAL data.")
        y_power_train = np.array(real_data_y_power)
        power_predictor = RandomForestRegressor()
        power_predictor.fit(X_train, y_power_train)
        print("Power predictor successfully trained.")
    else:
         print("NO POWER DATA POINTS. SKIPPING POWER PREDICTOR TRAINING.")


# 6. test predictors with a new random architecture
if timing_predictor is not None or power_predictor is not None:
    print("\n--- TESTING PREDICTORS ---")
    print("testing predictor(s) with new random architecture.")
    test_arch = get_random_architecture()
    test_features = featurize(test_arch).reshape(1, -1)

    print(f"test architecture: {test_arch}")
    print(f"test features: {test_features}")

    # Test timing predictor
    if timing_predictor:
        predicted_wns = timing_predictor.predict(test_features)
        print(f"predicted timing (WNS): {predicted_wns[0]:.2f} ns")
    else:
        print("Timing predictor was not trained.")

    # Test power predictor
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