# generate_cpp.py
# Generates a top-level C++ file calling REALISTIC HLS functions
# and embedding DUMMY weights/biases for synthesis.

import math

# --- DUMMY WEIGHT/BIAS ARRAYS ---
# We need HLS to "see" weights and biases to synthesize
# BRAMs and DSPs correctly. These are placeholders.
# We create one large dummy array for all weights.
MAX_WEIGHT_SIZE = 128 * 128 * 5 * 5 # ~400k
MAX_BIAS_SIZE = 1024

# Create the C++ string for these dummy arrays
DUMMY_WEIGHTS_CPP = f"const float dummy_weights[MAX_WEIGHT_SIZE] = {{ 0.1f }};\n"
DUMMY_BIAS_CPP = f"const float dummy_bias[MAX_BIAS_SIZE] = {{ 0.1f }};\n"

# --- MAX BUFFER SIZE (must match ops.cpp) ---
MAX_FEAT_SIZE = 32 * 32 * 128


def generate_cpp_from_architecture(arch, output_file="generated_design.cpp"):
    """
    Generate C++ code that calls realistic HLS functions
    with parameters from the architecture.
    """
    
    with open(output_file, 'w') as f:
        f.write("// Auto-generated realistic HLS design\n")
        f.write("// Architecture: " + str(arch) + "\n")
        f.write("#include <cstddef>\n\n")
        
        # --- 1. Define HLS Sizing Constants ---
        f.write(f"#define MAX_FEAT_SIZE {MAX_FEAT_SIZE}\n")
        f.write(f"#define MAX_WEIGHT_SIZE {MAX_WEIGHT_SIZE}\n")
        f.write(f"#define MAX_BIAS_SIZE {MAX_BIAS_SIZE}\n\n")

        # --- 2. Write placeholder function declarations (must match ops.cpp) ---
        f.write("// --- REAL HLS Function Declarations ---\n")
        f.write("void relu(float* data, int size);\n")
        f.write("void max_pool(float* input, float* output, int in_channels, int in_h, int in_w, int stride);\n") 
        f.write("void avg_pool(float* input, float* output, int in_channels, int in_h, int in_w);\n")
        f.write("void linear(float* input, float* output, const float* weights, const float* bias, int in_features, int out_features);\n")
        f.write("void conv(float* input, float* output, const float* weights, const float* bias, int in_channels, int out_channels, int kernel_size, int in_h, int in_w, int out_h, int out_w, int stride);\n\n") 

        # --- 3. Write the DUMMY embedded weights ---
        f.write("// --- Dummy Weights/Biases for Synthesis ---\n")
        f.write(DUMMY_WEIGHTS_CPP)
        f.write(DUMMY_BIAS_CPP)

        # --- 4. Write top function ---
        f.write("\nvoid top_function(float* input_gmem, float* output_gmem) {\n")
        
        # --- Pragmas for global memory ---
        # Note: We change the interface to simple pointers
        f.write("    #pragma HLS INTERFACE m_axi port=input_gmem bundle=gmem0 depth=MAX_FEAT_SIZE\n")
        f.write("    #pragma HLS INTERFACE m_axi port=output_gmem bundle=gmem1 depth=MAX_FEAT_SIZE\n")
        f.write("    #pragma HLS INTERFACE s_axilite port=return\n\n")
        
        # --- Buffers for intermediate results (Ping-Pong) ---
        f.write("    // Buffers to hold feature maps between layers\n")
        f.write(f"    static float buffer_a[MAX_FEAT_SIZE];\n")
        f.write(f"    static float buffer_b[MAX_FEAT_SIZE];\n")
        f.write("    #pragma HLS BIND_STORAGE variable=buffer_a type=RAM_2P\n")
        f.write("    #pragma HLS BIND_STORAGE variable=buffer_b type=RAM_2P\n\n")
        
        # --- FIX: Pointers for Ping-Pong Buffering ---
        f.write("    // --- Pointers for Ping-Pong Buffering ---\n")
        f.write("    float* in_buf = buffer_a;\n")
        f.write("    float* out_buf = buffer_b;\n")
        f.write("    float* temp; // <-- DECLARE TEMP POINTER ONCE\n\n")


        # --- 5. Generate calls to REAL HLS functions ---
        
        # We must track the data dimensions through the network
        # This is CRITICAL for validity.
        current_channels = 3  # Start with RGB
        current_h = 32
        current_w = 32
        current_features = 0  # for linear layers
        
        
        f.write(f"    // Manually load from gmem to local BRAM (simplified)\n")
        # Ensure we don't read more than MAX_FEAT_SIZE
        f.write(f"    int load_size = {current_channels*current_h*current_w};\n")
        f.write(f"    if (load_size > MAX_FEAT_SIZE) load_size = MAX_FEAT_SIZE;\n")
        f.write(f"    for(int i=0; i< load_size; ++i) buffer_a[i] = input_gmem[i];\n\n")
        

        for i, block in enumerate(arch.blocks):
            op_type = block.op_type
            params = block.params
            f.write(f"    // --- Block {i}: {op_type} ---\n")
            
            if op_type == 'conv':
                out_channels = params['out_channels']
                kernel_size = params['kernel_size']
                padding = params.get('padding', 0)
                stride = params.get('stride', 1) 
                
                # Calculate output dimensions
                if padding == 'same':
                    padding_int = kernel_size // 2
                    out_h = math.ceil(current_h / stride)
                    out_w = math.ceil(current_w / stride)
                else:
                    padding_int = padding
                    out_h = math.floor((current_h - kernel_size + 2 * padding_int) / stride) + 1
                    out_w = math.floor((current_w - kernel_size + 2 * padding_int) / stride) + 1
                
                f.write(f"    conv(in_buf, out_buf, dummy_weights, dummy_bias, {current_channels}, {out_channels}, {kernel_size}, {current_h}, {current_w}, {out_h}, {out_w}, {stride});\n") 
                
                # Update state for next layer
                current_channels = out_channels
                current_h, current_w = out_h, out_w
                current_features = 0 # Back in 2D mode
                
            elif op_type == 'relu':
                size = current_channels * current_h * current_w
                if current_features > 0: # Check if we are in linear mode
                    size = current_features
                if size <= 0: size = MAX_FEAT_SIZE # Safety default
                if size > MAX_FEAT_SIZE: size = MAX_FEAT_SIZE
                    
                f.write(f"    relu(in_buf, {size}); // In-place ReLU\n")
                # State unchanged, but we copy data to out_buf if it was in-place
                f.write(f"    if (in_buf != out_buf) for(int i=0; i<{size}; ++i) {{ out_buf[i] = in_buf[i]; }}\n")

            elif op_type == 'max_pool':
                kernel_size = params.get('kernel_size', 2)
                stride = params.get('stride', 2) 
                
                out_h = math.floor((current_h - kernel_size) / stride) + 1
                out_w = math.floor((current_w - kernel_size) / stride) + 1
                
                f.write(f"    max_pool(in_buf, out_buf, {current_channels}, {current_h}, {current_w}, {stride});\n")
                
                # Update state
                current_h, current_w = out_h, out_w
                current_features = 0 # Back in 2D mode

            elif op_type == 'global_avg_pool':
                f.write(f"    avg_pool(in_buf, out_buf, {current_channels}, {current_h}, {current_w});\n")
                
                # Update state
                current_h, current_w = 1, 1
                current_features = current_channels # Output is now 1D
                current_channels = 0 # No longer in 2D mode
            
            elif op_type == 'flatten':
                current_features = current_channels * current_h * current_w
                if current_features == 0: # Safety check if we already flattened
                    current_features = params.get('in_features', 128)
                    
                current_channels = 0 # No longer in 2D mode
                current_h, current_w = 0, 0
                
                f.write(f"    // Flatten: No C++ op, just change buffer interpretation\n")
                # Copy data to keep ping-pong logic simple
                if current_features > MAX_FEAT_SIZE: current_features = MAX_FEAT_SIZE
                if current_features <= 0: current_features = MAX_FEAT_SIZE # Safety
                f.write(f"    if (in_buf != out_buf) for(int i=0; i<{current_features}; ++i) {{ out_buf[i] = in_buf[i]; }}\n")
                
            elif op_type == 'linear':
                in_features = params['in_features']
                out_features = params['out_features']
                
                # Safety check for feature size
                if in_features == 0: in_features = current_features
                if in_features <= 0: in_features = 512 # Failsafe
                
                f.write(f"    linear(in_buf, out_buf, dummy_weights, dummy_bias, {in_features}, {out_features});\n")
                
                # Update state
                current_features = out_features
                current_channels = 0 # No longer in 2D mode
                current_h, current_w = 0, 0
            
            # --- FIX: Swap Pointers (Ping-Pong) ---
            f.write("    // --- Swap pointers for next layer ---\n")
            f.write(f"    temp = in_buf; in_buf = out_buf; out_buf = temp;\n\n") # <-- ASSIGN, DO NOT RE-DECLARE

        # --- 6. Write final result back to global memory ---
        # The final result is in in_buf (due to the last swap)
        f.write(f"    // Write final result from in_buf back to gmem\n")
        f.write(f"    int out_size = {current_features};\n")
        f.write(f"    if (out_size <= 0) out_size = MAX_FEAT_SIZE;\n") # Failsafe
        f.write(f"    if (out_size > MAX_FEAT_SIZE) out_size = MAX_FEAT_SIZE;\n")
        f.write(f"    for(int i=0; i< out_size; ++i) output_gmem[i] = in_buf[i];\n")
        f.write("}\n")
    
    print(f"Generated C++ file: {output_file}")
    return output_file

