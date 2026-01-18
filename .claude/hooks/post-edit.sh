#!/bin/bash
# =============================================================================
# Post-Edit Hook for Claude Code Agents
# =============================================================================
# This hook runs after file edits/writes to:
# - Log file changes for audit
# - Optionally run linting on changed files
# - Validate file integrity
# =============================================================================

set -eu

# Read input from stdin (JSON format)
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Exit early if no file path
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# =============================================================================
# AUDIT LOGGING (Optional)
# =============================================================================

# Uncomment to enable file change logging
# LOG_DIR="$CLAUDE_PROJECT_DIR/.claude/logs"
# mkdir -p "$LOG_DIR"
# echo "$(date -Iseconds) | $TOOL_NAME | $FILE_PATH" >> "$LOG_DIR/file-changes.log"

# =============================================================================
# AUTO-LINTING (Optional)
# =============================================================================

# Get file extension
EXT="${FILE_PATH##*.}"

# Uncomment to enable auto-linting for TypeScript/JavaScript files
# if [[ "$EXT" == "ts" || "$EXT" == "tsx" || "$EXT" == "js" || "$EXT" == "jsx" ]]; then
#   # Run ESLint fix on the file (non-blocking)
#   if command -v npx &> /dev/null; then
#     npx eslint --fix "$FILE_PATH" 2>/dev/null || true
#   fi
# fi

# =============================================================================
# FILE VALIDATION
# =============================================================================

# Block edits to critical config files without proper review
# Uses pattern matching to catch .env* variants (e.g., .env.staging, .env.test)
FILENAME=$(basename "$FILE_PATH")

# Check for critical files using case pattern matching
case "$FILENAME" in
  .env|.env.*|package-lock.json|yarn.lock|pnpm-lock.yaml)
    echo "WARNING: Critical file '$FILENAME' was modified. Please review changes carefully." >&2
    # Note: exit 0 to allow but warn, exit 2 to block
    exit 0
    ;;
esac

# =============================================================================
# PASSED: Edit completed successfully
# =============================================================================
exit 0
