#!/usr/bin/env bash
set -e

# Configuration
REPO="ezhil-003/qr-excel"
BIN_NAME="qr-excel"
INSTALL_DIR="/usr/local/bin"

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS_STR=linux;;
    Darwin*)    OS_STR=macos;;
    *)          echo "Unsupported OS: ${OS}" && exit 1;;
esac

# Detect Architecture
ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64)   ARCH_STR=amd64;;
    arm64)    ARCH_STR=universal;; # For macOS universal binary
    aarch64)  ARCH_STR=amd64;; # Provide fallback if arm64 linux isn't built yet, but we only built amd64 for linux
    *)        echo "Unsupported Architecture: ${ARCH}" && exit 1;;
esac

if [ "$OS_STR" = "macos" ]; then
    ASSET_NAME="${BIN_NAME}-macos-universal"
else
    ASSET_NAME="${BIN_NAME}-linux-amd64"
fi

echo "Fetching latest release information for $REPO..."
API_URL="https://api.github.com/repos/${REPO}/releases/latest"
LATEST_RELEASE=$(curl -sL $API_URL)
VERSION=$(echo "$LATEST_RELEASE" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$VERSION" ]; then
    echo "Error: Could not retrieve latest release from GitHub."
    exit 1
fi

echo "Latest release: $VERSION"
DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${VERSION}/${ASSET_NAME}"

echo "Downloading $ASSET_NAME from $DOWNLOAD_URL..."

# Create a temporary directory
TMP_DIR=$(mktemp -d)
trap 'rm -rf -- "$TMP_DIR"' EXIT

curl -sL "$DOWNLOAD_URL" -o "${TMP_DIR}/${BIN_NAME}"
chmod +x "${TMP_DIR}/${BIN_NAME}"

# Attempt to install to /usr/local/bin
echo "Installing to $INSTALL_DIR (may require sudo)..."
if [ -w "$INSTALL_DIR" ]; then
    mv "${TMP_DIR}/${BIN_NAME}" "$INSTALL_DIR"
else
    sudo mv "${TMP_DIR}/${BIN_NAME}" "$INSTALL_DIR"
fi

# Ship assets to runtime directory
ASSETS_DIR="$HOME/.qr-excel/assets"
echo "Shipping assets to $ASSETS_DIR..."
mkdir -p "$ASSETS_DIR"
curl -sL "https://raw.githubusercontent.com/${REPO}/main/qr_excel/assets/upi_logo.png" -o "${ASSETS_DIR}/upi_logo.png"
curl -sL "https://raw.githubusercontent.com/${REPO}/main/qr_excel/assets/upi_qr_template.db" -o "${ASSETS_DIR}/upi_qr_template.db"

echo "Successfully installed ${BIN_NAME}!"
echo "Run '${BIN_NAME} --help' to get started."
