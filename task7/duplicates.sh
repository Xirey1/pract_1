#!/bin/bash

dir="${1:-.}"

find "$dir" -type f -exec md5sum {} + \
    | sort \
    | awk '
        {
            hash=$1
            $1=""
            sub(/^ /, "")
            file=$0

            if (hash == prev) {
                if (!printed) {
                    print prev_file
                    printed = 1
                }
                print file
            } else {
                printed = 0
            }

            prev = hash
            prev_file = file
        }'
