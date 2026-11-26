#!/usr/bin/env python3
"""
Скрипт для объединения всех .md файлов из подпапок в единый файл.

Запуск:
  python merge_txt.py [папка1 папка2 ...]
Пути к папкам с исходными файлами передаются позиционными аргументами
(без ключей). Если аргументы не переданы, используются пути по умолчанию:
  - /home/smirnov/Documents/AI/Нулевой/Референсы
  - /home/smirnov/Documents/AI/Нулевой/Novells

Результат сохраняется в:
  - <OUTPUT_DIR>/bibl-[YYYYMMDD-HHMMSS].md
где OUTPUT_DIR по умолчанию:
  - /home/smirnov/Documents/AI/Нулевой/Библия
(можно переопределить переменной окружения MERGE_OUTPUT_DIR)

Кодировки:
  - Входные файлы читаются с автоопределением: сначала UTF-8 (в т.ч. с BOM),
    затем cp1251 (Windows-1251). Непрочитываемые файлы помечаются в выводе
    как ошибка чтения, но не прерывают слияние.
  - Выходной файл всегда записывается в UTF-8 (без BOM); артефакты U+FEFF
    из входного текста удаляются.
  - Кириллица полностью поддерживается в именах файлов/папок и в содержимом.

Исключает из выборки:
  - Папки и файлы, начинающиеся с "_"
  - Файлы и папки, содержащие "draft" в названии (без учёта регистра)
  - Пути и файлы внутри выходной директории (чтобы не подхватить
    собственные bibl-*.md от предыдущих запусков)

Если в папке есть файлы filename.md и filename_(datetime).md,
то приоритет отдаётся файлу с datetime в имени (выбирается самый свежий).
Если все файлы одной группы без datetime — берётся единственный.

Поддерживаемые форматы datetime в имени файла:
  - Вечер_(04:13_03.11.2026).md       → HH:MM_DD.MM.YYYY в скобках
  - Вечер_(04:13 03.11.2026).md       → HH:MM DD.MM.YYYY в скобках
  - Вечер_(04.13_03.11.2026).md       → HH.MM_DD.MM.YYYY в скобках
  - Вечер_(03.11.2026).md             → только дата DD.MM.YYYY в скобках
  - filename-20240115-143022.md       → YYYYMMDD-HHMMSS
  - filename-20240115_143022.md       → YYYYMMDD_HHMMSS
  - filename-2024-01-15_14-30-22.md   → YYYY-MM-DD_HH-MM-SS
  - filename-20240115.md              → YYYYMMDD
  - filename-2024-01-15.md            → YYYY-MM-DD
"""

import sys
import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Кодировки для чтения входных файлов (пробуются по порядку).
# utf-8-sig — сначала, чтобы корректно снимать BOM с UTF-8 файлов;
# cp1251 (Windows-1251) — совместимость с файлами в старой кириллической кодировке.
INPUT_ENCODINGS = ["utf-8-sig", "cp1251"]


def read_text_file(filepath: Path) -> tuple[str, str]:
    """
    Читает текстовый файл, пробуя кодировки из INPUT_ENCODINGS по порядку.
    Возвращает (содержимое, использованная_кодировка).
    Если ни одна кодировка не подошла — raises UnicodeDecodeError последней попытки.
    """
    last_error: UnicodeDecodeError | None = None
    for enc in INPUT_ENCODINGS:
        try:
            with open(filepath, "r", encoding=enc) as infile:
                content = infile.read()
            # Подстраховка: если файл был в UTF-8 без BOM, но содержал U+FEFF
            # внутри текста (артефакт двойной конвертации) — убираем его.
            return content.replace("\ufeff", ""), enc
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error


# Пути для поиска файлов (по умолчанию).
# Можно передать пути папок с исходными файлами аргументами командной строки:
#   python merge_txt.py /path/to/folder1 /path/to/folder2 ...
DEFAULT_SEARCH_PATHS = [
    Path("/home/smirnov/Documents/AI/Нулевой/Референсы"),
    Path("/home/smirnov/Documents/AI/Нулевой/Novells"),
]


def get_search_paths() -> list[Path]:
    """Возвращает пути для поиска: из аргументов командной строки или по умолчанию."""
    args = [a.strip() for a in sys.argv[1:] if a.strip()]
    if args:
        return [Path(a) for a in args]
    return DEFAULT_SEARCH_PATHS


# Путь для сохранения результата
# (можно переопределить переменной окружения MERGE_OUTPUT_DIR)
OUTPUT_DIR = Path(os.environ.get("MERGE_OUTPUT_DIR", "/home/smirnov/Documents/AI/Нулевой/Библия"))

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


def should_exclude(path: Path) -> bool:
    """
    Проверяет, должен ли файл/папка быть исключён из выборки.
    Исключаются:
      - Любые компоненты пути, начинающиеся с "_"
      - Любые компоненты пути, содержащие "draft" (без учёта регистра)
    """
    for part in path.parts:
        if part.startswith("_"):
            return True
        if "draft" in part.lower():
            return True
    return False


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


def find_md_files(base_path: Path) -> list[Path]:
    """Рекурсивно находит все .md файлы в подпапках указанной директории."""
    if not base_path.exists():
        print(f"⚠️  Директория не найдена: {base_path}")
        return []

    all_md_files = list(base_path.rglob("*.md"))
    
    # Фильтрация: исключаем файлы из папок с "_" или "draft"
    filtered_files = []
    excluded_count = 0
    for filepath in all_md_files:
        # Проверяем относительный путь от базовой директории
        rel_path = filepath.relative_to(base_path)
        if should_exclude(rel_path):
            excluded_count += 1
        else:
            filtered_files.append(filepath)
    
    if excluded_count > 0:
        print(f"   🚫 Исключено файлов (папки с '_' или 'draft'): {excluded_count}")
    
    filtered_files.sort()
    return filtered_files


def select_newest_per_group(files: list[Path]) -> tuple[list[Path], dict[str, dict]]:
    """
    Группирует файлы по базовому имени (без datetime).
    Для каждой группы выбирает файл с самой свежей датой.
    Приоритет у файлов с datetime в имени.
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
            # Разделяем файлы на "с датой" и "без даты"
            with_dt = [(f, dt) for f, dt in file_list if dt is not None]
            without_dt = [(f, dt) for f, dt in file_list if dt is None]

            if with_dt:
                # Приоритет у файлов с datetime — выбираем самый свежий из них
                with_dt.sort(key=lambda x: x[1], reverse=True)
                newest = with_dt[0][0]
                selected.append(newest)
                # Все остальные (и с датой, и без) идут в skipped
                skipped = with_dt[1:] + without_dt
            else:
                # Файлов с датой нет — берём единственный без даты
                newest = without_dt[0][0]
                selected.append(newest)
                skipped = without_dt[1:]

            group_details[group_key] = {
                "selected": newest,
                "selected_dt": (
                    next((dt for f, dt in file_list if f == newest and dt is not None), None)
                ),
                "skipped": skipped,
            }

    selected.sort()
    return selected, group_details


def merge_files(files: list[Path], output_path: Path) -> None:
    """Объединяет содержимое всех файлов в один выходной файл в формате Markdown.
    Входные файлы читаются с автоопределением кодировки (UTF-8 / UTF-8+BOM / cp1251),
    результат всегда записывается в UTF-8."""
    with open(output_path, "w", encoding="utf-8") as outfile:
        for i, filepath in enumerate(files):
            if i > 0:
                outfile.write("\n---\n\n")

            outfile.write(f"# {filepath.name}\n\n")
            outfile.write(f"*Путь: `{filepath}`*\n\n")

            try:
                content, used_enc = read_text_file(filepath)
                if used_enc != "utf-8-sig":
                    print(f"  🔤 {filepath.name}: прочитано в кодировке {used_enc}")
                outfile.write(content)
                if content and not content.endswith("\n"):
                    outfile.write("\n")
            except Exception as e:
                outfile.write(f"\n> ⚠️ **ОШИБКА ЧТЕНИЯ ФАЙЛА:** {e}\n")
                print(f"  ❌ Ошибка чтения: {filepath} — {e}")


def is_under_output_dir(path: Path) -> bool:
    """Проверяет, находится ли путь внутри выходной директории (или совпадает с ней)."""
    try:
        path.resolve().relative_to(OUTPUT_DIR.resolve())
        return True
    except (ValueError, OSError):
        return False


def main():
    search_paths = get_search_paths()

    # Выходная директория может находиться внутри одной из папок поиска —
    # исключаем такие пути, чтобы не подхватить собственные bibl-*.md файлы
    filtered_paths = []
    for p in search_paths:
        if is_under_output_dir(p):
            print(f"⏭️  Пропуск пути (внутри выходной директории): {p}")
        else:
            filtered_paths.append(p)
    search_paths = filtered_paths

    print("🔍 Поиск .md файлов...")
    print("=" * 50)

    all_files = []

    for search_path in search_paths:
        print(f"\n📂 Сканирование: {search_path}")
        files = [f for f in find_md_files(search_path) if not is_under_output_dir(f)]
        print(f"   Найдено файлов: {len(files)}")
        for f in files:
            print(f"   📄 {f.relative_to(search_path)}")
        all_files.extend(files)

    print(f"\n{'=' * 50}")
    print(f"📊 Всего найдено .md файлов: {len(all_files)}")

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
    output_filename = f"bibl-{datetime_str}.md"
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
