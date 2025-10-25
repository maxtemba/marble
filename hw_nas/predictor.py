import numpy as np
from sklearn.ensemble import RandomForestRegressor
from .search_space import Architecture, get_random_architecture

# architecture to vector featurization translation
def featurize(arch: Architecture):
    total_depth = len(arch.blocks)
    
    # all features to extract
    total_convs = 0
    max_conv_out_channels = 0
    total_relu = 0
    total_max_pool = 0
    total_avg_pool = 0
    total_linear = 0
    max_linear_out_features = 0
    total_padding_same = 0
    total_padding_num = 0
    total_stride_1 = 0
    total_stride_2 = 0
    
    for block in arch.blocks:
        op_type = block.op_type
        params = block.params
        
        if op_type == 'conv':
            total_convs += 1
            max_conv_out_channels = max(max_conv_out_channels, params.get('out_channels', 0))
            
            # featurize padding
            if params.get('padding') == 'same':
                total_padding_same += 1
            elif isinstance(params.get('padding'), int):
                total_padding_num += params.get('padding')
                
            # featurize stride
            if params.get('stride') == 1:
                total_stride_1 += 1
            elif params.get('stride') == 2:
                total_stride_2 += 1
                
        elif op_type == 'relu':
            total_relu += 1
        elif op_type == 'max_pool':
            total_max_pool += 1
            # all max_pool ops have stride 2
            total_stride_2 += 1
        elif op_type == 'global_avg_pool':
            total_avg_pool += 1
        elif op_type == 'linear':
            total_linear += 1
            max_linear_out_features = max(max_linear_out_features, params.get('out_features', 0))

    
    # return final featurized vector
    return np.array([
        total_depth, 
        total_convs, 
        max_conv_out_channels,
        total_relu,
        total_max_pool,
        total_avg_pool,
        total_linear,
        max_linear_out_features,
        total_padding_same,
        total_padding_num,
        total_stride_1,
        total_stride_2
    ])