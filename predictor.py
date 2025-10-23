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

