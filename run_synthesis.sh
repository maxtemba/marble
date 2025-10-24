#!/bin/bash
set -e # stops script on any error

echo "-----------------------------------"
echo "START..."
echo "-----------------------------------"

# 1. loads AMD Vitis/Vivado environment
source /tools/Xilinx/2025.1/Vitis/settings64.sh

# 2. check if generated c++ files exist
if [ ! -f "generated_design.cpp" ]; then
    echo "ERROR: generated_design.cpp not found!"
    exit 1
fi

if [ ! -f "ops.cpp" ]; then
    echo "ERROR: ops.cpp not found!"
    exit 1
fi

echo "Found generated C++ files."

# 3. run Vitis HLS using new v++ command
echo "Running Vitis HLS (v++ --mode hls)..."
rm -rf component.xml .Xil hls_config.cfg.xml *.log *.jou

v++ -c --mode hls --config hls_config.cfg

# 4. check if HLS succeeded and find the generated IP
if [ -d "top_function" ]; then
    echo "HLS completed successfully."
    HLS_IP_DIR="top_function"
else
    echo "ERROR: HLS did not generate IP!"
    echo "Checking for alternative output directories..."
    ls -la
    exit 1
fi

echo "HLS IP directory: $HLS_IP_DIR"

# 5. create build directory
mkdir -p ./build
rm -f vivado*.log
rm -f vivado*.jou

# 6. call Vivado without GUI in batch mode
echo "Running Vivado synthesis..."
vivado -mode batch -source build.tcl

echo "-----------------------------------"
echo "FINISHED."
echo "report ./build/timing_report.txt"
echo "-----------------------------------"
