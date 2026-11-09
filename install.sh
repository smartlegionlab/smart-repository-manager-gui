#!/bin/bash
set -e

REPO_URL="https://github.com/smartlegionlab/smart-repository-manager-gui.git"
APP_NAME="Smart Repository Manager"
APP_ID="smart-repository-manager-gui"
APP_VERSION="1.3.0"
INSTALL_DIR="$HOME/.local/share/$APP_ID"
VENV_DIR="$INSTALL_DIR/venv"
APPS_DIR="$HOME/.local/share/applications"
MENU_ENTRY="$APPS_DIR/$APP_ID.desktop"
DESKTOP_FILE="$APP_ID.desktop"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${GREEN}==>${NC} $*"; }
warn()  { echo -e "${YELLOW}==>${NC} $*"; }
error() { echo -e "${RED}==>${NC} $*" >&2; }
step()  { echo -e "${BOLD}${BLUE}[*]${NC} $*"; }

banner() {
    echo ""
    echo -e "${BOLD}${GREEN}==============================================${NC}"
    echo -e "${BOLD}${GREEN}  Smart Repository Manager - Installer${NC}"
    echo -e "${BOLD}${GREEN}==============================================${NC}"
    echo ""
}

banner

echo "This installer will:"
echo "  1. Download the application source code"
echo "  2. Install it to:  $INSTALL_DIR"
echo "  3. Create a Python virtual environment and install dependencies"
echo "  4. Register the app in your application menu"
echo "  5. Optionally create a shortcut on your Desktop"
echo ""
echo -e "Your data will be stored separately in:"
echo -e "  ${BOLD}$HOME/smart_repository_manager${NC}"
echo "  (that folder is created by the app on first run)"
echo ""

step "Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
    error "python3 is required but not installed."
    exit 1
fi
PY_VER="$(python3 --version 2>&1)"
info "Found: $PY_VER"

step "Checking git..."
if ! command -v git >/dev/null 2>&1; then
    error "git is required but not installed."
    exit 1
fi
info "git found."

step "Cloning repository..."
TMP_CLONE="$(mktemp -d)"
info "From: $REPO_URL"
info "Into: $TMP_CLONE"
git clone --depth 1 "$REPO_URL" "$TMP_CLONE" >/dev/null 2>&1
SOURCE_DIR="$TMP_CLONE"
info "Repository cloned."

step "Preparing install directory..."
if [ -d "$INSTALL_DIR" ]; then
    warn "Existing install found - removing it first."
    rm -rf "$INSTALL_DIR"
fi
mkdir -p "$INSTALL_DIR"
info "Install directory: $INSTALL_DIR"

step "Copying application files..."
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='.git' --exclude='venv' --exclude='__pycache__' \
          "$SOURCE_DIR"/ "$INSTALL_DIR"/
else
    cp -r "$SOURCE_DIR"/. "$INSTALL_DIR"/
    rm -rf "$INSTALL_DIR/.git" "$INSTALL_DIR/venv"
fi
info "Files copied."

rm -rf "$TMP_CLONE"
info "Temporary clone removed."

step "Creating virtual environment..."
info "Location: $VENV_DIR"
python3 -m venv "$VENV_DIR"

step "Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" >/dev/null
info "Dependencies installed."

ICON_PATH="$INSTALL_DIR/data/icons/icon.png"
[ -f "$ICON_PATH" ] || ICON_PATH="system-run"

DESKTOP_CONTENT="[Desktop Entry]
Version=$APP_VERSION
Type=Application
Name=$APP_NAME
Comment=A powerful desktop application for managing GitHub repositories with intelligent synchronization, and comprehensive visual management tools.
Exec=$VENV_DIR/bin/python $INSTALL_DIR/app.py
Icon=$ICON_PATH
Terminal=false
Categories=Utility;Development;
StartupNotify=true
Keywords=git;github;repository;manager;sync;
"

step "Registering application in the menu..."
mkdir -p "$APPS_DIR"
echo "$DESKTOP_CONTENT" > "$MENU_ENTRY"
chmod +x "$MENU_ENTRY"
info "Menu entry created: $MENU_ENTRY"

step "Desktop shortcut..."
if [ "${SRM_CREATE_DESKTOP_SHORTCUT:-0}" = "1" ]; then
    DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
    [ -z "$DESKTOP_DIR" ] && DESKTOP_DIR="$HOME/Desktop"
    mkdir -p "$DESKTOP_DIR"
    echo "$DESKTOP_CONTENT" > "$DESKTOP_DIR/$DESKTOP_FILE"
    chmod +x "$DESKTOP_DIR/$DESKTOP_FILE"
    info "Desktop shortcut created: $DESKTOP_DIR/$DESKTOP_FILE"
else
    info "Skipped. Set SRM_CREATE_DESKTOP_SHORTCUT=1 to enable."
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
fi

echo ""
echo -e "${BOLD}${GREEN}==============================================${NC}"
echo -e "${BOLD}${GREEN}  Installation complete${NC}"
echo -e "${BOLD}${GREEN}==============================================${NC}"
echo ""
echo "  Application:      $INSTALL_DIR"
echo "  Virtual env:      $VENV_DIR"
echo "  Menu entry:       $MENU_ENTRY"
echo "  Your data folder: $HOME/smart_repository_manager"
echo ""
echo "  Launch: Application menu -> \"$APP_NAME\""
echo ""
echo "  Uninstall:"
echo "  curl -fsSL https://raw.githubusercontent.com/smartlegionlab/smart-repository-manager-gui/master/uninstall.sh | bash"
echo ""