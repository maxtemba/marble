import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor

from hw_nas.search_space import get_random_architecture
from hw_nas.predictor import featurize

def train_predictors(real_data_X, real_data_y_timing, real_data_y_power, timing_path, power_path):
    """Trains and saves the timing and power predictors."""
    
    timing_predictor = None
    power_predictor = None

    # training with colected data
    if not real_data_X:
        print("NO VALID DATA POINTS COLLECTED. SKIPPING PREDICTOR TRAINING.")
        return None, None
    
    X_train = np.array(real_data_X)

    # train timing predictor
    if real_data_y_timing:
        print("start predictor training for TIMING (WNS) with REAL data.")
        y_timing_train = np.array(real_data_y_timing)
        timing_predictor = RandomForestRegressor(random_state=42) # Added random_state
        timing_predictor.fit(X_train, y_timing_train)
        print("Timing predictor successfully trained.")
        
        # saving 
        try:
            joblib.dump(timing_predictor, timing_path)
            print(f"Timing predictor saved to {timing_path}")
        except Exception as e:
            print(f"ERROR: Failed to save timing predictor: {e}")

    else:
        print("NO TIMING DATA POINTS. SKIPPING TIMING PREDICTOR TRAINING.")

    # train power predictor
    if real_data_y_power:
        print("start predictor training for POWER with REAL data.")
        y_power_train = np.array(real_data_y_power)
        power_predictor = RandomForestRegressor(random_state=42) # Added random_state
        power_predictor.fit(X_train, y_power_train)
        print("Power predictor successfully trained.")
        
        # saving
        try:
            joblib.dump(power_predictor, power_path)
            print(f"Power predictor saved to {power_path}")
        except Exception as e:
            print(f"ERROR: Failed to save power predictor: {e}")
        
    else:
        print("NO POWER DATA POINTS. SKIPPING POWER PREDICTOR TRAINING.")
        
    return timing_predictor, power_predictor


def test_trained_predictors(timing_predictor, power_predictor):
    """Tests the predictors that were just trained in memory."""
    
    if timing_predictor is None and power_predictor is None:
        if not (timing_predictor is not None or power_predictor is not None):
             print("\nNo predictors were successfully trained, skipping test.")
        return

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

