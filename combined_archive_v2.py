# ✅ Итоговая версия combined_archive_v2.py — с поддержкой:
# - конфигурации через config.json
# - выделенных master/players ключей и типов
# - оглавления только по сценам мастера
# - сохранения объединённого архива + отдельных глав

import os
import re
import json
from bs4 import BeautifulSoup


# Загрузка конфигурации
def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Получение всех путей и настроек из конфигурации
def get_paths_and_keys_from_config(config):
    input_dir = config.get("input_folder", "archive")
    output_dir = config.get("output_folder", "result")
    output_file = config.get("output_filename_v2", "archive_sessions_v2.json")
    meta = config.get("metadata_sessions_v2", {})

    key_master = config.get("key_master", "Мастер подземелий")
    key_players = config.get("key_players", "Действия игроков")
    type_master = config.get("master_type", "master")
    type_players = config.get("players_type", "players")

    return {
        "input_dir": os.path.join(os.getcwd(), input_dir),
        "output_dir": os.path.join(os.getcwd(), output_dir),
        "output_file": os.path.join(os.getcwd(), output_dir, output_file),
        "meta": meta,
        "key_master": key_master,
        "key_players": key_players,
        "type_master": type_master,
        "type_players": type_players
    }


# Унификация названия автора по конфигу
def normalize_key(key, config):
    key_clean = re.sub(r'#*', '', key).strip(': \t\n')
    return config.get(key_clean.strip(), key_clean)


# Очистка лишних символов
def clean_text(text):
    text = re.sub(r'-{3,}', '', text)
    text = re.sub(r'#*', '', text)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = re.sub(r'[ \t]+', ' ', line).strip()
        if not line:
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)


# Парсинг одной главы
def extract_scenes(filepath, config, start_id, chapter_id, key_master, key_players, type_master, type_players):
    with open(filepath, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")
    h4 = soup.find("h4")
    chapter_title = h4.get_text(strip=True) if h4 else os.path.splitext(os.path.basename(filepath))[0]

    conversations = soup.select("div.conversation")
    scenes = []
    scene_ids = []

    for convo in conversations:
        pre_blocks = convo.find_all("pre", class_="message")
        for block in pre_blocks:
            author = block.find("div", class_="author")
            text = block.get_text().strip()
            if author:
                raw_key = author.get_text()
                normalized_key = normalize_key(raw_key, config)
                content = clean_text(text.replace(raw_key, "").strip())

                if normalized_key == key_master:
                    if "сцена" in content.lower():
                        match = re.search(r"(СЦЕНА: ?.+)", content, flags=re.IGNORECASE)
                        scene_title = match.group(1).strip() if match else "СЦЕНА: (без названия)"
                    else:
                        scene_title = "СЦЕНА: (без названия)"

                    scene = {
                        "id": start_id,
                        "type": type_master,
                        "chapter": chapter_id,
                        "title": scene_title,
                        "content": content,
                        "tags": ["scene"]
                    }
                    # Удаление дублирующего заголовка из content
                    if scene.get("title") and isinstance(scene["title"], str):
                        title_clean = scene["title"].strip().replace("СЦЕНА:", "").strip("* ").strip()
                        pattern = rf"^\s*СЦЕНА:\s*\*{{0,2}}{re.escape(title_clean)}\*{{0,2}}\s*\n?"
                        scene["content"] = re.sub(pattern, "", scene["content"], count=1, flags=re.IGNORECASE)

                    scenes.append(scene)
                    scene_ids.append(start_id)
                    start_id += 1

                elif normalized_key == key_players:
                    scene = {
                        "id": start_id,
                        "type": type_players,
                        "chapter": chapter_id,
                        "title": None,
                        "content": content,
                        "tags": []
                    }
                    # Удаление дублирующего заголовка из content
                    if scene.get("title") and isinstance(scene["title"], str):
                        title_clean = scene["title"].strip().replace("СЦЕНА:", "").strip("* ").strip()
                        pattern = rf"^\s*СЦЕНА:\s*\*{{0,2}}{re.escape(title_clean)}\*{{0,2}}\s*\n?"
                        scene["content"] = re.sub(pattern, "", scene["content"], count=1, flags=re.IGNORECASE)

                    scenes.append(scene)
                    scene_ids.append(start_id)
                    start_id += 1

    return chapter_title, scenes, scene_ids, start_id


# Сохранение отдельного архива по главе
def save_chapter_json(output_dir, chapter_title, scenes, outline, index, meta, suffix=""):
    safe_title = re.sub(r"[^\w\d\-_ ]", "", chapter_title).replace(" ", "_")
    filename = f"{safe_title}{suffix}.json"
    path = os.path.join(output_dir, filename)

    archive_data = {
        "_meta": meta,
        "outline": outline,
        "archive": scenes,
        "index": index
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(archive_data, f, ensure_ascii=False, indent=2)
    print(f"Сохранён файл главы: {filename}")


# Сборка полного архива
def build_archive_from_folder(folder_path, config, key_master, key_players, type_master, type_players, output_dir,
                              meta):
    files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".html", ".txt"))
    ])

    prequels = [f for f in files if f.lower().startswith("ваншот - приквел")]
    main_chapters = [f for f in files if f not in prequels]
    files_ordered = prequels + main_chapters

    archive = []
    outline = []
    index = {}
    current_id = 1
    chapter_num = 1

    for file in files_ordered:
        filepath = os.path.join(folder_path, file)
        chapter_title, scenes, scene_ids, current_id = extract_scenes(
            filepath, config, current_id, chapter_num,
            key_master, key_players, type_master, type_players
        )

        archive.extend(scenes)
        for s in scenes:
            index[str(s["id"])] = len(archive) - len(scenes) + scenes.index(s)

        master_ids = [s["id"] for s in scenes if s["type"] == type_master]
        if master_ids:
            scene_range = f"от {master_ids[0]} до {master_ids[-1]}"
        else:
            scene_range = "Список сцен: —"

        outline_type = "Приквел" if file.lower().startswith("ваншот - приквел") else "Глава"
        title_clean = re.sub(r"^(Глава\s*\d+|Ваншот\s*-\s*Приквел):?\s*", "", chapter_title).strip()

        local_outline = [{
            "chapter": chapter_num,
            "type": outline_type,
            "title": title_clean,
            "scenes": scene_range
        }]

        # Отдельный файл по главе
        chapter_index = {str(s["id"]): idx for idx, s in enumerate(scenes)}
        save_chapter_json(output_dir, chapter_title, scenes, local_outline, chapter_index, meta)

        outline.append(local_outline[0])
        chapter_num += 1

    return archive, outline, index


# Сохранение основного архива
def save_json_archive(output_path, meta, outline, archive, index):
    archive_data = {
        "_meta": meta,
        "outline": outline,
        "archive": archive,
        "index": index
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(archive_data, f, ensure_ascii=False, indent=2)
    print(f"Сохранён объединённый архив: {output_path}")


# Главная функция
if __name__ == "__main__":
    config = load_config("config.json")
    paths = get_paths_and_keys_from_config(config)

    os.makedirs(paths["output_dir"], exist_ok=True)

    archive, outline, index = build_archive_from_folder(
        paths["input_dir"], config,
        paths["key_master"], paths["key_players"],
        paths["type_master"], paths["type_players"],
        paths["output_dir"], paths["meta"]
    )
    save_json_archive(paths["output_file"], paths["meta"], outline, archive, index)
