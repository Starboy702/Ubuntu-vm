#!/bin/bash

# Initialize variables
URL=""
FILE=""
GUTENBERG=false
WORD=""
HELP=false
VOWEL=false
CONSONANT=false
PUNCTUATION=false
DIGIT=false
TOP_TEN=false
LEAST_TEN=false

# Display help message
function display_help {
  echo "Usage: ./ca.sh [options]"
  echo "Options:"
  echo "  -h         Show this help message"
  echo "  -f FILE    Read from FILE (cannot be combined with -u)"
  echo "  -u URL     Download and read from the URL (cannot be combined with -f)"
  echo "  -g         Ignore lines before and after the project in Project Gutenberg files"
  echo "  -w         Output the word count"
  echo "  -v         Output the vowel count"
  echo "  -c         Output the consonant count"
  echo "  -p         Output the punctuation count"
  echo "  -d         Output the digit count"
  echo "  -t         Output the top 10 most frequent words"
  echo "  -T         Output the top 10 least frequent words"
  echo "  -W WORD    Output the count of the specified word"
}

# Check for errors and exit if any error occurs
function check_error {
  if [[ $? -ne 0 ]]; then
    echo "Error occurred. Exiting..."
    exit 1
  fi
}

# Process Gutenberg file if -g option is selected
function process_gutenberg {
  if $GUTENBERG; then
    sed -n '/\*\*\* START OF THE PROJECT \*\*\*/,$p' | sed '/\*\*\* END OF THE PROJECT \*\*\*/,$d'
    check_error
  fi
}

# Count lines in the text
function count_lines {
  echo "Line Count: $(wc -l < "$INPUT_FILE")"
}

# Count words in the text
function count_words {
  echo "Word Count: $(wc -w < "$INPUT_FILE")"
}

# Count vowels
function count_vowels {
  echo "Vowel Count: $(grep -o -i '[aeiou]' "$INPUT_FILE" | wc -l)"
}

# Count consonants
function count_consonants {
  echo "Consanant Count: $(grep -o -i '[bcdfghjklmnpqrstvwxyz]' "$INPUT_FILE" | wc -l)"
}

# Count punctuation marks
function count_punctuation {
  echo "Punctation Count: $(grep -o '[[:punct:]]' "$INPUT_FILE" | wc -l)"
}

# Count digits
function count_digits {
  echo "Digit Count: $(grep -o '[0-9]' "$INPUT_FILE" | wc -l)"
}

# Top 10 most frequent words
function top_ten {
  echo "Most Frequent Words"
  tr -c '[:alnum:]' '[\n*]' < "$INPUT_FILE" | sort | uniq -c | sort -nr | head -n 10
}

# Top 10 least frequent words
function least_ten {
  echo "Least Frequent Words"
  tr -c '[:alnum:]' '[\n*]' < "$INPUT_FILE" | sort | uniq -c | sort -n | head -n 10
}

# Count specified word
function count_word {
  WORD_COUNT=$(grep -wo -i "$WORD" "$INPUT_FILE" | wc -l)
  echo "\"$WORD\" count: $WORD_COUNT"
}

# Check command-line options
while getopts "hf:u:gvwcpdtTW:" opt; do
  case $opt in
    h) HELP=true ;;
    f) FILE="$OPTARG" ;;
    u) URL="$OPTARG" ;;
    g) GUTENBERG=true ;;
    w) WORD=true ;;
    v) VOWEL=true ;;
    c) CONSONANT=true ;;
    p) PUNCTUATION=true ;;
    d) DIGIT=true ;;
    t) TOP_TEN=true ;;
    T) LEAST_TEN=true ;;
    W) WORD="$OPTARG" ;;
    *) HELP=true ;;
  esac
done

# Display help message if -h is passed
if $HELP; then
  display_help
  exit 0
fi

# If file is passed, read from file
if [ -n "$FILE" ]; then
  INPUT_FILE="$FILE"
elif [ -n "$URL" ]; then
  INPUT_FILE=$(mktemp)
  curl -s "$URL" > "$INPUT_FILE"
  check_error
else
  INPUT_FILE="/dev/stdin"
fi

# Process Gutenberg file if -g option is set
process_gutenberg

# Perform required actions
if $WORD; then
  count_word
fi
if $VOWEL; then
  count_vowels
fi
if $CONSONANT; then
  count_consonants
fi
if $PUNCTUATION; then
  count_punctuation
fi
if $DIGIT; then
  count_digits
fi
if $TOP_TEN; then
  top_ten
fi
if $LEAST_TEN; then
  least_ten
fi
if $WORD; then
  count_words
fi

# Clean up if a temporary file was created
if [ -f "$INPUT_FILE" ] && [[ "$INPUT_FILE" != "/dev/stdin" ]]; then
  rm -f "$INPUT_FILE"
fi
