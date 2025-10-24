import subprocess
import os

# Import from other files in the hw_nas package
from hw_nas.search_space import get_random_architecture
from hw_nas.predictor import featurize
from hw_nas.cpp_generator import generate_cpp_from_architecture
from hw_nas.utils import read_vivado_results

def _run_synthesis_script(config):
    """Internal helper to run the synthesis script."""
    print("starting HLS + Vivado synthesis...")

    # cleanup old synthesis files
    if os.path.exists(config["VIVADO_LOG"]): os.remove(config["VIVADO_LOG"])
    if os.path.exists(config["VIVADO_JOU"]): os.remove(config["VIVADO_JOU"])
    if os.path.exists(config["BUILD_DIR"]):
        subprocess.run(["rm", "-rf", config["BUILD_DIR"]])
    if os.path.exists(config["HLS_OUTPUT_DIR"]):
         subprocess.run(["rm", "-rf", config["HLS_OUTPUT_DIR"]])

    # start HLS + Vivado synthesis using shell script
    # catch errors if synthesis fails, and skip data point
    try:
        # Run the script from the project root.
        # The script itself will cd to its own dir.
        subprocess.run(["bash", config["VIVADO_SCRIPT"]], check=True) # print logs directly to console
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Synthesis script failed with return code {e.returncode}!")
        return False # Indicate failure
    except FileNotFoundError:
        print(f"ERROR: Synthesis script not found at {config['VIVADO_SCRIPT']}")
        return False
        
    print("Synthesis finished.")
    return True # Indicate success

def collect_single_datapoint(iteration, total_iterations, config):
    """
    Runs one data collection cycle.
    Returns (features, wns, power) on success, or (None, None, None) on failure.
    """
    print(f"\n--- run {iteration}/{total_iterations} ---")

    # 1. define random architecture and featurize it
    arch = get_random_architecture()
    features = featurize(arch)

    # 2. generate c++ code from architecture
    print(f"Architecture: {arch}")
    print(f"Features: {features}")
    print("Generating C++ code from architecture...")
    try:
        generate_cpp_from_architecture(arch, config["GENERATED_CPP_FILE"])
    except Exception as e:
        print(f"ERROR: C++ generation failed: {e}")
        return None, None, None

    # 3. hardware run (HLS + Vivado synthesis)
    success = _run_synthesis_script(config)
    if not success:
        return None, None, None # Synthesis failed

    # 4. read results file and extract WNS and Power
    print("reading synthesis results.")
    wns, power = read_vivado_results(config["RESULTS_FILE"])

    # error handling for missing/invalid results
    if wns is None or power is None:
        print("ERROR: Failed to read valid WNS or Power from results file.")
        if wns is None:
            print(" - WNS read failed or was N/A.")
        if power is None:
            print(" - Power read failed or was N/A.")
        return None, None, None
    
    # Success! Return the collected data
    return features, wns, power

