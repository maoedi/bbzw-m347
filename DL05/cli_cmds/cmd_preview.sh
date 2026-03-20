#!/usr/bin/env bash

cmd_preview() {
    local LIGHT_BLUE="\033[1;36m"
    local RESET="\033[0m"

    echo
    echo -e "${LIGHT_BLUE}$*${RESET}"
    read -p ""
}