// placeholder c++ functions for neural network operations

#include <cstddef>

void relu(float* data, int size) {
    for (int i = 0; i < size; i++) {
        if (data[i] < 0) data[i] = 0;
    }
}

// 'add' function removed

void conv(float* input, float* output, int channels, int filter_size) {
    for (int c = 0; c < channels; c++) {
        for (int i = 0; i < 64; i++) {
            output[c * 64 + i] = input[i] * 0.5f;
        }
    }
}

void max_pool(float* input, float* output, int size, int kernel_size) {
    // Placeholder: just copy data
    for (int i = 0; i < size; i++) {
        output[i] = input[i];
    }
}

void avg_pool(float* input, float* output, int size) {
    // Placeholder: just copy data
    for (int i = 0; i < size; i++) {
        output[i] = input[i];
    }
}

void linear(float* input, float* output, int in_features, int out_features) {
    // Placeholder: just copy data
    for (int i = 0; i < out_features; i++) {
        if(i < in_features) {
            output[i] = input[i] * 0.2f;
        } else {
            output[i] = 0.1f;
        }
    }
}