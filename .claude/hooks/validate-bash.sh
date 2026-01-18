#!/bin/bash
# =============================================================================
# Bash Command Validation Hook for Claude Code Agents
# =============================================================================
# This hook validates bash commands before execution to prevent:
# - Destructive operations (rm -rf, DROP DATABASE, etc.)
# - Production environment access
# - Unauthorized network requests
# - Secret/credential exposure
# =============================================================================

set -eu

# Read input from stdin (JSON format)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Exit early if no command
if [ -z "$COMMAND" ]; then
  exit 0
fi

# =============================================================================
# BLOCKLIST: Dangerous patterns that should NEVER run
# =============================================================================

# Destructive file operations
# Matches rm with recursive + force flags in any order/combination:
# rm -rf, rm -fr, rm -r -f, rm -f -r, rm --recursive -f, rm -r --force, etc.
# Uses two checks: one for combined flags (-rf/-fr) and one for separate flags
if echo "$COMMAND" | grep -iE '\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r|--recursive\b.*-f|-f.*--recursive|--force\b.*-r|-r.*--force|--recursive\b.*--force|--force\b.*--recursive)\b' > /dev/null; then
  echo "BLOCKED: Recursive delete operations (rm -rf) are not allowed" >&2
  exit 2
fi

# Also block rm with just --recursive or -r followed by dangerous paths
if echo "$COMMAND" | grep -iE '\brm\s+(-[a-z]*r|--recursive)\s+(/|\.\.|~|\$HOME|\$\{HOME\}|/\*)' > /dev/null; then
  echo "BLOCKED: Recursive delete of system/home paths is not allowed" >&2
  exit 2
fi

# Database destructive operations
if echo "$COMMAND" | grep -iE '\b(DROP\s+(DATABASE|TABLE|INDEX|SCHEMA)|TRUNCATE|DELETE\s+FROM.*WHERE\s+1\s*=\s*1)\b' > /dev/null; then
  echo "BLOCKED: Destructive database operations require manual execution" >&2
  exit 2
fi

# Production environment access
if echo "$COMMAND" | grep -iE '(--env[= ]prod|--environment[= ]prod|-e\s+prod|NODE_ENV=prod|RAILS_ENV=prod)' > /dev/null; then
  echo "BLOCKED: Production environment commands require manual approval" >&2
  exit 2
fi

if echo "$COMMAND" | grep -iE '\b(prod|production)\.(example\.com|api\.|db\.|database\.)' > /dev/null; then
  echo "BLOCKED: Production host access requires manual approval" >&2
  exit 2
fi

# Privilege escalation (matches sudo anywhere, including after shell separators)
if echo "$COMMAND" | grep -iE '(^|[;&|]\s*)\bsudo\b' > /dev/null; then
  echo "BLOCKED: sudo commands are not allowed" >&2
  exit 2
fi

# Arbitrary code execution (matches eval/exec anywhere, including after shell separators)
if echo "$COMMAND" | grep -iE '(^|[;&|]\s*)\b(eval|exec)\b' > /dev/null; then
  echo "BLOCKED: eval/exec commands are not allowed" >&2
  exit 2
fi

# Network requests to external hosts (potential data exfiltration)
# Matches: http/https/ftp URLs, bare host:port patterns, upload flags (-d, --data, -X POST/PUT)
if echo "$COMMAND" | grep -iE '\b(curl|wget)\b.*(https?://|ftp://|-d\s|--data|-X\s*(POST|PUT)|@/)' > /dev/null; then
  echo "BLOCKED: External network requests require manual approval" >&2
  exit 2
fi

# Netcat connections (matches nc/netcat with any host/port pattern)
if echo "$COMMAND" | grep -iE '\b(nc|netcat)\b\s+[^|;&]+' > /dev/null; then
  echo "BLOCKED: Netcat connections require manual approval" >&2
  exit 2
fi

# SSH/remote access (matches anywhere in command, including after shell operators)
if echo "$COMMAND" | grep -iE '(^|[;&|]\s*)\b(ssh|scp|rsync)\b' > /dev/null; then
  echo "BLOCKED: Remote access commands require manual approval" >&2
  exit 2
fi

# Cloud CLI production commands
if echo "$COMMAND" | grep -iE '\b(aws|gcloud|az)\s.*prod' > /dev/null; then
  echo "BLOCKED: Cloud CLI production commands require manual approval" >&2
  exit 2
fi

# Git force push
if echo "$COMMAND" | grep -iE 'git\s+push\s+.*(-f|--force)' > /dev/null; then
  echo "BLOCKED: Force push requires manual approval" >&2
  exit 2
fi

# Environment variable exposure (matches lowercase, camelCase, and names with digits)
if echo "$COMMAND" | grep -iE '\b(printenv|env\s*$)' > /dev/null; then
  echo "BLOCKED: Commands that expose environment secrets are not allowed" >&2
  exit 2
fi

# Block echo/printf of variables containing KEY, SECRET, PASSWORD, TOKEN, CREDENTIAL
if echo "$COMMAND" | grep -iE '\b(echo|printf)\b.*\$[A-Za-z0-9_]*(KEY|SECRET|PASSWORD|TOKEN|CREDENTIAL)\b' > /dev/null; then
  echo "BLOCKED: Commands that expose environment secrets are not allowed" >&2
  exit 2
fi

# File permission changes that are too permissive (includes optional leading zero)
if echo "$COMMAND" | grep -iE 'chmod\s+(0?777|0?666|a\+rwx)' > /dev/null; then
  echo "BLOCKED: Overly permissive chmod operations are not allowed" >&2
  exit 2
fi

# =============================================================================
# ALLOWLIST: Safe command prefixes (optional - uncomment to enable strict mode)
# =============================================================================

# Uncomment below for strict allowlist mode (only these commands allowed)
# ALLOWED_PREFIXES="^(npm|npx|yarn|pnpm|node|git|jest|tsc|eslint|prettier|prisma|cat|ls|pwd|echo|mkdir|cp|mv|head|tail|wc|sort|uniq|grep|find|which|whoami)"
# if ! echo "$COMMAND" | grep -iE "$ALLOWED_PREFIXES" > /dev/null; then
#   echo "BLOCKED: Command not in allowlist. Only npm, git, node, and related tools are permitted." >&2
#   exit 2
# fi

# =============================================================================
# PASSED: Command is allowed
# =============================================================================
exit 0
