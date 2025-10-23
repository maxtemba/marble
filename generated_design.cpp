// Auto-generated design from Architecture
// Architecture: Block(5x5_conv, {'filter': 32}) -> Block(relu, {'filter': 32}) -> Block(3x3_conv, {'filter': 32}) -> Block(add, {'filter': 128})
#include <cstddef>

// Placeholder function declarations
void relu(float* data, int size);
void add(float* a, float* b, float* result, int size);
void conv(float* input, float* output, int channels, int filter_size);

void top_function(float* input, float* output, int size) {
    #pragma HLS INTERFACE m_axi port=input bundle=gmem0
    #pragma HLS INTERFACE m_axi port=output bundle=gmem1
    #pragma HLS INTERFACE s_axilite port=size
    #pragma HLS INTERFACE s_axilite port=return

    // Architecture implementation
    // Block 0: 5x5_conv with 32 filters
    conv(input, output, 32, 5);
    // Block 1: relu
    relu(output, size);
    // Block 2: 3x3_conv with 32 filters
    conv(input, output, 32, 3);
    // Block 3: add
    add(input, output, output, size);
}
