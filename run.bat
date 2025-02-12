@echo off
echo Running commands...
pyinstaller --onefile main.py
pyinstaller --noconsole --onefile --add-binary "unblockneteasemusic-win-x64.exe;." musicLauncher.py

echo Done.
pause
