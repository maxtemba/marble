# build.tcl - Corrected with power report, robust extraction, and specific regex fix
# --- MODIFIED: Assumes vivado is run from the 'build' directory ---

# Project will be created in the current directory (build/)
create_project -force vivado_project .
set_property part xck26-sfvc784-2LVI-i [current_project]

# HLS IP dir is now in the current directory (build/)
set hls_ip_dir "top_function"
set verilog_files {}

# --- Find Verilog files ---
# IMPORTANT: Adjust these paths if your HLS tool version outputs Verilog elsewhere
if {[file exists ${hls_ip_dir}/hls/impl/ip/hdl/verilog]} {
    puts "INFO: Found HLS Verilog in ${hls_ip_dir}/hls/impl/ip/hdl/verilog"
    set verilog_files [glob ${hls_ip_dir}/hls/impl/ip/hdl/verilog/*.v]
} elseif {[file exists ${hls_ip_dir}/syn/verilog]} {
    puts "INFO: Found HLS Verilog in ${hls_ip_dir}/syn/verilog"
    set verilog_files [glob ${hls_ip_dir}/syn/verilog/*.v]
} elseif {[file exists ${hls_ip_dir}/impl/verilog]} {
    puts "INFO: Found HLS Verilog in ${hls_ip_dir}/impl/verilog"
    set verilog_files [glob ${hls_ip_dir}/impl/verilog/*.v]
}

# Error out if no Verilog files were found after checking common locations
if {[llength $verilog_files] == 0} {
    puts "ERROR: No Verilog files found in expected HLS output locations (${hls_ip_dir}/hls/impl/ip/hdl/verilog, ${hls_ip_dir}/syn/verilog, or ${hls_ip_dir}/impl/verilog)."
    exit 1
}
puts "INFO: Found [llength $verilog_files] Verilog files"
add_files $verilog_files

# --- Add subcore IPs if they exist ---
# IMPORTANT: Adjust path if your HLS tool outputs subcore IPs elsewhere
if {[file exists ${hls_ip_dir}/hls/impl/ip/hdl/ip]} {
    puts "INFO: Adding subcore IPs from ${hls_ip_dir}/hls/impl/ip/hdl/ip"
    set ip_repo_paths [list ${hls_ip_dir}/hls/impl/ip/hdl/ip]
    set_property ip_repo_paths $ip_repo_paths [current_project]
    update_ip_catalog

    set xci_files [glob -nocomplain ${hls_ip_dir}/hls/impl/ip/hdl/ip/*/*.xci]
    if {[llength $xci_files] > 0} {
        puts "INFO: Adding [llength $xci_files] XCI files."
        add_files $xci_files
    } else {
        puts "INFO: No XCI files found in subcore IP directory."
    }
} else {
     puts "INFO: No subcore IP directory found at ${hls_ip_dir}/hls/impl/ip/hdl/ip."
}

set_property top top_function [current_fileset]
update_compile_order -fileset sources_1

# --- CREATE TIMING CONSTRAINTS FOR OOC MODE ---
# Paths are relative to the current dir (build/)
set constraints_file "./ooc_constraints.xdc"
# Use 'catch' for file operations to prevent script halt on permission issues etc.
if {[catch {open $constraints_file w} fp]} {
     puts "ERROR: Could not open constraints file $constraints_file for writing: $fp"
     exit 1
}
puts $fp "create_clock -period 10.000 -name ap_clk \[get_ports -quiet ap_clk\]"
if {[catch {close $fp}]} {
     puts "ERROR: Could not close constraints file $constraints_file"
}
add_files -fileset constrs_1 $constraints_file
set_property target_constrs_file $constraints_file [current_fileset -constrset]
set_property used_in_synthesis true [get_files $constraints_file]
set_property used_in_implementation true [get_files $constraints_file]
puts "INFO: Added timing constraints: $constraints_file"

# --- OOC mode ---
set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context} -objects [get_runs synth_1]

# --- Run Synthesis ---
puts "Starting synthesis..."
reset_runs synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1

# Check Synthesis Status more thoroughly
set synth_status [get_property STATUS [get_runs synth_1]]
set synth_progress [get_property PROGRESS [get_runs synth_1]]
if {$synth_status != "synth_design Complete!" || $synth_progress != "100%"} {
    puts "ERROR: Synthesis failed or did not complete."
    puts "ERROR: Status: $synth_status, Progress: $synth_progress"
    if {[get_property NEEDS_REFRESH [get_runs synth_1]] == 0} {
        open_run synth_1
        report_utilization -file ./synth_util_fail.rpt
        close_design
    }
    exit 1
}
puts "INFO: Synthesis completed successfully."

# --- Run Implementation ---
puts "Starting implementation..."
reset_runs impl_1
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1

# Check Implementation Status more thoroughly
set impl_status [get_property STATUS [get_runs impl_1]]
set impl_progress [get_property PROGRESS [get_runs impl_1]]
if {$impl_status != "route_design Complete!" || $impl_progress != "100%"} {
    puts "ERROR: Implementation failed or did not complete."
    puts "ERROR: Status: $impl_status, Progress: $impl_progress"
    if {[get_property NEEDS_REFRESH [get_runs impl_1]] == 0} {
        open_run impl_1
        report_timing_summary -file ./timing_summary_fail.rpt
        report_utilization -file ./impl_util_fail.rpt
        close_design
    }
    exit 1
}
puts "INFO: Implementation completed successfully."

puts "Opening implemented design..."
open_run impl_1

# --- Generate Reports ---
# --- FIX: Removed ./build/ prefix. Paths are now relative to the current dir (build/) ---
puts "Generating timing report..."
report_timing_summary -file ./timing_report.txt -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 10

puts "Generating power report..."
report_power -file ./power_report.txt

# --- Extract Results ---
puts "Extracting results..."

# Extract WNS
set wns "N/A"
if {![catch {get_timing_paths -max_paths 1 -nworst 1 -setup} timing_paths]} {
    if {[llength $timing_paths] > 0} {
        set wns [get_property SLACK [lindex $timing_paths 0]]
    } else {
        puts "WARN: No setup timing paths found for WNS extraction (design might be unconstrained or meet timing perfectly)."
    }
} else {
     puts "WARN: Could not get setup timing paths."
}


# Extract WHS
set whs "N/A"
if {![catch {get_timing_paths -max_paths 1 -nworst 1 -hold} hold_paths]} {
    if {[llength $hold_paths] > 0} {
        set whs [get_property SLACK [lindex $hold_paths 0]]
    } else {
        puts "WARN: No hold timing paths found for WHS extraction."
    }
} else {
     puts "WARN: Could not get hold timing paths."
}

# Extract Total Power (Robust Method)
set power "N/A"
# --- FIX: Removed ./build/ prefix. ---
set power_report_path "./power_report.txt"
if {[file exists $power_report_path]} {
    if {[catch {open $power_report_path r} fp_power]} {
        puts "ERROR: Could not open power report file '$power_report_path': $fp_power"
    } else {
        set power_content [read $fp_power]
        close $fp_power
        if {[regexp -nocase {\|\s*Total On-Chip Power \(W\)\s*\|\s*([\d\.]+)\s*\|} $power_content match power_value]} {
            set power $power_value
        } else {
            puts "WARN: Could not find 'Total On-Chip Power (W)' line with expected format in $power_report_path"
        }
    }
} else {
    puts "WARN: Power report file not found at $power_report_path"
}

# --- Write results to a single file ---
# --- FIX: Removed ./build/ prefix. ---
set results_file_path "./results.txt"
if {[catch {open $results_file_path w} fp_results]} {
     puts "ERROR: Could not open results file '$results_file_path' for writing: $fp_results"
} else {
    puts $fp_results "WNS: $wns"
    puts $fp_results "WHS: $whs"
    puts $fp_results "Power: $power"
    if {[catch {close $fp_results}]} {
        puts "ERROR: Could not close results file '$results_file_path'"
    } else {
        puts "INFO: Results written to $results_file_path"
    }
}

puts "Build complete. WNS=$wns ns, WHS=$whs ns, Power=$power W"

close_project
exit ; # Explicitly exit Tcl script

