#!/bin/bash

# Output file for the snapshot
output_file="filesystem_snapshot_$(date +%Y%m%d_%H%M%S).txt"

# Function to process files
process_file() {
    local file="$1"
    
    # Skip files ending with .sum
    if [[ "$file" == *.sum ]]; then
        return
    fi
    
    # Add file separator and path to output
    echo -e "\n=== File: $file ===" >> "$output_file"
    
    # Check if file is binary
    if [[ -f "$file" ]] && ! [[ -x "$file" ]] && file "$file" | grep -q "text"; then
        # For text files, add content
        echo -e "\n--- Content ---" >> "$output_file"
        cat "$file" >> "$output_file"
    else
        # For binary files, just note that it's binary
        echo -e "\n[Binary file]" >> "$output_file"
    fi
}

# Main function to traverse directory
traverse_directory() {
    local dir="$1"
    
    # Find all files and directories, excluding specified patterns
    find "$dir" \
        -not \( -path "*/target/*" -o -path "*/target" \) \
        -not \( -path "*/.git/*" -o -path "*/.git" \) \
        -not \( -path "*/.cargo/*" -o -path "*/.cargo" \) \
        -not \( -path "*/.rustup/*" -o -path "*/.rustup" \) \
        -type f -o -type d | while read -r item; do
        
        if [[ -f "$item" ]]; then
            process_file "$item"
        elif [[ -d "$item" ]]; then
            echo -e "\n=== Directory: $item ===" >> "$output_file"
        fi
    done
}

# Initialize output file with header
echo "File System Snapshot - Generated on $(date)" > "$output_file"
echo "Current working directory: $(pwd)" >> "$output_file"
echo -e "\n----------------------------------------" >> "$output_file"

# Start traversal from current directory
traverse_directory "."

echo "Snapshot has been generated in: $output_file"