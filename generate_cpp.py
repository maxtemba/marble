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
        f.write("void add(float* a, float* b, float* result, int size);\n")
        f.write("void conv(float* input, float* output, int channels, int filter_size);\n\n")
        
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
            
            if 'conv' in op_type:
                # Extract filter size from op_type (e.g., '3x3_conv' -> 3)
                filter_size = int(op_type.split('x')[0]) if 'x' in op_type else 3
                filters = params.get('filter', 64)
                f.write(f"    // Block {i}: {op_type} with {filters} filters\n")
                f.write(f"    conv(input, output, {filters}, {filter_size});\n")
            elif op_type == 'relu':
                f.write(f"    // Block {i}: {op_type}\n")
                f.write(f"    relu(output, size);\n")
            elif op_type == 'add':
                f.write(f"    // Block {i}: {op_type}\n")
                f.write(f"    add(input, output, output, size);\n")
        
        f.write("}\n")
    
    print(f"Generated C++ file: {output_file}")
    return output_file
