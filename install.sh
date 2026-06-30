#!/bin/bash
# Same script works for BOTH downloaded repos AND remote installations

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "==============================================="
echo " WAS Document Time Machine Installer (v2.0.0)"
echo "==============================================="

if ! command -v python3 &> /dev/null; then
    echo -e "\n${RED}ERROR: Python 3 is required.${NC}"
    echo "Ubuntu/Debian: sudo apt install python3-pip"
    echo "macOS: brew install python3"
    echo "Windows: https://python.org/downloads"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 detected${NC}"

echo -e "\n${BLUE}Installing WAS package...${NC}"

INSTALL_FLAGS=""

if ! python3 -m pip install $INSTALL_FLAGS . ; then
    echo -e "${YELLOW}Standard install failed, trying with --break-system-packages...${NC}"
    if python3 -m pip install $INSTALL_FLAGS --break-system-packages . ; then
        :
    else
        echo -e "\n${RED}ERROR: pip install failed. Manual install options:${NC}"
        echo ""
        echo "  Option 1 (recommended): Use a virtual environment:"
        echo "    python3 -m venv ~/.venvs/was && source ~/.venvs/was/bin/activate && pip install ."
        echo ""
        echo "  Option 2: Force install:"
        echo "    pip3 install --user --break-system-packages ."
        echo ""
        echo "  Option 3: System-wide (may need sudo):"
        echo "    sudo pip3 install ."
        exit 1
    fi
fi

USER_BIN="$HOME/.local/bin"

if command -v was &> /dev/null; then
    echo -e "\n${GREEN}✅ SUCCESS! WAS is installed.${NC}"
    echo "Run: ${BLUE}was --help${NC}"

elif [ -x "$USER_BIN/was" ]; then
    echo -e "\n${YELLOW}⚠️  'was' is installed but '$USER_BIN' is not in your PATH.${NC}"

    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
        RC_FILE="$HOME/.zshrc"
    else
        RC_FILE="$HOME/.bashrc"
    fi

    read -p "Automatically add to PATH? [Y/n] " response
    if [[ ! "$response" =~ ^[Nn] ]]; then
        if ! grep -q "$USER_BIN" "$RC_FILE"; then
            echo "export PATH=\"$USER_BIN:\$PATH\"" >> "$RC_FILE"
        fi
        export PATH="$USER_BIN:$PATH"
        echo -e "${GREEN}✓ Added to $RC_FILE${NC}"
        echo -e "${GREEN}✅ SUCCESS! WAS is installed and ready.${NC}"
        echo "Run: ${BLUE}was --help${NC}"
    else
        echo -e "\n${YELLOW}Okay. Fix it manually with:${NC}"
        echo "  echo 'export PATH=\"$USER_BIN:\$PATH\"' >> $RC_FILE"
        echo "  source $RC_FILE"
    fi
else
    echo -e "\n${RED}⚠️  Installation may have completed, but 'was' was not found.${NC}"
    echo "Check: python3 -m pip show was-cli"
    exit 1
fi
