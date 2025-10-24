import joblib
import os
import numpy as np
import sys  # <-- Add this

# --- FIX: Add project root to Python path ---
# This allows imports from the 'hw_nas' package
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)
# --- End of FIX ---

from hw_nas.search_space import get_random_architecture
from hw_nas.predictor import featurize

# --- Configuration ---
# Paths are relative to the project root
TIMING_PREDICTOR_PATH = "data/saved_models/timing_predictor.joblib"
POWER_PREDICTOR_PATH = "data/saved_models/power_predictor.joblib"

def main():
    """
    Loads trained predictors and tests them with a new random architecture.
    """
    print("--- LOADING PREDICTORS ---")

    timing_predictor = None
    power_predictor = None

    # Load timing predictor
    if os.path.exists(TIMING_PREDICTOR_PATH):
        try:
            timing_predictor = joblib.load(TIMING_PREDICTOR_PATH)
            print(f"Successfully loaded timing predictor from {TIMING_PREDICTOR_PATH}")
        except Exception as e:
            print(f"ERROR: Failed to load timing predictor: {e}")
    else:
        print(f"WARN: Timing predictor file not found at {TIMING_PREDICTOR_PATH}")

    # Load power predictor
    if os.path.exists(POWER_PREDICTOR_PATH):
        try:
            power_predictor = joblib.load(POWER_PREDICTOR_PATH)
            print(f"Successfully loaded power predictor from {POWER_PREDICTOR_PATH}")
        except Exception as e:
            print(f"ERROR: Failed to load power predictor: {e}")
    else:
        print(f"WARN: Power predictor file not found at {POWER_PREDICTOR_PATH}")


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
            print("Timing predictor was not loaded.")

        # power predictor
        if power_predictor:
            predicted_power = power_predictor.predict(test_features)
            print(f"predicted power: {predicted_power[0]:.4f} W")
        else:
            print("Power predictor was not loaded.")
    else:
        print("\nNo predictors were loaded, skipping test.")

if __name__ == "__main__":
    main()

