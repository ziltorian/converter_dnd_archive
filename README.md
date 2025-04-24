
# 📦 Convertor: Архиватор Сессий DnD

Этот проект автоматизирует сбор, конвертацию и структурирование данных из HTML- и TXT-файлов игровых сессий Dungeons & Dragons в формат JSON.

---

## 🧩 Структура проекта

```
convertor/
│
├── main.py                         # Главный скрипт для запуска всех этапов
├── combined_archive_v2.py         # Объединение сессий в общий архив
├── check_system_messages.py       # Поиск системных сообщений от ChatGPT
├── converter_characters.py        # Конвертер персонажей и шаблонов
├── config.json                    # Все настройки, пути, ключи
│
├── archive/                       # 📁 Исходные сессии в HTML или TXT
├── characters/                    # 📁 Файлы шаблонов персонажей
└── result/                        # 📁 Готовые JSON-файлы
     ├── archive_sessions_v2.json
     ├── prequels_and_oneshots.json
     ├── archive_Глава_....json
     ├── archive_Ваншот_....json
```

---

### 📥 Установка из GitHub

> Репозиторий: [https://github.com/ziltorian/dndconverter](https://github.com/ziltorian/dndconverter)

#### 1. Клонируй репозиторий

```bash
git clone https://github.com/ziltorian/dndconverter.git
cd dndconverter
```

#### 2. Установи виртуальную среду (по желанию, но рекомендуется)

```bash
python -m venv .venv
.\.venv\Scripts\activate      :: для Windows
source .venv/bin/activate     # для Linux/macOS
```

#### 3. Установи зависимости

```bash
pip install -r requirements.txt
```

#### 4. Запуск проекта

```bash
python main.py
```

#### ✅ Альтернативный способ — через `update_and_run.bat`

```bash
update_and_run.bat
```

Этот файл:
- автоматически подтягивает обновления с GitHub
- обновляет зависимости
- запускает `main.py`

---

## 🚀 Быстрый запуск

1. Установи зависимости:

```bash
pip install -r requirements.txt
```

2. Запусти основной скрипт:

```bash
python main.py
```

---

## ⚙️ Настройка

Открой `config.json`, чтобы задать:

- Пути к папкам (`archive`, `result`, `characters`)
- Названия ключей (`master`, `players`)
- Настройки метаданных, названий глав, форматов сцены

---

## 📌 Пример входных данных

В `archive/` помести HTML или TXT-файл из ChatGPT-сессии. Файл должен содержать блоки `<pre class="message">` с авторами `user` и `chatgpt`.

В `characters/` используй `.txt` с разметкой Markdown по ТЗ. Пример:

```
# Персонаж:
- Имя: Ядвига
### Общая информация:
- Раса: Дварф, мужчина
- Класс: Жрец
- Уровень персонажа: 2
## Снаряжение:
### Механический жучок:
- Свойства: Указаны в "Осколки"
```

---

## ✨ Возможности

- Поддержка ваншотов / приквелов
- Автогенерация заголовков сцен
- Вложенные JSON-структуры с метаданными
- Отдельный `prequels_and_oneshots.json`
- Проверка на системные сообщения
- Парсинг персонажей с вложенностью до 10 уровней

---

## 📄 Автор

Создан с заботой об удобстве, порядке и приключениях 🎲
