# build.tcl - Corrected with OOC timing constraints

create_project -force vivado_project ./build
set_property part xck26-sfvc784-2LVI-i [current_project]

set hls_ip_dir "top_function"
set verilog_files {}

# Find Verilog files (your existing logic)
if {[file exists ${hls_ip_dir}/hls/impl/ip/hdl/verilog]} {
    puts "INFO: Found HLS Verilog in ${hls_ip_dir}/hls/impl/ip/hdl/verilog"
    set verilog_files [glob ${hls_ip_dir}/hls/impl/ip/hdl/verilog/*.v]
}
if {[llength $verilog_files] == 0 && [file exists ${hls_ip_dir}/syn/verilog]} {
    puts "INFO: Found HLS Verilog in ${hls_ip_dir}/syn/verilog"
    set verilog_files [glob ${hls_ip_dir}/syn/verilog/*.v]
}
if {[llength $verilog_files] == 0 && [file exists ${hls_ip_dir}/impl/verilog]} {
    puts "INFO: Found HLS Verilog in ${hls_ip_dir}/impl/verilog"
    set verilog_files [glob ${hls_ip_dir}/impl/verilog/*.v]
}

if {[llength $verilog_files] == 0} {
    puts "ERROR: No Verilog files found"
    exit 1
}

puts "INFO: Found [llength $verilog_files] Verilog files"
add_files $verilog_files

# Add subcore IPs if they exist
if {[file exists ${hls_ip_dir}/hls/impl/ip/hdl/ip]} {
    puts "INFO: Adding subcore IPs"
    set ip_repo_paths [list ${hls_ip_dir}/hls/impl/ip/hdl/ip]
    set_property ip_repo_paths $ip_repo_paths [current_project]
    update_ip_catalog
    
    set xci_files [glob -nocomplain ${hls_ip_dir}/hls/impl/ip/hdl/ip/*/*.xci]
    if {[llength $xci_files] > 0} {
        add_files $xci_files
    }
}

set_property top top_function [current_fileset]
update_compile_order -fileset sources_1

# CREATE TIMING CONSTRAINTS FOR OOC MODE
set constraints_file "./build/ooc_constraints.xdc"
file mkdir "./build"
set fp [open $constraints_file w]
puts $fp "create_clock -period 10.000 -name ap_clk \[get_ports -quiet ap_clk\]"
puts $fp "set_input_delay -clock ap_clk 0 \[all_inputs\]"
puts $fp "set_output_delay -clock ap_clk 0 \[all_outputs\]"
close $fp

add_files -fileset constrs_1 $constraints_file
set_property used_in_synthesis true [get_files $constraints_file]
puts "INFO: Added timing constraints: $constraints_file"

# OOC mode
set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context} -objects [get_runs synth_1]

puts "Starting synthesis..."
launch_runs synth_1 -jobs 4
wait_on_run synth_1

set synth_status [get_property STATUS [get_runs synth_1]]
if {$synth_status != "synth_design Complete!"} {
    puts "ERROR: Synthesis failed: $synth_status"
    exit 1
}

puts "Starting implementation..."
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1

puts "Opening implemented design..."
open_run impl_1

report_timing_summary -file ./build/timing_report.txt -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 10

# Extract WNS/WHS
puts "Extracting timing..."
set timing_paths [get_timing_paths -max_paths 1 -nworst 1 -setup]
if {[llength $timing_paths] > 0} {
    set wns [get_property SLACK [lindex $timing_paths 0]]
} else {
    set wns "N/A"
}

set hold_paths [get_timing_paths -max_paths 1 -nworst 1 -hold]
if {[llength $hold_paths] > 0} {
    set whs [get_property SLACK [lindex $hold_paths 0]]
} else {
    set whs "N/A"
}

set wns_file [open "./build/wns.txt" w]
puts $wns_file "WNS: $wns"
puts $wns_file "WHS: $whs"
close $wns_file

puts "Build complete. WNS=$wns ns, WHS=$whs ns"

close_project
