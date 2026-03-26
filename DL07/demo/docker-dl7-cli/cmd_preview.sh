#!/usr/bin/env bash

cmd_preview() {
    local LIGHT_BLUE="\033[1;36m"
    local YELLOW="\033[1;33m"
    local RESET="\033[0m"

    echo
    echo -e "${LIGHT_BLUE}$*${RESET}"
    read -p "$(echo -e "${YELLOW}ENTER = weiter${RESET}")"
}

step() {
    local GREEN="\033[1;32m"
    local RESET="\033[0m"
    echo
    echo -e "${GREEN}==> $*${RESET}"
}

note() {
    local YELLOW="\033[1;33m"
    local RESET="\033[0m"
    echo -e "${YELLOW}$*${RESET}"
}

hr() {
    echo
    printf '%*s\n' "${COLUMNS:-72}" '' | tr ' ' -
    echo
}
