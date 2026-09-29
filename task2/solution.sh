awk '$2 ~ /^[0-9]+$/ {print $2, $1}' /etc/protocols | sort -rn | head -5
