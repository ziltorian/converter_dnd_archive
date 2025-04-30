import os
import json
import re
from typing import Any, Dict, List

# Загружаем конфигурацию
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

input_dir = config.get("input_characters", "characters")
output_dir = config.get("output_folder", "result")

# --- Регулярные выражения для разбора строк ---
header_pattern = re.compile(r"^(#{1,10})\s*(.+?)(:)?\s*$")  # Заголовки ###–######
pair_pattern = re.compile(r"^\s*(?:[-—])?\s*([^\s][^:]{0,50}):(?:\s+(.*))?$")
# pair_pattern = re.compile(r"^\s*-?\s*([^:]+):\s*(.*)$")  # Ключ: значение
list_pattern = re.compile(r"^\s*[-–—]\s*(?!.*:)(.+)$")  # Элемент списка


# --- Разбор структурированного текста секции ---
def parse_structured_text(text: str) -> Dict[str, Any]:
    lines = text.strip().splitlines()
    root: Dict[str, Any] = {}
    stack: List[Dict[str, Any]] = [root]
    levels: List[int] = [0]

    current_key_for_list = None  # <- добавлено

    for line in lines:
        line = line.strip()
        if not line:
            continue

        header_match = header_pattern.match(line)
        pair_match = pair_pattern.match(line)
        list_match = list_pattern.match(line)

        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            while levels and levels[-1] >= level:
                stack.pop()
                levels.pop()
            parent = stack[-1]
            parent[title] = {}
            stack.append(parent[title])
            levels.append(level)
            current_key_for_list = None
            continue

        if pair_match:
            key = pair_match.group(1).strip()
            value = pair_match.group(2).strip() if pair_match.group(2) else ""

            if value:
                stack[-1][key] = value
                current_key_for_list = None
            else:
                stack[-1][key] = []
                current_key_for_list = key
            continue

        if list_match:
            item = list_match.group(1).strip()
            if current_key_for_list:
                stack[-1][current_key_for_list].append(item)
            else:
                if "_list" not in stack[-1]:
                    stack[-1]["_list"] = []
                stack[-1]["_list"].append(item)
            continue

        # если это просто обычный абзац (не пара, не список, не заголовок)
        if line and not line.startswith("-") and not header_match:
            current = stack[-1]

            # если ключ недавно открыт, но его значение — строка, преврати в список
            if isinstance(current, dict):
                if "_text" not in current:
                    current["_text"] = []
                current["_text"].append(line)

    return root


def simplify_structure(data: Any) -> Any:
    """
    Рекурсивно упрощает вложенные блоки вида {"_list": [...]} → [...]
    """
    if isinstance(data, dict):
        # Если словарь содержит только _list — заменить на сам список
        if set(data.keys()) == {"_list"}:
            return simplify_structure(data["_list"])
        if set(data.keys()) == {"_text"}:
            return simplify_structure(data["_text"])

        # Рекурсивно применить ко всем значениям
        return {k: simplify_structure(v) for k, v in data.items()}

    elif isinstance(data, list):
        return [simplify_structure(item) for item in data]

    return data


# --- Разделение на секции по "---" и разбор каждой ---
def parse_character_file(text: str) -> Dict[str, Any]:
    has_top_level_header = re.search(r"^#\s*(.+)", text, flags=re.MULTILINE)

    if has_top_level_header:
        root_title = has_top_level_header.group(1).strip()
        body = re.sub(r"^#\s*.+", "", text, count=1, flags=re.MULTILINE)
        sections = re.split(r"^---+\s*$", body, flags=re.MULTILINE)
        container = {}

        for section in sections:
            structured = parse_structured_text(section)
            if len(structured) == 1:
                key = list(structured.keys())[0]
                container[key] = structured[key]
            else:
                container.update(structured)

        return {root_title: simplify_structure(container)}

    else:
        sections = re.split(r"^---+\s*$", text, flags=re.MULTILINE)
        parsed: Dict[str, Any] = {}
        for section in sections:
            structured = parse_structured_text(section)
            if len(structured) == 1:
                key = list(structured.keys())[0]
                parsed[key] = structured[key]
            else:
                parsed.update(structured)

        return simplify_structure(parsed)


# --- Основной обработчик файлов ---
def process_files():
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[Создана папка]: {output_dir}")

    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename.replace(".txt", ".json"))

            print(f"[Обработка файла]: {filename}")

            with open(input_path, "r", encoding="utf-8") as file:
                content = file.read()

            structured = parse_character_file(content)
            structured = simplify_structure(structured)

            with open(output_path, "w", encoding="utf-8") as out:
                json.dump(structured, out, ensure_ascii=False, indent=2)

            print(f"[Сохранён]: {output_path}")


# --- Запуск ---
if __name__ == "__main__":
    print(f"[Старт] Чтение из: {input_dir}  Сохранение в: {output_dir}")
    process_files()
