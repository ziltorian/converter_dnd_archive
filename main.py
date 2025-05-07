import os
import subprocess
import sys

# Установить кодировку UTF-8 для Windows-консоли
if os.name == 'nt':
    os.system("chcp 65001 > nul")

# Список скриптов для запуска
scripts_to_run = [
    "combined_archive.py",
    "check_system_messages.py",
    "converter_characters.py",
    "generate_outline.py"
]

print("\nЗапуск скриптов обработки архива:\n")

for script in scripts_to_run:
    print(f"Запуск: {script}")
    try:
        result = subprocess.run(
            ["python", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Ошибка:\n{result.stderr}")
    except Exception as e:
        print(f"Не удалось запустить {script}: {e}")

print("\nВсе этапы завершены.")
