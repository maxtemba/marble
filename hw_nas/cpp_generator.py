import math

# max buffer size (must match ops.cpp)
MAX_FEAT_SIZE = 32 * 32 * 128

def generate_cpp_from_architecture(arch, output_file="generated_design.cpp"):
    """
    Generates a simple ++ file from an Architecture object
    for HLS synthesis testing and predictor data collection.
    """
    
    with open(output_file, 'w') as f:
        f.write(f"// Auto-generated HLS design\n")
        f.write(f"// Arch: {arch}\n")
        f.write("#include <cstddef>\n\n")
        
        # HLS sizing constraint
        f.write(f"#define MAX_FEAT_SIZE {MAX_FEAT_SIZE}\n\n")

        # function declarations from ops.cpp
        f.write("void relu(float* data, int size);\n")
        f.write("void max_pool(float* input, float* output, int in_channels, int in_h, int in_w, int stride);\n") 
        f.write("void avg_pool(float* input, float* output, int in_channels, int in_h, int in_w);\n")
        f.write("void linear(float* input, float* output, const float* weights, const float* bias, int in_features, int out_features);\n")
        f.write("void conv(float* input, float* output, const float* weights, const float* bias, int in_channels, int out_channels, int kernel_size, int in_h, int in_w, int out_h, int out_w, int stride);\n\n") 
        
        # placeholder weights to match function signatures
        f.write("const float dummy_weights[1] = {0.0f};\n")
        f.write("const float dummy_bias[1] = {0.0f};\n\n")

        # main top function
        f.write("void top_function(float* input_gmem, float* output_gmem) {\n")
        
        # important for HLS?? TODO: verify necessity
        f.write("    #pragma HLS INTERFACE m_axi port=input_gmem bundle=gmem0 depth=MAX_FEAT_SIZE\n")
        f.write("    #pragma HLS INTERFACE m_axi port=output_gmem bundle=gmem1 depth=MAX_FEAT_SIZE\n")
        f.write("    #pragma HLS INTERFACE s_axilite port=return\n\n")
        
        # --- Single Buffer for all operations ---
        f.write(f"    static float buffer[MAX_FEAT_SIZE];\n")
        f.write("    #pragma HLS BIND_STORAGE variable=buffer type=RAM_2P\n\n")

        # --- 5. Generate Layer Calls ---
        
        # Track data shape
        current_channels = 3  # Start with RGB
        current_h = 32
        current_w = 32
        current_features = 0  # for linear layers
        is_linear = False     # Flag to track if we're in 1D (linear) mode
        
        # Load initial data from memory
        f.write(f"    int load_size = {current_channels * current_h * current_w};\n")
        f.write(f"    if (load_size > MAX_FEAT_SIZE) load_size = MAX_FEAT_SIZE;\n")
        f.write(f"    for(int i=0; i < load_size; ++i) buffer[i] = input_gmem[i];\n\n")

        for i, block in enumerate(arch.blocks):
            op_type = block.op_type
            params = block.params
            f.write(f"    // --- Block {i}: {op_type} ---\n")
            
            if op_type == 'conv':
                out_channels = params['out_channels']
                kernel_size = params['kernel_size']
                padding = params.get('padding', 0)
                stride = params.get('stride', 1) 
                
                # Calculate output shape
                if padding == 'same':
                    out_h = math.ceil(current_h / stride)
                    out_w = math.ceil(current_w / stride)
                else:
                    padding_int = padding
                    out_h = math.floor((current_h - kernel_size + 2 * padding_int) / stride) + 1
                    out_w = math.floor((current_w - kernel_size + 2 * padding_int) / stride) + 1
                
                f.write(f"    conv(buffer, buffer, dummy_weights, dummy_bias, {current_channels}, {out_channels}, {kernel_size}, {current_h}, {current_w}, {out_h}, {out_w}, {stride});\n") 
                
                # Update shape
                current_channels = out_channels
                current_h, current_w = out_h, out_w
                current_features = 0
                is_linear = False
                
            elif op_type == 'relu':
                size = current_features if is_linear else (current_channels * current_h * current_w)
                if size <= 0: size = MAX_FEAT_SIZE
                if size > MAX_FEAT_SIZE: size = MAX_FEAT_SIZE
                f.write(f"    relu(buffer, {size}); // In-place\n")

            elif op_type == 'max_pool':
                kernel_size = params.get('kernel_size', 2)
                stride = params.get('stride', 2) 
                
                out_h = math.floor((current_h - kernel_size) / stride) + 1
                out_w = math.floor((current_w - kernel_size) / stride) + 1
                
                f.write(f"    max_pool(buffer, buffer, {current_channels}, {current_h}, {current_w}, {stride});\n")
                
                current_h, current_w = out_h, out_w
                current_features = 0
                is_linear = False

            elif op_type == 'global_avg_pool':
                f.write(f"    avg_pool(buffer, buffer, {current_channels}, {current_h}, {current_w});\n")
                
                current_h, current_w = 1, 1
                current_features = current_channels 
                is_linear = True
            
            elif op_type == 'flatten':
                current_features = current_channels * current_h * current_w
                f.write(f"    // Flatten: No C++ op needed\n")
                is_linear = True
                
            elif op_type == 'linear':
                in_features = params['in_features']
                out_features = params['out_features']
                
                if in_features == 0: in_features = current_features # Get last layer's features
                
                f.write(f"    linear(buffer, buffer, dummy_weights, dummy_bias, {in_features}, {out_features});\n")
                
                current_features = out_features
                is_linear = True
            
            f.write("\n") # Add a newline for readability

        # --- 6. Write final result back to global memory ---
        f.write(f"    // Write final result from buffer back to gmem\n")
        f.write(f"    int out_size = {current_features};\n")
        f.write(f"    if (out_size <= 0 || out_size > MAX_FEAT_SIZE) out_size = MAX_FEAT_SIZE;\n")
        f.write(f"    for(int i=0; i < out_size; ++i) output_gmem[i] = buffer[i];\n")
        f.write("}\n")
    
    print(f"Generated C++ file: {output_file}")
    return output_file