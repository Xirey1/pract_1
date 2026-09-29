#!/bin/bash

if [ -z "$1" ]; then
    echo "Использование: $0 <файл>"
    exit 1
fi

grep -oE '[A-Za-z_][A-Za-z0-9_]*' "$1" | sort -u
