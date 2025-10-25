# generate_cpp.py
# Generates a top-level C++ file calling placeholder functions based on Architecture

def generate_cpp_from_architecture(arch, output_file="generated_design.cpp"):
    """
    Generate C++ code that calls placeholder functions based on the architecture.
    
    Args:
        arch: Architecture object containing blocks
        output_file: Output C++ file path
    """
    with open(output_file, 'w') as f:
        # Write includes
        f.write("// Auto-generated design from Architecture\n")
        f.write("// Architecture: " + str(arch) + "\n")
        f.write("#include <cstddef>\n\n")
        
        # Write placeholder function declarations
        f.write("// Placeholder function declarations\n")
        f.write("void relu(float* data, int size);\n")
        # 'add' declaration removed
        f.write("void conv(float* input, float* output, int channels, int filter_size);\n")
        f.write("void max_pool(float* input, float* output, int size, int kernel_size);\n")
        f.write("void avg_pool(float* input, float* output, int size);\n")
        f.write("void linear(float* input, float* output, int in_features, int out_features);\n\n")

        
        # Write top function with HLS interface
        f.write("void top_function(float* input, float* output, int size) {\n")
        f.write("    #pragma HLS INTERFACE m_axi port=input bundle=gmem0\n")
        f.write("    #pragma HLS INTERFACE m_axi port=output bundle=gmem1\n")
        f.write("    #pragma HLS INTERFACE s_axilite port=size\n")
        f.write("    #pragma HLS INTERFACE s_axilite port=return\n\n")
        
        f.write("    // Architecture implementation\n")
        
        # Generate calls for each block
        for i, block in enumerate(arch.blocks):
            op_type = block.op_type
            params = block.params
            
            if op_type == 'conv':
                # Read params from the block
                filter_size = params.get('kernel_size', 3)
                filters = params.get('out_channels', 64)
                f.write(f"    // Block {i}: {op_type} with {filters} filters, {filter_size}x{filter_size}\n")
                f.write(f"    conv(input, output, {filters}, {filter_size});\n")
            elif op_type == 'relu':
                f.write(f"    // Block {i}: {op_type}\n")
                f.write(f"    relu(output, size);\n")
            # 'add' block removed
            elif op_type == 'max_pool':
                kernel_size = params.get('kernel_size', 2)
                f.write(f"    // Block {i}: {op_type} with {kernel_size}x{kernel_size} kernel\n")
                f.write(f"    max_pool(output, output, size, {kernel_size});\n")
            elif op_type == 'global_avg_pool':
                f.write(f"    // Block {i}: {op_type}\n")
                f.write(f"    avg_pool(output, output, size);\n")
            elif op_type == 'linear':
                in_features = params.get('in_features', 512) # For placeholder, not really used
                out_features = params.get('out_features', 512)
                f.write(f"    // Block {i}: {op_type} with {out_features} out_features\n")
                f.write(f"    linear(output, output, {in_features}, {out_features});\n")
            elif op_type == 'flatten':
                f.write(f"    // Block {i}: {op_type} (no-op in C++ placeholder)\n")
                pass # Flatten is a data reshape, no C++ op needed for placeholder
        
        f.write("}\n")
    
    print(f"Generated C++ file: {output_file}")
    return output_file