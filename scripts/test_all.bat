@echo off
setlocal
cd /d "%~dp0.."
echo === Stage 2 - configuration ===
python main.py --vfs demos\demo_vfs.zip --script demos\stage2_ok.vfs --batch
if errorlevel 1 exit /b 1
echo === Stage 3 - minimal and nested ZIP ===
python main.py --vfs demos\minimal_vfs.zip --script demos\stage3_minimal.vfs --batch
if errorlevel 1 exit /b 1
python main.py --vfs demos\nested_vfs.zip --script demos\stage3_nested.vfs --batch
if errorlevel 1 exit /b 1
echo === Stage 4 - commands ===
python main.py --vfs demos\demo_vfs.zip --script demos\stage4_success.vfs --batch
if errorlevel 1 exit /b 1
echo === Stage 5 - in-memory rm ===
python main.py --vfs demos\demo_vfs.zip --script demos\stage5_success.vfs --batch
if errorlevel 1 exit /b 1
echo === Expected failures ===
python main.py --vfs demos\invalid_vfs.zip --script demos\stage4_success.vfs --batch
if not errorlevel 1 exit /b 1
python main.py --vfs demos\demo_vfs.zip --script demos\stage4_error.vfs --batch
if not errorlevel 1 exit /b 1
python main.py --vfs demos\demo_vfs.zip --script demos\stage5_error.vfs --batch
if not errorlevel 1 exit /b 1
echo === Automated tests ===
python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
echo All tests passed.
endlocal
