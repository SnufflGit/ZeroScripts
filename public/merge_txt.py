#!/usr/bin/env python3
"""
Скрипт для объединения всех .txt файлов из подпапок в единый файл.
Ищет файлы в:
  - /home/smirnov/Documents/AI/Нулевой/Референсы
  - /home/smirnov/Documents/AI/Нулевой/Novells
И сохраняет результат в:
  - /home/smirnov/Documents/AI/Нулевой/Библия/bibl-[datetime].txt

Если в папке несколько файлов вида filename-(datetime).txt,
то для слияния выбирается самый свежий (с наибольшей датой).

Поддерживаемые форматы datetime в имени файла:
  - Вечер_(04:13_03.11.2026).txt       → HH:MM_DD.MM.YYYY в скобках
  - Вечер_(04:13 03.11.2026).txt       → HH:MM DD.MM.YYYY в скобках
  - filename-20240115-143022.txt       → YYYYMMDD-HHMMSS
  - filename-20240115.txt              → YYYYMMDD
  - filename-2024-01-15.txt            → YYYY-MM-DD
"""

import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# Пути для поиска файлов
SEARCH_PATHS = [
    Path("/home/smirnov/Documents/AI/Нулевой/Референсы"),
    Path("/home/smirnov/Documents/AI/Нулевой/Novells"),
]

# Путь для сохранения результата
OUTPUT_DIR = Path("/home/smirnov/Documents/AI/Нулевой/Библия")

# Regex-паттерны для извлечения datetime из имени файла (перед расширением)
# Каждый паттерн: (regex, формат_даты)
DATETIME_PATTERNS = [
    # Основной формат: name_(HH:MM_DD.MM.YYYY)  — например: Вечер_(04:13_03.11.2026)
    (re.compile(r"^(.+)_\((\d{2}:\d{2}_\d{2}\.\d{2}\.\d{4})\)$"), "%H:%M_%d.%m.%Y"),
    # Вариант с пробелом: name_(HH:MM DD.MM.YYYY) — например: Вечер_(04:13 03.11.2026)
    (re.compile(r"^(.+)_\((\d{2}:\d{2} \d{2}\.\d{2}\.\d{4})\)$"), "%H:%M %d.%m.%Y"),
    # Вариант с точкой вместо _: name_(HH.MM_DD.MM.YYYY)
    (re.compile(r"^(.+)_\((\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{4})\)$"), "%H.%M_%d.%m.%Y"),
    # Только дата в скобках: name_(DD.MM.YYYY)
    (re.compile(r"^(.+)_\((\d{2}\.\d{2}\.\d{4})\)$"), "%d.%m.%Y"),
    # YYYYMMDD-HHMMSS
    (re.compile(r"^(.+)-(\d{8}-\d{6})$"), "%Y%m%d-%H%M%S"),
    # YYYYMMDD_HHMMSS
    (re.compile(r"^(.+)-(\d{8}_\d{6})$"), "%Y%m%d_%H%M%S"),
    # YYYY-MM-DD_HH-MM-SS
    (re.compile(r"^(.+)-(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})$"), "%Y-%m-%d_%H-%M-%S"),
    # YYYYMMDD
    (re.compile(r"^(.+)-(\d{8})$"), "%Y%m%d"),
    # YYYY-MM-DD
    (re.compile(r"^(.+)-(\d{4}-\d{2}-\d{2})$"), "%Y-%m-%d"),
]


def parse_datetime_from_filename(filename: str) -> tuple[str, datetime | None]:
    """
    Извлекает базовое имя и datetime из имени файла.
    Возвращает (base_name, parsed_datetime).
    Если datetime не найден, возвращает (полное_имя, None).
    """
    stem = Path(filename).stem

    for pattern, fmt in DATETIME_PATTERNS:
        match = pattern.match(stem)
        if match:
            base_name = match.group(1)
            dt_str = match.group(2)
            try:
                parsed_dt = datetime.strptime(dt_str, fmt)
                return base_name, parsed_dt
            except ValueError:
                continue

    # Если ни один паттерн не подошёл — считаем что datetime нет
    return stem, None


def find_txt_files(base_path: Path) -> list[Path]:
    """Рекурсивно находит все .txt файлы в подпапках указанной директории."""
    if not base_path.exists():
        print(f"⚠️  Директория не найдена: {base_path}")
        return []

    txt_files = list(base_path.rglob("*.txt"))
    txt_files.sort()
    return txt_files


def select_newest_per_group(files: list[Path]) -> tuple[list[Path], dict[str, dict]]:
    """
    Группирует файлы по базовому имени (без datetime).
    Для каждой группы выбирает файл с самой свежей датой.
    Возвращает (список_выбранных, словарь_групп).
    """
    groups: dict[str, list[tuple[Path, datetime | None]]] = defaultdict(list)

    for filepath in files:
        base_name, parsed_dt = parse_datetime_from_filename(filepath.name)
        # Ключ группы: директория + базовое имя
        group_key = f"{filepath.parent}::{base_name}"
        groups[group_key].append((filepath, parsed_dt))

    selected = []
    group_details = {}

    for group_key, file_list in groups.items():
        if len(file_list) == 1:
            filepath, _ = file_list[0]
            selected.append(filepath)
        else:
            # Несколько файлов — выбираем самый свежий
            # Файлы без даты считаем самыми старыми
            file_list.sort(
                key=lambda x: x[1] if x[1] is not None else datetime.min,
                reverse=True,
            )
            newest = file_list[0][0]
            selected.append(newest)

            group_details[group_key] = {
                "selected": newest,
                "selected_dt": file_list[0][1],
                "skipped": [(f, dt) for f, dt in file_list[1:]],
            }

    selected.sort()
    return selected, group_details


def merge_files(files: list[Path], output_path: Path) -> None:
    """Объединяет содержимое всех файлов в один выходной файл."""
    with open(output_path, "w", encoding="utf-8") as outfile:
        for i, filepath in enumerate(files):
            if i > 0:
                outfile.write("\n" + "=" * 60 + "\n\n")

            outfile.write(f"--- {filepath.name} ---\n")
            outfile.write(f"--- Путь: {filepath} ---\n\n")

            try:
                with open(filepath, "r", encoding="utf-8") as infile:
                    content = infile.read()
                    outfile.write(content)
                    if content and not content.endswith("\n"):
                        outfile.write("\n")
            except Exception as e:
                outfile.write(f"\n[ОШИБКА ЧТЕНИЯ ФАЙЛА: {e}]\n")
                print(f"  ❌ Ошибка чтения: {filepath} — {e}")


def main():
    print("🔍 Поиск .txt файлов...")
    print("=" * 50)

    all_files = []

    for search_path in SEARCH_PATHS:
        print(f"\n📂 Сканирование: {search_path}")
        files = find_txt_files(search_path)
        print(f"   Найдено файлов: {len(files)}")
        for f in files:
            print(f"   📄 {f.relative_to(search_path)}")
        all_files.extend(files)

    print(f"\n{'=' * 50}")
    print(f"📊 Всего найдено .txt файлов: {len(all_files)}")

    if not all_files:
        print("❌ Файлы не найдены. Нечего объединять.")
        return

    # Фильтрация: для файлов с datetime в имени оставляем только самый свежий
    print(f"\n🔄 Фильтрация дубликатов (выбор самых свежих)...")
    selected_files, group_details = select_newest_per_group(all_files)

    # Выводим информацию о пропущенных файлах
    if group_details:
        print(f"\n   ⚡ Обнаружено {len(group_details)} групп(а) с несколькими версиями:")
        for group_key, details in group_details.items():
            base = group_key.split("::")[-1]
            dt_str = details["selected_dt"].strftime("%d.%m.%Y %H:%M") if details["selected_dt"] else "без даты"
            print(f"\n   📌 Группа «{base}»:")
            print(f"      ✅ Выбран: {details['selected'].name}  ({dt_str})")
            for skipped, skipped_dt in details["skipped"]:
                skipped_dt_str = skipped_dt.strftime("%d.%m.%Y %H:%M") if skipped_dt else "без даты"
                print(f"      ⏭️  Пропущен: {skipped.name}  ({skipped_dt_str})")
    else:
        print("   ℹ️  Дубликатов не обнаружено.")

    skipped_count = len(all_files) - len(selected_files)
    print(f"\n   📋 Для слияния отобрано: {len(selected_files)} файлов")
    if skipped_count > 0:
        print(f"   🗑️  Пропущено (устаревшие версии): {skipped_count}")

    # Создаём директорию для вывода
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Формируем имя выходного файла с датой и временем
    datetime_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_filename = f"bibl-{datetime_str}.txt"
    output_path = OUTPUT_DIR / output_filename

    print(f"\n📝 Объединение файлов...")
    print(f"📁 Выходной файл: {output_path}")

    merge_files(selected_files, output_path)

    # Размер итогового файла
    size = output_path.stat().st_size
    size_kb = size / 1024

    print(f"\n✅ Готово!")
    print(f"📄 Файл: {output_path}")
    print(f"📏 Размер: {size_kb:.1f} КБ ({size} байт)")
    print(f"📚 Файлов объединено: {len(selected_files)}")


if __name__ == "__main__":
    main()
