set -e # stops script on any error

echo "-----------------------------------"
echo "START..."
echo "-----------------------------------"

# 1. loads AMD Vitis/Vivado environment
source /tools/Xilinx/2025.1/Vitis/settings64.sh

# 2. generate a clean build directory
rm -rf ./build
rm -f vivado*.log
rm -f vivado*.jou

# 3. call Vivado without GUI in batch mode, handing it over Vivado build script
vivado -mode batch -source build.tcl

echo "-----------------------------------"
echo "FINISHED."
echo "report ./build/timing_report.txt"
echo "-----------------------------------"