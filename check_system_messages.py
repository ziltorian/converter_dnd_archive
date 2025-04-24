# ✅ Обновлённый check_system_messages.py
# Анализирует только файлы из папки archive (исходники)
# Ищет системные сообщения (например, от ChatGPT)
# Выводит в консоль найденные фразы, если они есть

import os
import re
import json
from bs4 import BeautifulSoup

CONFIG_PATH = "config.json"

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_archive_files(input_folder):
    return sorted([
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.lower().endswith((".html", ".txt"))
    ])

def extract_system_messages_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    system_blocks = []

    # Предположим, системные сообщения могут быть в блоках pre.message без автора
    for pre in soup.select("pre.message"):
        if not pre.find("div", class_="author"):
            text = pre.get_text().strip()
            if any(x in text.lower() for x in ["please remember", "system message", "this content", "was generated"]):
                system_blocks.append(text[:300])  # первые 300 символов

    return system_blocks

def check_all_archives_for_system_blocks(config):
    input_folder = config.get("input_folder", "archive")
    full_path = os.path.join(os.getcwd(), input_folder)

    all_files = get_archive_files(full_path)
    found_any = False

    for filepath in all_files:
        system_blocks = extract_system_messages_from_file(filepath)
        if system_blocks:
            print(f"\n⚠Системные сообщения в файле: {os.path.basename(filepath)}")
            for msg in system_blocks:
                print(f"---\n{msg}\n---")
            found_any = True

    if not found_any:
        print("Ни одного системного сообщения не найдено.")

if __name__ == "__main__":
    config = load_config(CONFIG_PATH)
    check_all_archives_for_system_blocks(config)

