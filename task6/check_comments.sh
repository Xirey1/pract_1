#!/bin/bash

dir="${1:-.}"

find "$dir" -type f \( -name '*.c' -o -name '*.js' -o -name '*.py' \) | while read -r f; do
    first=$(head -n 1 "$f" | sed 's/^[[:space:]]*//')

    case "$f" in
        *.c|*.js) pat='^(//|/\*)' ;;
        *.py)     pat='^#' ;;
    esac

    if echo "$first" | grep -qE "$pat"; then
        echo "$f: комментарий есть"
    else
        echo "$f: комментария нет"
    fi
done
