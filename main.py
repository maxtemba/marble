import subprocess # runs shell commands
import os # file operations

from search_space import get_random_architecture 
from predictor import featurize                 
from parse_report import parse_timing_report

from sklearn.ensemble import RandomForestRegressor 
import numpy as np

# config
NUM_DATAPOINTS_TO_GATHER = 1 # maybe 100? For demo, keep it small
VIVADO_SCRIPT = "./run_synthesis.sh" # Vivado setup script
REPORT_FILE_PATH = "./build/timing_report.txt"

# database for real data
real_data_X = [] # feature vectors
real_data_y = [] # WNS values +-

print(f"start data collection for {NUM_DATAPOINTS_TO_GATHER} architectures")


for i in range(NUM_DATAPOINTS_TO_GATHER):
    print(f"\n--- run {i+1}/{NUM_DATAPOINTS_TO_GATHER} ---")
    
    # 1. define random architecture and featurize it
    arch = get_random_architecture()
    features = featurize(arch)
    
    # 2. ÜBERSETZE Architektur in Hardware-Code
    #    (!!!!! DAS IST DAS FEHLENDE BINDEGLIED !!!!!)
    #    Im Moment überspringen wir das und bauen *immer noch*
    #    das statische 'hello.v', nur um den Zyklus zu testen.
    
    # TODO: Hier kommt die Funktion hin:
    # write_hls_code_for_architecture(arch)
    
    print(f"Architektur: {arch}")
    print(f"Features: {features}")
    
    # 3. hardware run (Vivado synthesis)
    print("starting Vivado-Synthese...")
    # log cleanup 
    if os.path.exists("vivado.log"): os.remove("vivado.log")
    if os.path.exists("build/"): subprocess.run(["rm", "-rf", "build/"])
    
    # start Vivado synthesis using shell script
    # catch errors if vivado fails
    try:
        subprocess.run(["bash", VIVADO_SCRIPT], check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Vivado synthesis failed!")
        print(e.stderr)
        continue # Überspringe diesen Datenpunkt

    print("Synthesis finished.")

    # 4. read timing report and extract WNS using parser
    print("reading time report.")
    wns = parse_timing_report(REPORT_FILE_PATH)
    
    if wns is not None:
        # for valid data point, save features + wns
        print(f"ERFOLG: Echter WNS-Wert: {wns} ns")
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
    
    # importamnt for sklearn: convert to np arrays
    X_train = np.array(real_data_X)
    y_train = np.array(real_data_y)

    # train forest regressor as predictor
    real_predictor = RandomForestRegressor()
    real_predictor.fit(X_train, y_train)

    print(" predictor succesfully trained.")

    # 6. test predictor with a new random architecture
    print(" testing predictor with new random architecture.")
    test_arch = get_random_architecture()
    test_features = featurize(test_arch).reshape(1, -1)
    
    predicted_wns = real_predictor.predict(test_features)
    
    print(f"test architecture: {test_arch}")
    print(f"test feature: {test_features}")
    print(f"times (WNS): {predicted_wns[0]:.2f} ns")