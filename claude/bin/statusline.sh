#!/usr/bin/env bash
# Claude Code status line — native rate-limit / burn / context visibility.
# Reads the session JSON on stdin (see https://code.claude.com/docs/en/statusline).
#
# Line 1: model · repo · branch
# Line 2: color bars for 5h + weekly rate limits and context, + projected
#         time-until-cap (derived from rate-limit deltas) + session cost.
#
# Self-contained: only needs jq + git. No network, no Node/ccusage subprocess.
# Rate-limit data (rate_limits.*) appears only for Pro/Max after the first API
# response, and can be absent per account/version — every field degrades safely.

# ---- on/off toggle ---------------------------------------------------------
# `statusline.sh toggle|on|off` flips a flag file; when disabled the status
# line renders nothing. Lets you hide it without editing settings.json.
FLAG="$HOME/.claude/.statusline-disabled"
case "$1" in
  off)    : > "$FLAG"; echo "status line: OFF"; exit 0 ;;
  on)     rm -f "$FLAG"; echo "status line: ON"; exit 0 ;;
  toggle) if [ -f "$FLAG" ]; then rm -f "$FLAG"; echo "status line: ON";
          else : > "$FLAG"; echo "status line: OFF"; fi; exit 0 ;;
esac
[ -f "$FLAG" ] && exit 0   # disabled → render nothing

input=$(cat)

# ---- helpers ---------------------------------------------------------------
j() { printf '%s' "$input" | jq -r "$1" 2>/dev/null; }

# Muted 256-color palette (soft, professional — not neon).
C_RESET=$'\033[0m'; C_DIM=$'\033[38;5;244m'; C_BOLD=$'\033[1m'
C_GREEN=$'\033[38;5;108m'    # soft sage
C_YELLOW=$'\033[38;5;179m'   # muted amber
C_RED=$'\033[38;5;167m'      # muted terracotta
C_CYAN=$'\033[38;5;109m'     # soft teal (repo)
C_BLUE=$'\033[38;5;103m'     # slate (branch)
C_MAGENTA=$'\033[38;5;139m'  # dusty mauve (model)

# color for a "used %" value: low=green, mid=yellow, high=red
usecolor() { # $1=pct(int)
  if   [ "$1" -ge 85 ]; then printf '%s' "$C_RED"
  elif [ "$1" -ge 60 ]; then printf '%s' "$C_YELLOW"
  else printf '%s' "$C_GREEN"; fi
}

# 10-cell progress bar for a used %
bar() { # $1=pct(int)
  local pct=$1 w=10 filled i out=""
  [ "$pct" -lt 0 ] && pct=0; [ "$pct" -gt 100 ] && pct=100
  filled=$(( (pct + 5) / 10 ))
  for ((i=0;i<w;i++)); do
    if [ "$i" -lt "$filled" ]; then out+="▓"; else out+="░"; fi
  done
  printf '%s' "$out"
}

# humanize seconds -> "2h10m" / "45m" / "3d4h"
dur() { # $1=seconds
  local s=$1
  [ "$s" -lt 0 ] && { printf '0m'; return; }
  local d=$((s/86400)) h=$(((s%86400)/3600)) m=$(((s%3600)/60))
  if   [ "$d" -gt 0 ]; then printf '%dd%dh' "$d" "$h"
  elif [ "$h" -gt 0 ]; then printf '%dh%dm' "$h" "$m"
  else printf '%dm' "$m"; fi
}

int() { printf '%.0f' "${1:-0}" 2>/dev/null || printf '0'; }

# ---- extract fields --------------------------------------------------------
MODEL=$(j '.model.display_name'); [ -z "$MODEL" ] || [ "$MODEL" = "null" ] && MODEL="?"
CWD=$(j '.workspace.current_dir'); [ -z "$CWD" ] || [ "$CWD" = "null" ] && CWD="$PWD"
REPO=$(j '.workspace.repo.name')
[ -z "$REPO" ] || [ "$REPO" = "null" ] && REPO=$(basename "$CWD")

CTX=$(int "$(j '.context_window.used_percentage // 0')")
COST=$(j '.cost.total_cost_usd // 0')
SESSION=$(j '.session_id // "nosession"')

FIVE=$(j '.rate_limits.five_hour.used_percentage // empty')
FIVE_RESET=$(j '.rate_limits.five_hour.resets_at // empty')
WEEK=$(j '.rate_limits.seven_day.used_percentage // empty')
WEEK_RESET=$(j '.rate_limits.seven_day.resets_at // empty')

NOW=$(date +%s)

# git branch (fast, no status)
BRANCH=$(git -C "$CWD" rev-parse --abbrev-ref HEAD 2>/dev/null)

# ---- derive burn / time-until-cap from 5h rate-limit deltas ----------------
# State per session: "<ts> <five_pct> <rate_ema(pct/sec)>"
STATE_DIR="${TMPDIR:-/tmp}/cc-statusline"
mkdir -p "$STATE_DIR" 2>/dev/null
STATE_FILE="$STATE_DIR/${SESSION}.state"

CAP_ETA=""
if [ -n "$FIVE" ]; then
  FIVE_I=$(int "$FIVE")
  rate_ema=""
  if [ -f "$STATE_FILE" ]; then
    read -r p_ts p_five p_ema < "$STATE_FILE"
    dt=$(( NOW - ${p_ts:-$NOW} ))
    # only update rate when time advanced and usage went up (else window reset/idle)
    if [ "$dt" -ge 1 ] && awk "BEGIN{exit !($FIVE > ${p_five:-0})}"; then
      inst=$(awk "BEGIN{printf \"%.6f\", ($FIVE - $p_five)/$dt}")
      if [ -n "$p_ema" ] && awk "BEGIN{exit !(${p_ema:-0} > 0)}"; then
        rate_ema=$(awk "BEGIN{printf \"%.6f\", ${p_ema}*0.6 + $inst*0.4}")
      else
        rate_ema="$inst"
      fi
    else
      # idle or reset: decay slightly, keep prior estimate
      rate_ema="${p_ema:-}"
    fi
  fi
  # persist
  printf '%s %s %s\n' "$NOW" "$FIVE" "${rate_ema:-}" > "$STATE_FILE"

  # project time until the 5h window hits 100%
  if [ -n "$rate_ema" ] && awk "BEGIN{exit !($rate_ema > 0)}"; then
    secs=$(awk "BEGIN{printf \"%d\", (100 - $FIVE)/$rate_ema}")
    reset_in=999999999
    [ -n "$FIVE_RESET" ] && reset_in=$(( FIVE_RESET - NOW ))
    if [ "$secs" -ge "$reset_in" ]; then
      CAP_ETA="${C_GREEN}safe→reset${C_RESET}"      # window resets before you'd cap
    else
      CAP_ETA="${C_RED}~$(dur "$secs")→cap${C_RESET}"
    fi
  else
    CAP_ETA="${C_DIM}burn idle${C_RESET}"
  fi
fi

# ---- render ----------------------------------------------------------------
# Line 1
L1="${C_BOLD}${C_MAGENTA}${MODEL}${C_RESET} ${C_DIM}·${C_RESET} ${C_CYAN}${REPO}${C_RESET}"
[ -n "$BRANCH" ] && L1+=" ${C_DIM}·${C_RESET} ${C_BLUE}⎇ ${BRANCH}${C_RESET}"

# Line 2 segments
seg_ratelimit() { # $1=label $2=pct $3=reset_epoch
  local label=$1 pct reset=$3 col
  if [ -z "$2" ]; then
    printf '%s%s --%s' "$C_DIM" "$label" "$C_RESET"; return
  fi
  pct=$(int "$2"); col=$(usecolor "$pct")
  local tail=""
  [ -n "$reset" ] && tail=" ${C_DIM}↻$(dur $((reset - NOW)))${C_RESET}"
  printf '%s%s %s%s %d%%%s%s' "$C_DIM" "$label" "$col" "$(bar "$pct")" "$pct" "$C_RESET" "$tail"
}

CTX_COL=$(usecolor "$CTX")
COST_FMT=$(awk "BEGIN{printf \"%.2f\", ${COST:-0}}")

L2="$(seg_ratelimit '5h'  "$FIVE" "$FIVE_RESET")"
L2+=" ${C_DIM}│${C_RESET} $(seg_ratelimit 'wk' "$WEEK" "$WEEK_RESET")"
L2+=" ${C_DIM}│${C_RESET} ${C_DIM}ctx${C_RESET} ${CTX_COL}$(bar "$CTX") ${CTX}%${C_RESET}"
L2+=" ${C_DIM}│${C_RESET} ${C_GREEN}\$${COST_FMT}${C_RESET}"
[ -n "$CAP_ETA" ] && L2+=" ${C_DIM}│${C_RESET} $CAP_ETA"

printf '%s\n%s' "$L1" "$L2"
