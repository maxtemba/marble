# run_hls.tcl
# Tcl script to run Vitis HLS on generated C++ code

# Create HLS project
open_project hls_project -reset

# Set top function
set_top top_function

# Add source files
add_files generated_design.cpp

# Set solution and target device
open_solution "solution1" -reset
set_part {xcvu9p-flga2104-2-i}

# Run C synthesis
csynth_design

# Export RTL
export_design -format ip_catalog

# Close project
close_project

puts "HLS synthesis complete"
