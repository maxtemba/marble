import numpy as np
from sklearn.ensemble import RandomForestRegressor
from search_space import Architecture, get_random_architecture

# architecture to vector featurization translation
def featurize(arch: Architecture):
    total_convs = 0
    total_depth = len(arch.blocks)
    max_filter = 0
    
    for block in arch.blocks:
        if 'conv' in block.op_type:
            total_convs += 1
            max_filter = max(max_filter, block.params.get('filter', 0))
    
    return np.array([total_depth, total_convs, max_filter])

# TODO: replace with real data collection and training, dummy for now
print("generate dummy training data...")
X_train = []
y_train = [] # Dummy-Latenz

for _ in range(50): # 50 dummy-datenpoints
    arch = get_random_architecture()
    features = featurize(arch)
    
    # nonsensical dummy latency function
    dummy_latency = features[0] * 10 + features[2] * 0.5 
    
    X_train.append(features)
    y_train.append(dummy_latency)

# predictor training
print("Trainiere Prädiktor mit Dummy-Daten... 🧠")
predictor = RandomForestRegressor()
predictor.fit(X_train, y_train)

# predictor test
print("\n--- test predictor ---")
test_arch = get_random_architecture()
test_features = featurize(test_arch).reshape(1, -1) # sklearn expects 2D array

predicted_latency = predictor.predict(test_features)

print(f"test architectures: {test_arch}")
print(f"test featrues: {test_features}")
print(f"predicted latency: {predicted_latency[0]:.2f} ms")