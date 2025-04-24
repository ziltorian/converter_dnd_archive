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
header_pattern = re.compile(r"^(#{1,10})\s*(.+?):\s*$")          # Заголовки ###–######
pair_pattern = re.compile(r"^\s*-\s*([^:]+):\s*(.*)$")          # Ключ: значение
list_pattern = re.compile(r"^\s*-\s*(?!.*:)(.+)$")              # Элемент списка

# --- Разбор структурированного текста секции ---
def parse_structured_text(text: str) -> Dict[str, Any]:
    lines = text.strip().splitlines()
    root: Dict[str, Any] = {}
    stack: List[Dict[str, Any]] = [root]
    levels: List[int] = [0]  # Корень имеет уровень 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        header_match = re.match(r"^(#{1,10})\s*(.+?):\s*$", line)
        pair_match = re.match(r"^\s*-\s*([^:]+):\s*(.*)$", line)
        list_match = re.match(r"^\s*-\s*(?!.*:)(.+)$", line)

        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            # Закрываем уровни до нужного
            while levels and levels[-1] >= level:
                stack.pop()
                levels.pop()

            parent = stack[-1]
            parent[title] = {}
            stack.append(parent[title])
            levels.append(level)
            continue

        # Ключ: значение
        if pair_match:
            key = pair_match.group(1).strip()
            value = pair_match.group(2).strip()
            stack[-1][key] = value
            continue

        # Элемент списка
        if list_match:
            item = list_match.group(1).strip()
            current = stack[-1]

            # если блок содержит только один пустой ключ — преобразовать его в список
            if (
                len(current) == 1
                and list(current.values())[0] == ""
                and "_list" not in current
            ):
                key = list(current.keys())[0]
                current[key] = [item]
            elif (
                len(current) == 1
                and isinstance(list(current.values())[0], list)
            ):
                key = list(current.keys())[0]
                current[key].append(item)
            else:
                if "_list" not in current:
                    current["_list"] = []
                current["_list"].append(item)

    return root

def simplify_structure(data: Any) -> Any:
    """
    Рекурсивно упрощает вложенные блоки вида {"_list": [...]} → [...]
    """
    if isinstance(data, dict):
        # Если словарь содержит только _list — заменить на сам список
        if set(data.keys()) == {"_list"}:
            return simplify_structure(data["_list"])

        # Рекурсивно применить ко всем значениям
        return {k: simplify_structure(v) for k, v in data.items()}

    elif isinstance(data, list):
        return [simplify_structure(item) for item in data]

    return data


# --- Разделение на секции по "---" и разбор каждой ---
def parse_character_file(text: str) -> Dict[str, Any]:
    sections = re.split(r"^---+\s*$", text, flags=re.MULTILINE)
    parsed: Dict[str, Any] = {}
    for section in sections:
        structured = parse_structured_text(section)
        parsed.update(structured)
    return parsed

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
