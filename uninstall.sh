#!/bin/bash

INSTALL_PATH="$HOME/.config/linux-desktop-gremlin"

PICKER_LINK_PATH="$HOME/.local/bin/gremlin-picker"
PICKER_DESKTOP_FILE="$HOME/.local/share/applications/gremlin_picker.desktop"

DOWNLOADER_LINK_PATH="$HOME/.local/bin/gremlin-downloader"
DOWNLOADER_DESKTOP_FILE="$HOME/.local/share/applications/gremlin_downloader.desktop"


if [ -d "$INSTALL_PATH" ]; then
    rm -rf "$INSTALL_PATH"
    echo "Removed directory: $INSTALL_PATH"
fi

if [ -L "$PICKER_LINK_PATH" ]; then
    rm "$PICKER_LINK_PATH"
    echo "Removed symlink: $PICKER_LINK_PATH"
fi

if [ -f "$PICKER_DESKTOP_FILE" ]; then
    rm "$PICKER_DESKTOP_FILE"
    echo "Removed desktop entry: $PICKER_DESKTOP_FILE"
fi

if [ -L "$DOWNLOADER_LINK_PATH" ]; then
    rm "$DOWNLOADER_LINK_PATH"
    echo "Removed symlink: $DOWNLOADER_LINK_PATH"
fi

if [ -f "$DOWNLOADER_DESKTOP_FILE" ]; then
    rm "$DOWNLOADER_DESKTOP_FILE"
    echo "Removed desktop entry: $DOWNLOADER_DESKTOP_FILE"
fi
