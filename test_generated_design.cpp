// Auto-generated realistic HLS design
// Architecture: Block(conv, {'in_channels': 3, 'out_channels': 3, 'kernel_size': 5, 'padding': 2, 'stride': 2}) -> Block(max_pool, {'kernel_size': 2, 'stride': 2}) -> Block(conv, {'in_channels': 3, 'out_channels': 3, 'kernel_size': 3, 'padding': 'same', 'stride': 1}) -> Block(global_avg_pool, {}) -> Block(flatten, {'in_features': 3}) -> Block(linear, {'in_features': 3, 'out_features': 128})
#include <cstddef>

#define MAX_FEAT_SIZE 131072
#define MAX_WEIGHT_SIZE 409600
#define MAX_BIAS_SIZE 1024

// --- REAL HLS Function Declarations ---
void relu(float* data, int size);
void max_pool(float* input, float* output, int in_channels, int in_h, int in_w, int stride);
void avg_pool(float* input, float* output, int in_channels, int in_h, int in_w);
void linear(float* input, float* output, const float* weights, const float* bias, int in_features, int out_features);
void conv(float* input, float* output, const float* weights, const float* bias, int in_channels, int out_channels, int kernel_size, int in_h, int in_w, int out_h, int out_w, int stride);

// --- Dummy Weights/Biases for Synthesis ---
const float dummy_weights[MAX_WEIGHT_SIZE] = { 0.1f };
const float dummy_bias[MAX_BIAS_SIZE] = { 0.1f };

void top_function(float* input_gmem, float* output_gmem) {
    #pragma HLS INTERFACE m_axi port=input_gmem bundle=gmem0 depth=MAX_FEAT_SIZE
    #pragma HLS INTERFACE m_axi port=output_gmem bundle=gmem1 depth=MAX_FEAT_SIZE
    #pragma HLS INTERFACE s_axilite port=return

    // Buffers to hold feature maps between layers
    static float buffer_a[MAX_FEAT_SIZE];
    static float buffer_b[MAX_FEAT_SIZE];
    #pragma HLS BIND_STORAGE variable=buffer_a type=RAM_2P
    #pragma HLS BIND_STORAGE variable=buffer_b type=RAM_2P

    // --- Pointers for Ping-Pong Buffering ---
    float* in_buf = buffer_a;
    float* out_buf = buffer_b;
    float* temp; // <-- DECLARE TEMP POINTER ONCE

    // Manually load from gmem to local BRAM (simplified)
    int load_size = 3072;
    if (load_size > MAX_FEAT_SIZE) load_size = MAX_FEAT_SIZE;
    for(int i=0; i< load_size; ++i) buffer_a[i] = input_gmem[i];

    // --- Block 0: conv ---
    conv(in_buf, out_buf, dummy_weights, dummy_bias, 3, 3, 5, 32, 32, 16, 16, 2);
    // --- Swap pointers for next layer ---
    temp = in_buf; in_buf = out_buf; out_buf = temp;

    // --- Block 1: max_pool ---
    max_pool(in_buf, out_buf, 3, 16, 16, 2);
    // --- Swap pointers for next layer ---
    temp = in_buf; in_buf = out_buf; out_buf = temp;

    // --- Block 2: conv ---
    conv(in_buf, out_buf, dummy_weights, dummy_bias, 3, 3, 3, 8, 8, 8, 8, 1);
    // --- Swap pointers for next layer ---
    temp = in_buf; in_buf = out_buf; out_buf = temp;

    // --- Block 3: global_avg_pool ---
    avg_pool(in_buf, out_buf, 3, 8, 8);
    // --- Swap pointers for next layer ---
    temp = in_buf; in_buf = out_buf; out_buf = temp;

    // --- Block 4: flatten ---
    // Flatten: No C++ op, just change buffer interpretation
    if (in_buf != out_buf) for(int i=0; i<3; ++i) { out_buf[i] = in_buf[i]; }
    // --- Swap pointers for next layer ---
    temp = in_buf; in_buf = out_buf; out_buf = temp;

    // --- Block 5: linear ---
    linear(in_buf, out_buf, dummy_weights, dummy_bias, 3, 128);
    // --- Swap pointers for next layer ---
    temp = in_buf; in_buf = out_buf; out_buf = temp;

    // Write final result from in_buf back to gmem
    int out_size = 128;
    if (out_size <= 0) out_size = MAX_FEAT_SIZE;
    if (out_size > MAX_FEAT_SIZE) out_size = MAX_FEAT_SIZE;
    for(int i=0; i< out_size; ++i) output_gmem[i] = in_buf[i];
}
