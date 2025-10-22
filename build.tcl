# amd kria kv260
set part_name "xck26-sfvc784-2LVI-i"

# TODO: just for testing to have some code running
set top_module "hello"
 
set build_dir "./build"
file mkdir $build_dir

# Vivado-project set up
create_project $top_module $build_dir -part $part_name -force
set_property top $top_module [current_fileset]

add_files ./hello.v

add_files -fileset constrs_1 ./constraints.xdc


# start synthesis
launch_runs synth_1 -jobs 8
wait_on_run synth_1
puts "synthesis FINISHED."

# start implementation
launch_runs impl_1 -jobs 8
wait_on_run impl_1
puts "implementation FINISHED."

# run implementation
open_run impl_1

# report creation
report_timing_summary -file $build_dir/timing_report.txt
puts "report SAVED"

close_project
exit