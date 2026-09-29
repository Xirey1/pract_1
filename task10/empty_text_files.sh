#!/bin/bash

dir="${1:-.}"

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не является директорией"
    exit 1
fi

find "$dir" -type f -empty | while read -r f; do
    if file --mime "$f" | grep -qE 'text/|inode/x-empty'; then
        echo "$f"
    fi
done
