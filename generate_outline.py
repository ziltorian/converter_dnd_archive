import json
import yaml
import os
from typing import Dict, Any


# === CONFIG ===
CONFIG = {
    "input_path": "./result/Дополнение Осколки забытого мира.json",
    "json_output_path": "./result/Дополнение Осколки забытого мира_с_оглавлением.json",
    "yaml_output_path": "./result/Дополнение Осколки забытого мира_оглавление.yaml",
    "max_depth": 3,  # <<<<<<<<<<<<<<<<<<<<<<<<<<< ЗДЕСЬ менять глубину оглавления
                     # 2 — включает только ## и ниже
                     # 3 — включает до ###
                     # 4 — до #### и т.д.
    "outline_key": "Оглавление"
}


def load_json_file(path: str) -> Dict[str, Any]:
    """Загрузить JSON-файл и вернуть его как словарь."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], path: str) -> None:
    """Сохранить словарь как JSON-файл."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_yaml_file(data: Dict[str, Any], path: str) -> None:
    """Сохранить словарь как YAML-файл."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


def generate_outline(data: Dict[str, Any], depth: int = 1, max_depth: int = 4) -> Dict[str, Any]:
    """
    Рекурсивно пройтись по словарю и построить оглавление.
    Включает ключи-словари и ключи-списки, игнорирует служебные (_list, _text).
    :param data: исходный JSON-словарь
    :param depth: текущая глубина обхода
    :param max_depth: максимальная глубина для включения в оглавление
    :return: словарь-оглавление
    """
    if depth > max_depth or not isinstance(data, dict):
        return {}

    result: Dict[str, Any] = {}
    for key, value in data.items():
        if key in ("_text", "_list"):
            continue
        if isinstance(value, dict):
            nested = generate_outline(value, depth + 1, max_depth)
            result[key] = nested if nested else {}
        elif isinstance(value, list):
            result[key] = {}  # добавим заголовок, но не заглядываем внутрь списка
    return result


def insert_outline(original: Dict[str, Any], outline: Dict[str, Any], outline_key: str = "оглавление") -> Dict[str, Any]:
    """
    Вставить оглавление внутрь копии JSON, на верхнем уровне под заданным ключом.
    :param original: исходный JSON
    :param outline: словарь-оглавление
    :param outline_key: ключ для вставки
    :return: обновлённый JSON
    """
    result: Dict[str, Any] = {outline_key: outline}
    result.update(original)
    return result


def main() -> None:
    if not os.path.exists(CONFIG["input_path"]):
        print(f"❌ Файл не найден: {CONFIG['input_path']}")
        return

    print(f"Загрузка: {CONFIG['input_path']}")
    data = load_json_file(CONFIG["input_path"])

    print("Генерация оглавления...")
    outline_body = generate_outline(data, depth=1, max_depth=CONFIG["max_depth"])
    top_level_key = next(iter(data))  # Первый ключ — как основной заголовок
    outline = {top_level_key: outline_body.get(top_level_key, {})}

    print("Встраивание оглавления в JSON...")
    data_with_outline = insert_outline(data, outline, CONFIG["outline_key"])
    save_json_file(data_with_outline, CONFIG["json_output_path"])

    print("Сохранение YAML...")
    save_yaml_file({CONFIG["outline_key"]: outline}, CONFIG["yaml_output_path"])

    print("✅ Готово!")
    print(f"→ JSON с оглавлением: {CONFIG['json_output_path']}")
    print(f"→ YAML оглавление: {CONFIG['yaml_output_path']}")


if __name__ == "__main__":
    main()
