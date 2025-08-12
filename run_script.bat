@echo off
cd /d "C:\Users\zande\OneDrive\Documents\News alerts DOC OPA"
"venv\Scripts\python.exe" "main.py" >> "task_log.txt" 2>&1
echo Task completed at %date% %time% >> "task_log.txt"