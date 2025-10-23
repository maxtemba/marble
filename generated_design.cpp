// Auto-generated design from Architecture
// Architecture: Block(relu, {'filter': 64}) -> Block(5x5_conv, {'filter': 32}) -> Block(5x5_conv, {'filter': 128}) -> Block(5x5_conv, {'filter': 128})
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
    // Block 0: relu
    relu(output, size);
    // Block 1: 5x5_conv with 32 filters
    conv(input, output, 32, 5);
    // Block 2: 5x5_conv with 128 filters
    conv(input, output, 128, 5);
    // Block 3: 5x5_conv with 128 filters
    conv(input, output, 128, 5);
}
