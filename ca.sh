#!/bin/bash

echo "Hello from the script!"
date
whoami

# Get the current day of the month 
today=$(date +%d)

# Loop through all the files in the current directory
for file in *; do
    # Will check if it's a regular file
    if [[ -f "$file" ]]; then
        # Gets the last day of the files last modification 
        mod_day=$(date -r "$file" +%d)

        # Compares with today date
        if [[ "$mod_day" == "$today" ]]; then
            echo "$file"
        fi
    fi
done
