#!/usr/bin/env bash
#
# parse_email.sh
# --------------
# Usage: parse_email.sh <email_file>
#
# Description:
#   This script reads a raw email file, extracts the "From", "To",
#   "Subject", and "Date" headers, then prints them along with the
#   message body. The body is assumed to start after the first empty line.
#

# Exit on error, undefined variable use, or failed pipe
set -euo pipefail

# Ensure an email file argument was provided
if [ $# -lt 1 ]; then
  echo "Usage: $0 <email_file>"
  exit 1
fi

EMAIL_FILE="$1"

# Extract headers (this approach takes the *first* match found)
FROM="$(grep -m 1 '^From:' "$EMAIL_FILE"    | sed 's/^From:[[:space:]]*//')"
TO="$(grep -m 1 '^To:' "$EMAIL_FILE"        | sed 's/^To:[[:space:]]*//')"
SUBJECT="$(grep -m 1 '^Subject:' "$EMAIL_FILE" | sed 's/^Subject:[[:space:]]*//')"
DATE="$(grep -m 1 '^Date:' "$EMAIL_FILE"    | sed 's/^Date:[[:space:]]*//')"

# Capture the email body (everything after the first blank line)
BODY="$(awk 'BEGIN { in_body = 0 }
  /^[[:space:]]*$/ { in_body = 1; next } 
  { if(in_body == 1) print }' "$EMAIL_FILE")"

# Print the parsed fields
echo "From:    $FROM"
echo "To:      $TO"
echo "Subject: $SUBJECT"
echo "Date:    $DATE"
echo
echo "Body:"
echo "------"
echo "$BODY"
