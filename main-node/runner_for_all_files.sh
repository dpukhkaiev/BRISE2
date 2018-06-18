#!/usr/bin/env bash

# Getting all files that will be measured

files=(./csv/*.csv)

mkdir -p ./Results

for file in "${files[@]}"
 do
    # Read current file name from config file for further replacement
    cur_source_file=$(cat task.json | jq '.params .WSFile')
    # Get new file name that will be run
    new_source_file=$(basename $file)
    # Generate log file name to write script output.
    log_filename=./Results/Run_$new_source_file\_$(date +"%d.%m.%y_%H:%M").log
    # Replace current file name with new one in config file
    sed -i "s/$cur_source_file/\"$new_source_file\"/" ./task.json

    # Run experiment 3 times for each file.
    for i in {1..3}
     do
      echo $(date +"%d.%m.%y_%H:%M"): Running ${i} iteration for ${new_source_file}
      echo RUNNING ${i} ITERATION. Started at: $(date +"%T") &>> ${log_filename}
      python3 main.py >> ${log_filename}
    done

done
