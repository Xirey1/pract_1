#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
echo '=== Этап 2. Параметры ==='
"$PYTHON" main.py --vfs demos/demo_vfs.zip --script demos/stage2_ok.vfs --batch
echo '=== Этап 3. Три варианта ZIP ==='
"$PYTHON" main.py --vfs demos/minimal_vfs.zip --script demos/stage3_minimal.vfs --batch
"$PYTHON" main.py --vfs demos/nested_vfs.zip --script demos/stage3_nested.vfs --batch
echo '=== Этап 4. Команды ==='
"$PYTHON" main.py --vfs demos/demo_vfs.zip --script demos/stage4_success.vfs --batch
echo '=== Этап 5. rm ==='
"$PYTHON" main.py --vfs demos/demo_vfs.zip --script demos/stage5_success.vfs --batch
echo '=== Ожидаемые ошибки (неуспешный код возврата) ==='
if "$PYTHON" main.py --vfs demos/invalid_vfs.zip --script demos/stage4_success.vfs --batch; then
  echo 'ОШИБКА: некорректный ZIP не был отклонён' >&2; exit 1
fi
if "$PYTHON" main.py --vfs demos/demo_vfs.zip --script demos/stage4_error.vfs --batch; then
  echo 'ОШИБКА: скрипт продолжился после ошибки' >&2; exit 1
fi
if "$PYTHON" main.py --vfs demos/demo_vfs.zip --script demos/stage5_error.vfs --batch; then
  echo 'ОШИБКА: rm удалил каталог без -r' >&2; exit 1
fi
echo '=== Автоматические тесты ==='
"$PYTHON" -m unittest discover -s tests -v
echo 'Все проверки пройдены.'
