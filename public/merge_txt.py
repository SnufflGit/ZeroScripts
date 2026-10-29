#!/usr/bin/env python3
"""
Скрипт для объединения всех .txt файлов из подпапок в единый файл.
Ищет файлы в:
  - /home/smirnov/Documents/AI/Нулевой/Референсы
  - /home/smirnov/Documents/AI/Нулевой/Novells
И сохраняет результат в:
  - /home/smirnov/Documents/AI/Нулевой/Библия/bibl-[datetime].txt
"""

import os
import glob
from datetime import datetime
from pathlib import Path


# Пути для поиска файлов
SEARCH_PATHS = [
    Path("/home/smirnov/Documents/AI/Нулевой/Референсы"),
    Path("/home/smirnov/Documents/AI/Нулевой/Novells"),
]

# Путь для сохранения результата
OUTPUT_DIR = Path("/home/smirnov/Documents/AI/Нулевой/Библия")


def find_txt_files(base_path: Path) -> list[Path]:
    """Рекурсивно находит все .txt файлы в подпапках указанной директории."""
    if not base_path.exists():
        print(f"⚠️  Директория не найдена: {base_path}")
        return []
    
    txt_files = list(base_path.rglob("*.txt"))
    txt_files.sort()  # Сортируем для предсказуемого порядка
    return txt_files


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
                    # Добавляем перенос строки, если файл не заканчивается на него
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
    
    # Создаём директорию для вывода, если она не существует
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Формируем имя выходного файла с датой и временем
    datetime_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_filename = f"bibl-{datetime_str}.txt"
    output_path = OUTPUT_DIR / output_filename
    
    print(f"\n📝 Объединение файлов...")
    print(f"📁 Выходной файл: {output_path}")
    
    merge_files(all_files, output_path)
    
    # Размер итогового файла
    size = output_path.stat().st_size
    size_kb = size / 1024
    
    print(f"\n✅ Готово!")
    print(f"📄 Файл: {output_path}")
    print(f"📏 Размер: {size_kb:.1f} КБ ({size} байт)")
    print(f"📚 Файлов объединено: {len(all_files)}")


if __name__ == "__main__":
    main()
