# Практика 1
```bash
## Задача 1.

grep -o '^[^:]*' /etc/passwd | sort

## Задача 2.

awk '$2 ~ /^[0-9]+$/ {print $2, $1}' /etc/protocols | sort -rn | head -5

## Задача 3.

#!/bin/bash
text="$1"
len=${#text}
line=$(printf '%*s' "$((len + 2))" '' | tr ' ' '-')

echo "+${line}+"
echo "| ${text} |"
echo "+${line}+"

## Задача 4.

#!/bin/bash
if [ -z "$1" ]; then
    echo "Использование: $0 <файл>"
    exit 1
fi

grep -oE '[A-Za-z_][A-Za-z0-9_]*' "$1" | sort -u

## Задача 5.

#!/bin/bash
sudo cp "$1" /usr/local/bin/"$1"
sudo chmod 755 /usr/local/bin/"$1"

## Задача 6.

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

## Задача 7.

#!/bin/bash
dir="${1:-.}"

find "$dir" -type f -exec md5sum {} + \
    | sort \
    | awk '
        {
            hash=$1; $1=""; sub(/^ /,""); file=$0
            if (hash == prev) {
                if (!printed) { print prev_file; printed = 1 }
                print file
            } else { printed = 0 }
            prev = hash; prev_file = file
        }'

## Задача 8.

#!/bin/bash
dir="${1:-.}"
ext="$2"
out="${3:-archive.tar}"

if [ -z "$ext" ]; then
    echo "Использование: $0 <каталог> <расширение> [выходной.tar]"
    exit 1
fi

find "$dir" -type f -name "*.$ext" -print0 | tar --null -cvf "$out" -T -

## Задача 9.

#!/bin/bash
sed 's/    /\t/g' "$1" > "$2"

## Задача 10.

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
```
