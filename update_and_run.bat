@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo 🔄 Проверка обновлений с GitHub...
git pull https://github.com/ziltorian/converter_dnd_archive main

echo 📦 Установка/обновление зависимостей...
pip install -r requirements.txt

echo 🚀 Запуск основного скрипта...
python main.py

echo 🟢 Завершено. Нажмите любую клавишу для выхода.
pause >nul
