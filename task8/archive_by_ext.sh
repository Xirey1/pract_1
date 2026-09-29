#!/bin/bash

dir="${1:-.}"
ext="$2"
out="${3:-archive.tar}"

if [ -z "$ext" ]; then
    echo "Использование: $0 <каталог> <расширение> [выходной.tar]"
    exit 1
fi

find "$dir" -type f -name "*.$ext" -print0 | tar --null -cvf "$out" -T -

echo "Архив '$out' создан"
