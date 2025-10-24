#!/bin/bash
set -e # stops script on any error

echo "-----------------------------------"
echo "START..."
echo "-----------------------------------"

# Get the directory where this script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Navigate to the project root (one level up)
PROJECT_ROOT="$SCRIPT_DIR/.."

# 1. loads AMD Vitis/Vivado environment
source /tools/Xilinx/2025.1/Vitis/settings64.sh

# --- MODIFIED: Paths are now relative to PROJECT_ROOT ---
HLS_CONFIG_FILE="$PROJECT_ROOT/hls_vivado/hls_config.cfg"
BUILD_TCL_FILE="$PROJECT_ROOT/hls_vivado/build.tcl"
BUILD_DIR="$PROJECT_ROOT/build"
CPP_SRC_DIR="$PROJECT_ROOT/hls_vivado/src"

# 2. check if generated c++ files exist
if [ ! -f "$CPP_SRC_DIR/generated_design.cpp" ]; then
    echo "ERROR: $CPP_SRC_DIR/generated_design.cpp not found!"
    exit 1
fi

if [ ! -f "$CPP_SRC_DIR/ops.cpp" ]; then
    echo "ERROR: $CPP_SRC_DIR/ops.cpp not found!"
    exit 1
fi

echo "Found generated C++ files."

# 3. Create build directory and CD into it
echo "Creating/clearing build directory: $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR" # <-- KEY CHANGE: We are now inside the build directory

# 4. run Vitis HLS using new v++ command
echo "Running Vitis HLS (v++ --mode hls)..."
# All output files (top_function, .Xil, logs) will be created HERE
v++ -c --mode hls --config "$HLS_CONFIG_FILE"

# 5. check if HLS succeeded and find the generated IP
if [ -d "top_function" ]; then
    echo "HLS completed successfully."
else
    echo "ERROR: HLS did not generate IP directory 'top_function'!"
    echo "Checking for alternative output directories..."
    ls -la
    exit 1
fi

echo "HLS IP directory: top_function" # It's now in our local dir

# 6. call Vivado without GUI in batch mode
echo "Running Vivado synthesis..."
# Vivado will also run HERE, creating vivado.log, vivado.jou, etc.
vivado -mode batch -source "$BUILD_TCL_FILE"

echo "-----------------------------------"
echo "FINISHED."
echo "report ./results.txt" # Report is now in build/results.txt
echo "-----------------------------------"

