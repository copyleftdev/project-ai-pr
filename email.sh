#!/usr/bin/env bash
#
# parse_email.sh - A simple yet high-quality Bash script to parse a raw email file.
#
# Usage:
#   parse_email.sh <email_file>
#
# Description:
#   This script extracts the "From", "To", "Subject", and "Date" headers
#   from a raw email file, then prints them along with the message body.
#   The body is assumed to begin after the first blank line.
#
# Note:
#   Real-world email parsing can be significantly more complex than this
#   script demonstrates. For complex MIME, encodings, or multi-line headers,
#   consider a dedicated parser.

###############################################################################
# Bash Strict Mode
###############################################################################
set -euo pipefail  # Exit on error, undefined variable, or failed pipe
IFS=$'\n\t'        # Safe Internal Field Separator

###############################################################################
# Global Constants
###############################################################################
readonly SCRIPT_NAME="${0##*/}"

###############################################################################
# Functions
###############################################################################

# ------------------------------------------------------------------------------
# usage()
#   Display usage message and exit.
# ------------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage:
  $SCRIPT_NAME <email_file>

Description:
  Parse a raw email file and extract the "From", "To", "Subject", "Date", 
  and body. The body is assumed to begin after the first blank line.

Example:
  $SCRIPT_NAME example.eml
EOF
  exit 1
}

# ------------------------------------------------------------------------------
# check_requirements()
#   Verify that necessary command-line tools are available.
# ------------------------------------------------------------------------------
check_requirements() {
  local -a required_commands=("grep" "awk" "sed")
  for cmd in "${required_commands[@]}"; do
    if ! command -v "$cmd" &>/dev/null; then
      echo "Error: '$cmd' command not found. Please install it." >&2
      exit 1
    fi
  done
}

# ------------------------------------------------------------------------------
# parse_headers() 
#   Extract the primary headers: From, To, Subject, and Date.
#   Arguments:
#     1. The path to the email file
#   Outputs:
#     Global variables: HEADER_FROM, HEADER_TO, HEADER_SUBJECT, HEADER_DATE
# ------------------------------------------------------------------------------
parse_headers() {
  local email_file="$1"

  HEADER_FROM="$(grep -m 1 '^From:'    "$email_file" || true)"
  HEADER_TO="$(grep -m 1 '^To:'        "$email_file" || true)"
  HEADER_SUBJECT="$(grep -m 1 '^Subject:' "$email_file" || true)"
  HEADER_DATE="$(grep -m 1 '^Date:'    "$email_file" || true)"

  # Remove the field label and leading spaces
  HEADER_FROM="${HEADER_FROM#From:}"
  HEADER_TO="${HEADER_TO#To:}"
  HEADER_SUBJECT="${HEADER_SUBJECT#Subject:}"
  HEADER_DATE="${HEADER_DATE#Date:}"

  # Trim leading whitespace
  HEADER_FROM="$(echo "$HEADER_FROM" | sed 's/^[[:space:]]*//')"
  HEADER_TO="$(echo "$HEADER_TO" | sed 's/^[[:space:]]*//')"
  HEADER_SUBJECT="$(echo "$HEADER_SUBJECT" | sed 's/^[[:space:]]*//')"
  HEADER_DATE="$(echo "$HEADER_DATE" | sed 's/^[[:space:]]*//')"
}

# ------------------------------------------------------------------------------
# parse_body()
#   Extract the body of the email (all lines after the first blank line).
#   Arguments:
#     1. The path to the email file
#   Outputs:
#     BODY_CONTENT
# ------------------------------------------------------------------------------
parse_body() {
  local email_file="$1"
  BODY_CONTENT="$(
    awk '
      BEGIN { in_body = 0 }
      /^[[:space:]]*$/ { in_body = 1; next }
      { if (in_body == 1) print }
    ' "$email_file"
  )"
}

# ------------------------------------------------------------------------------
# main()
#   Main function coordinating the parsing and output.
# ------------------------------------------------------------------------------
main() {
  # Check arguments
  if [[ $# -ne 1 ]]; then
    usage
  fi

  local email_file="$1"

  # Validate the email file
  if [[ ! -f "$email_file" ]]; then
    echo "Error: File '$email_file' not found or not a regular file." >&2
    exit 1
  fi

  # Ensure required tools are installed
  check_requirements

  # Parse the email
  parse_headers "$email_file"
  parse_body "$email_file"

  # Print results
  echo "From:    ${HEADER_FROM:-"(Not found)"}"
  echo "To:      ${HEADER_TO:-"(Not found)"}"
  echo "Subject: ${HEADER_SUBJECT:-"(Not found)"}"
  echo "Date:    ${HEADER_DATE:-"(Not found)"}"
  echo
  echo "Body:"
  echo "------"
  echo "${BODY_CONTENT:-"(No body found)"}"
}

###############################################################################
# Entry Point
###############################################################################
main "$@"
