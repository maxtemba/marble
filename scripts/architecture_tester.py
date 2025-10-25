import sys
import os
import torch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from hw_nas.search_space import get_random_architecture, build_pytorch_model
from hw_nas.predictor import featurize
from hw_nas.cpp_generator import generate_cpp_from_architecture


# config for minimal test
INPUT_CHANNELS = 3
INPUT_SIZE = 32
BATCH_SIZE = 1 
CPP_OUTPUT_FILE = "./scripts/test_generated_design.cpp"

def main():
    print("----------------------------")
    print("--- STARTING MINIMAL TEST ---")
    print("----------------------------")

    # 1. generate a random, valid architecture
    print("1. Generating random architecture...")
    try:
        arch = get_random_architecture(
            input_channels=INPUT_CHANNELS, 
            input_size=INPUT_SIZE
        )
        print(f"   ... SUCCESS. Architecture:\n{arch}\n")
    except Exception as e:
        print(f"   ... FAILED: {e}")
        return # Stop test if this fails

    # 2. test PyTorch Model Generation & Forward Pass
    print("2. Testing PyTorch model generation...")
    try:
        model = build_pytorch_model(arch)
        print("   ... Model built successfully. Structure:")
        print(model)
        
        # test forward pass
        print("\n   ... Testing PyTorch forward pass...")
        dummy_input = torch.randn(BATCH_SIZE, INPUT_CHANNELS, INPUT_SIZE, INPUT_SIZE)
        output = model(dummy_input)
        print(f"   ... PyTorch forward pass SUCCESS. Output shape: {output.shape}\n")
        
    except Exception as e:
        print(f"   ... PyTorch test FAILED: {e}\n")

    # 3. test Featurizer
    print("3. Testing Featurizer...")
    try:
        features = featurize(arch)
        print(f"   ... Featurizer SUCCESS. Features:\n{features}\n")
    except Exception as e:
        print(f"   ... Featurizer FAILED: {e}\n")

    # 4. test C++ Code Generator
    print("4. Testing C++ Generator...")
    try:
        generate_cpp_from_architecture(arch, CPP_OUTPUT_FILE)
        print(f"   ... C++ Generator SUCCESS. File created at: {CPP_OUTPUT_FILE}\n")
    except Exception as e:
        print(f"   ... C++ Generator FAILED: {e}\n")

    print("--------------------------")
    print("--- MINIMAL TEST DONE ---")
    print("--------------------------")

if __name__ == "__main__":
    main()