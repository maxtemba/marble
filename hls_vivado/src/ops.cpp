// placeholder c++ functions for neural network operations

#include <cstddef>

void relu(float* data, int size) {
    for (int i = 0; i < size; i++) {
        if (data[i] < 0) data[i] = 0;
    }
}

void add(float* a, float* b, float* result, int size) {
    for (int i = 0; i < size; i++) {
        result[i] = a[i] + b[i];
    }
}

void conv(float* input, float* output, int channels, int filter_size) {
    for (int c = 0; c < channels; c++) {
        for (int i = 0; i < 64; i++) {
            output[c * 64 + i] = input[i] * 0.5f;
        }
    }
}
