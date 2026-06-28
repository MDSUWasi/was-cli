#!/bin/bash
# WAS Document Time Machine — Uninstaller

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================"
echo " WAS Uninstaller"
echo "======================================"

# --- Uninstall pip package ---
echo "Uninstalling WAS package..."

if ! python3 -m pip uninstall was-cli -y 2>/dev/null; then
    echo -e "${YELLOW}Trying with --break-system-packages...${NC}"
    if ! python3 -m pip uninstall was-cli -y --break-system-packages 2>/dev/null; then
        echo -e "${RED}Could not uninstall via pip. Was it installed differently?${NC}"
        echo "Try: pip3 uninstall was-cli"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Package removed${NC}"

# --- Remove PATH entry ---
# Detect shell config file
if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
    RC_FILE="$HOME/.zshrc"
else
    RC_FILE="$HOME/.bashrc"
fi

if [ -f "$RC_FILE" ] && grep -q '.local/bin' "$RC_FILE"; then
    read -p "Remove WAS PATH entry from $RC_FILE? [Y/n] " response
    if [[ ! "$response" =~ ^[Nn] ]]; then
        # FIX: Only remove lines that export PATH with .local/bin,
        # not every line that happens to mention .local/bin
        sed -i '/export PATH=.*\.local\/bin/d' "$RC_FILE"
        echo -e "${GREEN}✓ PATH entry removed from $RC_FILE${NC}"
        echo -e "${YELLOW}Restart your terminal or run: source $RC_FILE${NC}"
    fi
fi

echo -e "\n${GREEN}✅ WAS has been uninstalled.${NC}"