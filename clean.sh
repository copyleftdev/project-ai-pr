#!/bin/bash

###############################################################################
# Git Branch Cleanup Script
# 
# This script safely removes all local and remote branches except master and main.
# It includes safety checks, error handling, and detailed logging of operations.
#
# Usage: 
#   ./git-cleanup.sh
#
# Requirements:
#   - Git must be installed
#   - Script must be run from within a git repository
#   - User must have appropriate permissions for branch deletion
#
# Safety Features:
#   - Preserves master and main branches
#   - Checks for uncommitted changes
#   - Requires confirmation before deletion
#   - Validates git repository status
#   - Handles network and command failures
###############################################################################

# Exit on any error, but ensure we handle the error appropriately
set -eE

# Text colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error handler function
handle_error() {
    local line_number=$1
    local error_code=$2
    print_message "$RED" "Error occurred in line ${line_number} (Exit code: ${error_code})"
    case ${error_code} in
        128)
            print_message "$RED" "Git repository error: Command failed due to repository state"
            ;;
        1)
            print_message "$RED" "General error: Command failed to execute properly"
            ;;
        *)
            print_message "$RED" "Unknown error occurred"
            ;;
    esac
    exit ${error_code}
}

# Set up error trap
trap 'handle_error ${LINENO} $?' ERR

###############################################################################
# Utility Functions
###############################################################################

# Function: print_message
# Description: Prints a colored message to stdout
# Parameters:
#   $1 - Color code
#   $2 - Message to print
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function: check_git_repo
# Description: Validates that the current directory is a git repository
# Exits with error if not in a git repository
check_git_repo() {
    print_message "$YELLOW" "Checking repository status..."
    if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        print_message "$RED" "Error: Not a git repository"
        print_message "$YELLOW" "Please run this script from within a git repository"
        exit 1
    fi
}

# Function: check_git_installed
# Description: Verifies that git is installed and accessible
check_git_installed() {
    if ! command -v git >/dev/null 2>&1; then
        print_message "$RED" "Error: Git is not installed"
        print_message "$YELLOW" "Please install git before running this script"
        exit 1
    fi
}

# Function: check_working_directory
# Description: Ensures the working directory is clean before proceeding
check_working_directory() {
    local has_changes=0
    
    # Check for staged changes
    if ! git diff --staged --quiet; then
        print_message "$RED" "Error: You have staged changes"
        has_changes=1
    fi
    
    # Check for unstaged changes
    if ! git diff --quiet; then
        print_message "$RED" "Error: You have unstaged changes"
        has_changes=1
    fi
    
    # Check for untracked files
    if [ -n "$(git ls-files --others --exclude-standard)" ]; then
        print_message "$RED" "Error: You have untracked files"
        has_changes=1
    fi
    
    if [ $has_changes -eq 1 ]; then
        print_message "$YELLOW" "Please commit or stash your changes before proceeding"
        exit 1
    fi
}

# Function: fetch_latest
# Description: Fetches the latest changes from all remotes and prunes deleted branches
# Handles network errors and remote connectivity issues
fetch_latest() {
    print_message "$YELLOW" "Fetching latest changes from remote..."
    if ! git fetch --all --prune; then
        print_message "$RED" "Error: Failed to fetch from remote"
        print_message "$YELLOW" "Please check your internet connection and remote repository access"
        exit 1
    fi
}

###############################################################################
# Main Cleanup Function
###############################################################################

# Function: cleanup_branches
# Description: Performs the main branch cleanup operation
# - Switches to main/master branch
# - Deletes local branches
# - Deletes remote branches
# - Performs garbage collection
cleanup_branches() {
    local current_branch=$(git branch --show-current)
    local default_branch=""
    
    # Determine and switch to default branch
    if git show-ref --verify --quiet refs/heads/main; then
        default_branch="main"
    elif git show-ref --verify --quiet refs/heads/master; then
        default_branch="master"
    else
        print_message "$RED" "Error: Neither main nor master branch found"
        print_message "$YELLOW" "Please create either a main or master branch first"
        exit 1
    fi
    
    print_message "$YELLOW" "Switching to ${default_branch} branch..."
    if ! git checkout "$default_branch"; then
        print_message "$RED" "Error: Failed to switch to ${default_branch} branch"
        exit 1
    fi

    # Delete local branches
    print_message "$YELLOW" "Deleting local branches..."
    local local_branches=$(git branch | grep -v "main\|master\|\*" || true)
    if [ -n "$local_branches" ]; then
        echo "$local_branches" | xargs -r git branch -D
    else
        print_message "$GREEN" "No local branches to delete"
    fi

    # Delete remote branches
    print_message "$YELLOW" "Deleting remote branches..."
    local remote_branches=$(git branch -r | grep -v "main\|master" | sed 's/origin\///' || true)
    if [ -n "$remote_branches" ]; then
        echo "$remote_branches" | xargs -r -I {} git push origin --delete {}
    else
        print_message "$GREEN" "No remote branches to delete"
    fi

    # Clean up references and optimize repository
    print_message "$YELLOW" "Performing repository cleanup..."
    git gc --prune=now

    # Return to original branch if it still exists
    if [ "$current_branch" != "$default_branch" ] && \
       git show-ref --verify --quiet refs/heads/"$current_branch"; then
        print_message "$YELLOW" "Returning to original branch: ${current_branch}"
        git checkout "$current_branch"
    fi
}

###############################################################################
# Main Script Execution
###############################################################################

main() {
    print_message "$YELLOW" "Starting Git branch cleanup..."
    
    # Initial checks
    check_git_installed
    check_git_repo
    check_working_directory
    fetch_latest
    
    # Prompt for confirmation
    print_message "$YELLOW" "WARNING: This will delete all branches except main and master."
    print_message "$YELLOW" "This operation cannot be undone!"
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message "$YELLOW" "Operation cancelled by user"
        exit 0
    fi

    # Perform cleanup
    cleanup_branches
    
    print_message "$GREEN" "Branch cleanup completed successfully!"
    print_message "$GREEN" "Your repository is now clean!"
}

# Execute main function
main "$@"