#!/bin/bash

# Git Branch Cleanup Script
# This script removes all local and remote branches except master and main
# Usage: ./git-cleanup.sh

set -e  # Exit on any error

# Text colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        print_message "$RED" "Error: Not a git repository"
        exit 1
    fi
}

# Function to check if working directory is clean
check_working_directory() {
    if ! git diff --quiet HEAD; then
        print_message "$RED" "Error: Working directory is not clean. Please commit or stash your changes."
        exit 1
    fi
}

# Function to fetch latest changes
fetch_latest() {
    print_message "$YELLOW" "Fetching latest changes from remote..."
    git fetch --all --prune
}

# Main cleanup function
cleanup_branches() {
    local current_branch=$(git branch --show-current)
    
    # Switch to main or master branch
    if git show-ref --verify --quiet refs/heads/main; then
        git checkout main
    elif git show-ref --verify --quiet refs/heads/master; then
        git checkout master
    else
        print_message "$RED" "Error: Neither main nor master branch found"
        exit 1
    fi

    # Delete local branches except main and master
    print_message "$YELLOW" "Deleting local branches..."
    git branch | grep -v "main\|master\|\*" | xargs -r git branch -D

    # Delete remote branches except main and master
    print_message "$YELLOW" "Deleting remote branches..."
    git branch -r | grep -v "main\|master" | sed 's/origin\///' | xargs -r -I {} git push origin --delete {}

    # Clean up references
    git gc --prune=now

    # Switch back to original branch if it still exists
    if git show-ref --verify --quiet refs/heads/"$current_branch"; then
        git checkout "$current_branch"
    fi
}

# Main execution
main() {
    print_message "$YELLOW" "Starting Git branch cleanup..."
    
    check_git_repo
    check_working_directory
    fetch_latest
    
    # Prompt for confirmation
    read -p "This will delete all branches except main and master. Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message "$YELLOW" "Operation cancelled"
        exit 0
    fi

    cleanup_branches
    
    print_message "$GREEN" "Branch cleanup completed successfully!"
}

main "$@"