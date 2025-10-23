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
real_data_y = [] # WNS values +-

def read_wns_from_file(wns_file_path='./build/wns.txt'):
    """Liest WNS aus der von Vivado generierten wns.txt Datei."""
    try:
        with open(wns_file_path, 'r') as f:
            for line in f:
                if line.startswith('WNS:'):
                    wns_str = line.split(':')[1].strip()
                    return float(wns_str)
        print(f"ERROR: WNS not found in {wns_file_path}")
        return None
    except FileNotFoundError:
        print(f"ERROR: File {wns_file_path} not found")
        return None
    except Exception as e:
        print(f"ERROR reading WNS file: {e}")
        return None


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
    
    # log cleanup
    if os.path.exists("vivado.log"): os.remove("vivado.log")
    if os.path.exists("build/"): subprocess.run(["rm", "-rf", "build/"])
    
    # start HLS + Vivado synthesis using shell script
    # catch errors if synthesis fails, and skip data point
    try:
        subprocess.run(["bash", VIVADO_SCRIPT], check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Synthesis failed!")
        if e.stderr:
            print(e.stderr)
        continue # Skip this data point
    
    print("Synthesis finished.")
    
    # 4. read timing report and extract WNS using parser function, TODO change to real parser, change build directory
    print("reading timing report.")
    wns = read_wns_from_file('./build/wns.txt')

    
    if wns is not None:
        # for valid data point, save features + wns
        print(f"SUCCESS: Real WNS value: {wns} ns")
        real_data_X.append(features)
        real_data_y.append(wns)
    else:
        print("ERROR: WNS read failed")

print("\n\n--- FINISHED DATA COLLECTION ---")
print(f"GOT {len(real_data_y)} from {NUM_DATAPOINTS_TO_GATHER} DATA POINTS.")

if not real_data_y:
    print("NO DATA POINTS. SKIPPING PREDICTOR TRAINING.")
else:
    # 5. predictor training with real data
    print("start predictor training with REAL data.")
    
    # important for sklearn: convert to np arrays
    X_train = np.array(real_data_X)
    y_train = np.array(real_data_y)
    
    # train forest regressor as predictor
    real_predictor = RandomForestRegressor()
    real_predictor.fit(X_train, y_train)
    
    print("predictor successfully trained.")
    
    # 6. test predictor with a new random architecture
    print("testing predictor with new random architecture.")
    test_arch = get_random_architecture()
    test_features = featurize(test_arch).reshape(1, -1)
    predicted_wns = real_predictor.predict(test_features)
    
    print(f"test architecture: {test_arch}")
    print(f"test feature: {test_features}")
    print(f"predicted timing (WNS): {predicted_wns[0]:.2f} ns")
