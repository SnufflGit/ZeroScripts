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

# Regex для извлечения datetime из конца имени файла (перед расширением)
# Поддерживает форматы:
#   filename-20240115-143022.txt
#   filename-20240115.txt
#   filename-2024-01-15_14-30-22.txt
#   filename-20240115_143022.txt
DATETIME_PATTERNS = [
    # YYYYMMDD-HHMMSS
    re.compile(r"^(.+)-(\d{8}-\d{6})$"),
    # YYYYMMDD_HHMMSS
    re.compile(r"^(.+)-(\d{8}_\d{6})$"),
    # YYYY-MM-DD_HH-MM-SS
    re.compile(r"^(.+)-(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})$"),
    # YYYYMMDD
    re.compile(r"^(.+)-(\d{8})$"),
    # YYYY-MM-DD
    re.compile(r"^(.+)-(\d{4}-\d{2}-\d{2})$"),
]

# Форматы для парсинга извлечённой datetime-строки
DATETIME_FORMATS = [
    "%Y%m%d-%H%M%S",
    "%Y%m%d_%H%M%S",
    "%Y-%m-%d_%H-%M-%S",
    "%Y%m%d",
    "%Y-%m-%d",
]


def parse_datetime_from_filename(filename: str) -> tuple[str, datetime | None]:
    """
    Извлекает базовое имя и datetime из имени файла.
    Возвращает (base_name, parsed_datetime).
    Если datetime не найден, возвращает (полное_имя, None).
    """
    # Убираем расширение .txt
    stem = Path(filename).stem

    for pattern in DATETIME_PATTERNS:
        match = pattern.match(stem)
        if match:
            base_name = match.group(1)
            dt_str = match.group(2)

            # Пытаемся распарсить дату
            for fmt in DATETIME_FORMATS:
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


def select_newest_per_group(files: list[Path]) -> tuple[list[Path], dict[str, list[Path]]]:
    """
    Группирует файлы по базовому имени (без datetime).
    Для каждой группы выбирает файл с самой свежей датой.
    Возвращает (список_выбранных, словарь_групп).
    """
    # Группируем: base_name -> [(filepath, datetime), ...]
    groups: dict[str, list[tuple[Path, datetime | None]]] = defaultdict(list)

    for filepath in files:
        base_name, parsed_dt = parse_datetime_from_filename(filepath.name)
        # Используем директорию + базовое имя как ключ группы,
        # чтобы файлы из разных папок с одинаковым именем не смешивались
        group_key = f"{filepath.parent}::{base_name}"
        groups[group_key].append((filepath, parsed_dt))

    selected = []
    group_details = {}

    for group_key, file_list in groups.items():
        if len(file_list) == 1:
            # Один файл — берём его
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

            # Логируем, какие файлы были отброшены
            group_details[group_key] = {
                "selected": newest,
                "skipped": [f for f, _ in file_list[1:]],
            }

    selected.sort()
    return selected, group_details


def merge_files(files: list[Path], output_path: Path) -> None:
    """Объединяет содержимое всех файлов в один выходной файл."""
    with open(output_path, "w", encoding="utf-8") as outfile:
        for i, filepath in enumerate(files):
            # Добавляем разделитель между файлами
            if i > 0:
                outfile.write("\n" + "=" * 60 + "\n\n")

            # Записываем имя файла как заголовок
            outfile.write(f"--- {filepath.name} ---\n")
            outfile.write(f"--- Путь: {filepath} ---\n\n")

            # Читаем и записываем содержимое
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
            print(f"\n   📌 Группа «{base}»:")
            print(f"      ✅ Выбран: {details['selected'].name}")
            for skipped in details["skipped"]:
                print(f"      ⏭️  Пропущен: {skipped.name}")
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
