import os
import json
import re
from typing import Any, Dict, List

# Загружаем конфигурацию
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

input_dir: str = config.get("input_characters", "characters")
output_dir: str = config.get("output_folder", "result")

# --- Регулярные выражения для разбора строк ---
header_pattern = re.compile(r"^(#{1,10})\s*(.+?)(:)?\s*$")  # Заголовки #–##########
# Пары ключ: значение — только если ключ до 50 символов, без скобок
pair_pattern = re.compile(
    r"""^
    \s*
    (?:[-–—])?         # возможное тире
    \s*
    ([^:]{1,50}?)  # ключ без скобок и двоеточий, до 50 символов
    :
    \s*
    (.*)?              # значение (необязательно)
    $
    """, re.VERBOSE
)
# pair_pattern = re.compile(r"^\s*(?:[-–—])?\s*([^\s][^:]{0,50}):(?:\s+(.*))?$")  # Ключ: значение
# Элемент списка — начинается с любого тире
list_pattern = re.compile(r"^\s*[-–—]\s*(.+)$")


# Улучшенная версия функции parse_structured_text с более точной логикой:
# 1. Сохраняет строки начинающиеся с тире как элементы списка, даже если они содержат ":"
#    (если не распознаны как пара по pair_pattern).
# 2. Строки с ключами длиной > 50 символов больше не распознаются как пары.

# Обновлённая логика: каждый новый ключ сбрасывает флаг привязки, текст — обнуляет

def parse_structured_text(text: str) -> Dict[str, Any]:
    """
    Разбирает markdown-подобный текст в структуру данных.

    - Заголовки → вложенные блоки
    - Ключ без значения → ожидает список
    - Ключ: значение (если ключ короткий) → пара
    - Всё остальное → _text или _list
    """
    lines = text.strip().splitlines()
    root: Dict[str, Any] = {}
    stack: List[Dict[str, Any]] = [root]
    levels: List[int] = [0]

    current_key_for_list: str | None = None
    list_binding_active = False  # Активна ли привязка к предыдущему ключу

    for line in lines:
        line = line.strip()
        if not line:
            continue

        header_match = header_pattern.match(line)
        list_match = list_pattern.match(line)
        pair_match = pair_pattern.match(line)

        # --- Заголовок ---
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
            list_binding_active = False
            continue

        # --- Ключ: значение ---
        if pair_match:
            key = pair_match.group(1).strip()
            value = pair_match.group(2).strip() if pair_match.group(2) else ""

            if len(key) > 50:
                # длинный ключ → не пара, а текст
                stack[-1].setdefault("_text", []).append(line)
                current_key_for_list = None
                list_binding_active = False
                continue

            if value:
                stack[-1][key] = value
                current_key_for_list = None
                list_binding_active = False
            else:
                stack[-1][key] = []
                current_key_for_list = key
                list_binding_active = True
            continue

        # --- Список ---
        if list_match:
            item = list_match.group(1).strip()

            # Если item формально выглядит как пара, но ключ слишком длинный → оставить как список
            if pair_pattern.match(line):
                key_candidate = pair_pattern.match(line).group(1)
                if len(key_candidate) > 50:
                    item = line.lstrip("-–—").strip()
                else:
                    # это настоящая пара
                    key = key_candidate.strip()
                    value = pair_pattern.match(line).group(2) or ""
                    stack[-1][key] = value.strip()
                    current_key_for_list = None
                    list_binding_active = False
                    continue

            if current_key_for_list and list_binding_active:
                stack[-1][current_key_for_list].append(item)
            else:
                stack[-1].setdefault("_list", []).append(item)
            continue

        # --- Абзац ---
        stack[-1].setdefault("_text", []).append(line)
        current_key_for_list = None
        list_binding_active = False

    return root


def simplify_structure(data: Any) -> Any:
    """
    Рекурсивно упрощает структуру:
    - {"_list": [...]} → [...]
    - {"_text": [...]} → [...]

    Args:
        data: Любая вложенная структура данных (dict / list / str).

    Returns:
        Упрощённая структура с убранными обёртками _list и _text, если они единственные.
    """
    if isinstance(data, dict):
        if set(data.keys()) == {"_list"}:
            return simplify_structure(data["_list"])
        if set(data.keys()) == {"_text"}:
            return simplify_structure(data["_text"])
        return {k: simplify_structure(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [simplify_structure(item) for item in data]
    return data


def parse_character_file(text: str) -> Dict[str, Any]:
    """
    Делит входной файл на секции по `---` и применяет разбор к каждой из них.
    Если в тексте найден заголовок первого уровня (`#`), он считается корневым.

    Args:
        text: Полный текст файла персонажа.

    Returns:
        Вложенный словарь, представляющий JSON-структуру персонажа.
    """
    has_top_level_header = re.search(r"^#[^#]\s*(.+)", text, flags=re.MULTILINE)

    if has_top_level_header:
        root_title = has_top_level_header.group(1).strip()
        body = re.sub(r"^#\s*.+", "", text, count=1, flags=re.MULTILINE)
        sections = re.split(r"^---+\s*$", body, flags=re.MULTILINE)
        container: Dict[str, Any] = {}

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


def process_files() -> None:
    """
    Обрабатывает все файлы в папке `input_dir`, конвертирует их в JSON и сохраняет в `output_dir`.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[Создана папка]: {output_dir}")

    for filename in os.listdir(input_dir):
        if filename.endswith((".txt", ".md")):
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(output_dir, output_filename)

            print(f"[Обработка файла]: {filename}")

            with open(input_path, "r", encoding="utf-8") as file:
                content = file.read()

            structured = parse_character_file(content)
            structured = simplify_structure(structured)

            with open(output_path, "w", encoding="utf-8") as out:
                json.dump(structured, out, ensure_ascii=False, indent=2)

            print(f"[Сохранён]: {output_path}")


if __name__ == "__main__":
    print(f"[Старт] Чтение из: {input_dir}  Сохранение в: {output_dir}")
    process_files()
