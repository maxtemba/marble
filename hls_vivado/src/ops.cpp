// --- Simple Placeholder C++ functions for faster testing ---
// NOTE: HLS will optimize this, and the results will not be
// realistic for power/timing. This is only for flow testing.

#include <cstddef>

// Define a max buffer size just for safety
#define MAX_FEAT_SIZE (32 * 32 * 128)

// --- RELU ---
void relu(float* data, int size) {
    if (size > MAX_FEAT_SIZE) size = MAX_FEAT_SIZE;
    for (int i = 0; i < size; i++) {
        if (data[i] < 0.0f) {
            data[i] = 0.0f;
        }
    }
}

// --- MAX POOL ---
void max_pool(float* input, float* output, 
              int in_channels, int in_h, int in_w, int stride) 
{
    // Placeholder: just copy a portion of the data
    int size = (in_h * in_w * in_channels) / stride;
    if (size > MAX_FEAT_SIZE) size = MAX_FEAT_SIZE;
    if (size <= 0) size = 1;
    
    for (int i = 0; i < size; i++) {
        if (i < MAX_FEAT_SIZE) {
            output[i] = input[i] * 0.9f; // Multiply to prevent optimizing away
        }
    }
}

// --- GLOBAL AVG POOL ---
void avg_pool(float* input, float* output, 
              int in_channels, int in_h, int in_w) 
{
    // Placeholder: just copy the channel data
    if (in_channels > MAX_FEAT_SIZE) in_channels = MAX_FEAT_SIZE;
    if (in_channels <= 0) in_channels = 1;

    for (int i = 0; i < in_channels; i++) {
        if (i < MAX_FEAT_SIZE) {
            output[i] = input[i] * 0.5f; // Multiply to prevent optimizing away
        }
    }
}


// --- LINEAR ---
void linear(float* input, 
            float* output, 
            const float* weights, // weights are ignored
            const float* bias,    // bias is ignored
            int in_features,
            int out_features) 
{
    // Placeholder: just copy/manipulate data
    if (out_features > MAX_FEAT_SIZE) out_features = MAX_FEAT_SIZE;
    if (out_features <= 0) out_features = 1;
    
    for (int i = 0; i < out_features; i++) {
        if (i < MAX_FEAT_SIZE) {
            // Do a simple operation to represent "work"
            output[i] = (i < in_features ? input[i] : 0.0f) * 0.2f; 
        }
    }
}


// --- CONV 2D ---
void conv(float* input, 
          float* output, 
          const float* weights, // weights are ignored
          const float* bias,    // bias is ignored
          int in_channels,
          int out_channels,
          int kernel_size,
          int in_h, int in_w, 
          int out_h, int out_w, 
          int stride
          ) 
{
    // Placeholder: just copy/manipulate data
    int out_size = out_h * out_w * out_channels;
    if (out_size > MAX_FEAT_SIZE) out_size = MAX_FEAT_SIZE;
    if (out_size <= 0) out_size = 1;
    
    for (int i = 0; i < out_size; i++) {
        if (i < MAX_FEAT_SIZE) {
             // Do a simple operation to represent "work"
            output[i] = input[i % MAX_FEAT_SIZE] * 0.1f;
        }
    }
}

