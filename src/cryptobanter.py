#!/usr/bin/env python
"""
Display Crypto Banter ASCII art.
This can be run as a standalone script.
"""

import sys

# ANSI color codes
RED = "\033[31m"
WHITE = "\033[37m"
RESET = "\033[0m"

# 8-bit style pixel art for "cryptobanter"
crypto_banter = [
    RED + "█▀▀ █▀█ █▄█ █▀█ ▀█▀ █▀█" + WHITE + "   █▀▄ █▀█ █▄ █ ▀█▀ █▀▀ █▀█" + RESET,
    RED + "█   █▀▄  █  █▀▀  █  █ █" + WHITE + "   █▀▄ █▀█ █ ▀█  █  █▀▀ █▀▄" + RESET,
    RED + "▀▀▀ ▀ ▀  ▀  ▀    ▀  ▀▀▀" + WHITE + "   ▀▀  ▀ ▀ ▀  ▀  ▀  ▀▀▀ ▀ ▀" + RESET
]

def print_crypto_banter():
    print("\n")
    for line in crypto_banter:
        print("  " + line)
    print("\n")

if __name__ == "__main__":
    print_crypto_banter() 