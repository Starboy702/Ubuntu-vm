#!/usr/bin/env bash

# Timestamp flags
ts=$(date +%Y-%m-%d)
year=$(date +%Y)
month=$(date +%m)
day=$(date +%d)

# Help function
help() {
  echo "Usage: ca.sh [-l NUM] [-u NUM] [-e EXT]"
  echo "You need to provide a range of file numbers and an extension"
  echo "Sample usage: ./ca.sh -l 10 -u 15 -e csv"
}

# Check log folder 
check_log_folder() {
  echo "Checking log/$year/$month/$day structure"
  folder="log/$year/$month/$day"
  if [ ! -d "$folder" ]; then
    echo "Missing folder. Creating one"
    mkdir -p "$folder"
  fi
}

# Filter/ backup files
filter_files() {
  echo "Filtering files range [$lower-$upper] for extension $ext"
  folder="log/$year/$month/$day"
  mkdir -p "$folder"

  for file in data/data_*.$ext; do
    [[ -f "$file" ]] || continue
    filename=$(basename "$file")
    num=$(echo "$filename" | grep -oP 'data_\K[0-9]+')
    if [[ $num -ge $lower && $num -le $upper ]]; then
      cp "$file" "$folder/"
    fi
  done
}

# Parse options
lower=""
upper=""
ext=""

while getopts ":l:u:e:h" opt; do
  case $opt in
    l)
      lower=$OPTARG
      echo "Option l: Lower bound ($lower)"
      ;;
    u)
      upper=$OPTARG
      echo "Option u: Upper bound ($upper)"
      ;;
    e)
      ext=$OPTARG
      echo "Option e: File extension ($ext)"
      ;;
    h)
      help
      exit 0
      ;;
    \?)
      echo "Invalid Option"
      help
      exit 1
      ;;
    :)
      echo "Missing argument for -$OPTARG"
      help
      exit 1
      ;;
  esac
done


if [[ -z "$lower" || -z "$upper" || -z "$ext" ]]; then
  help
  exit 1
fi

# Run script logic
check_log_folder
filter_files

echo "Done"
exit 0
