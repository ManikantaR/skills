#!/usr/bin/env bash
# GitHub Copilot CLI status line — EXPERIMENTAL feature (~/.copilot/settings.json,
# statusLine.command). Copilot pipes a JSON payload on stdin after each model
# response, same mechanism as Claude Code, but with DIFFERENT field names and a
# different billing model (Copilot meters "premium requests", not Claude's
# 5-hour/weekly windows). So this variant shows: model · repo/branch, then
# context %, tokens, and premium-requests if present — no 5h/weekly bars.
#
# ⚠ VERIFY THE FIELD MAP: the payload schema is unstable (experimental since
# 2026-05). Dump your real payload and adjust the `j '...'` paths below:
#     ./statusline.sh debug     # pretty-prints the raw stdin JSON, then exits
#
# Deps: jq + git. Toggle: `statusline.sh on|off|toggle`.

FLAG="$HOME/.copilot/.statusline-disabled"
case "$1" in
  debug)  cat | jq . 2>/dev/null || cat; exit 0 ;;
  off)    : > "$FLAG"; echo "copilot status line: OFF"; exit 0 ;;
  on)     rm -f "$FLAG"; echo "copilot status line: ON"; exit 0 ;;
  toggle) if [ -f "$FLAG" ]; then rm -f "$FLAG"; echo "ON"; else : > "$FLAG"; echo "OFF"; fi; exit 0 ;;
esac
[ -f "$FLAG" ] && exit 0

input=$(cat)
j() { printf '%s' "$input" | jq -r "$1" 2>/dev/null; }

# ---- muted 256-color palette (matches the Claude variant) -------------------
C_RESET=$'\033[0m'; C_DIM=$'\033[38;5;244m'; C_BOLD=$'\033[1m'
C_GREEN=$'\033[38;5;108m'; C_YELLOW=$'\033[38;5;179m'; C_RED=$'\033[38;5;167m'
C_CYAN=$'\033[38;5;109m'; C_BLUE=$'\033[38;5;103m'; C_MAGENTA=$'\033[38;5;139m'

usecolor() { if [ "$1" -ge 85 ]; then printf '%s' "$C_RED"
  elif [ "$1" -ge 60 ]; then printf '%s' "$C_YELLOW"; else printf '%s' "$C_GREEN"; fi; }
bar() { local p=$1 w=10 f i o=""; [ "$p" -lt 0 ]&&p=0; [ "$p" -gt 100 ]&&p=100
  f=$(((p+5)/10)); for ((i=0;i<w;i++)); do [ "$i" -lt "$f" ]&&o+="▓"||o+="░"; done; printf '%s' "$o"; }
int() { printf '%.0f' "${1:-0}" 2>/dev/null || printf '0'; }

# ---- FIELD MAP — adjust to your captured payload (defensive multi-path) ------
MODEL=$(j '.model.display_name // .model.name // .model // empty'); [ -z "$MODEL" ] && MODEL="Copilot"
CWD=$(j '.cwd // .workspace.current_dir // empty'); [ -z "$CWD" ] && CWD="$PWD"
REPO=$(j '.workspace.repo.name // empty'); [ -z "$REPO" ] && REPO=$(basename "$CWD")
CTX=$(int "$(j '.context_window.used_percentage // .context.used_percentage // .contextUsage.percent // 0')")
TOKENS=$(j '.tokens.used // .usage.total_tokens // .token_usage.total // empty')
PREMIUM=$(j '.premium_requests.used // .premiumRequests.used // .quota.premium_requests.used // empty')
COST=$(j '.cost.total_cost_usd // empty')

BRANCH=$(git -C "$CWD" rev-parse --abbrev-ref HEAD 2>/dev/null)

# ---- render (two lines) -----------------------------------------------------
L1="${C_BOLD}${C_MAGENTA}${MODEL}${C_RESET} ${C_DIM}·${C_RESET} ${C_CYAN}${REPO}${C_RESET}"
[ -n "$BRANCH" ] && L1+=" ${C_DIM}·${C_RESET} ${C_BLUE}⎇ ${BRANCH}${C_RESET}"

CTX_COL=$(usecolor "$CTX")
L2="${C_DIM}ctx${C_RESET} ${CTX_COL}$(bar "$CTX") ${CTX}%${C_RESET}"
[ -n "$TOKENS" ]  && L2+=" ${C_DIM}│ ${TOKENS} tok${C_RESET}"
[ -n "$PREMIUM" ] && L2+=" ${C_DIM}│${C_RESET} ${C_YELLOW}${PREMIUM} premium${C_RESET}"
[ -n "$COST" ]    && L2+=" ${C_DIM}│${C_RESET} ${C_GREEN}\$$(awk "BEGIN{printf \"%.2f\",$COST}")${C_RESET}"

printf '%s\n%s' "$L1" "$L2"
