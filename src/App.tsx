import { useState } from 'react'

const pythonCode = `#!/usr/bin/env python3
"""
Скрипт для объединения всех .txt файлов из подпапок в единый файл.
Ищет файлы в:
  - /home/smirnov/Documents/AI/Нулевой/Референсы
  - /home/smirnov/Documents/AI/Нулевой/Novells
И сохраняет результат в:
  - /home/smirnov/Documents/AI/Нулевой/Библия/bibl.txt

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
    (re.compile(r"^(.+)_\\((\\d{2}:\\d{2}_\\d{2}\\.\\d{2}\\.\\d{4})\\)$"), "%H:%M_%d.%m.%Y"),
    # Вариант с пробелом: name_(HH:MM DD.MM.YYYY) — например: Вечер_(04:13 03.11.2026)
    (re.compile(r"^(.+)_\\((\\d{2}:\\d{2} \\d{2}\\.\\d{2}\\.\\d{4})\\)$"), "%H:%M %d.%m.%Y"),
    # Вариант с точкой вместо _: name_(HH.MM_DD.MM.YYYY)
    (re.compile(r"^(.+)_\\((\\d{2}\\.\\d{2}_\\d{2}\\.\\d{2}\\.\\d{4})\\)$"), "%H.%M_%d.%m.%Y"),
    # Только дата в скобках: name_(DD.MM.YYYY)
    (re.compile(r"^(.+)_\\((\\d{2}\\.\\d{2}\\.\\d{4})\\)$"), "%d.%m.%Y"),
    # YYYYMMDD-HHMMSS
    (re.compile(r"^(.+)-(\\d{8}-\\d{6})$"), "%Y%m%d-%H%M%S"),
    # YYYYMMDD_HHMMSS
    (re.compile(r"^(.+)-(\\d{8}_\\d{6})$"), "%Y%m%d_%H%M%S"),
    # YYYY-MM-DD_HH-MM-SS
    (re.compile(r"^(.+)-(\\d{4}-\\d{2}-\\d{2}_\\d{2}-\\d{2}-\\d{2})$"), "%Y-%m-%d_%H-%M-%S"),
    # YYYYMMDD
    (re.compile(r"^(.+)-(\\d{8})$"), "%Y%m%d"),
    # YYYY-MM-DD
    (re.compile(r"^(.+)-(\\d{4}-\\d{2}-\\d{2})$"), "%Y-%m-%d"),
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
                outfile.write("\\n" + "=" * 60 + "\\n\\n")

            outfile.write(f"--- {filepath.name} ---\\n")
            outfile.write(f"--- Путь: {filepath} ---\\n\\n")

            try:
                with open(filepath, "r", encoding="utf-8") as infile:
                    content = infile.read()
                    outfile.write(content)
                    if content and not content.endswith("\\n"):
                        outfile.write("\\n")
            except Exception as e:
                outfile.write(f"\\n[ОШИБКА ЧТЕНИЯ ФАЙЛА: {e}]\\n")
                print(f"  ❌ Ошибка чтения: {filepath} — {e}")


def main():
    print("🔍 Поиск .txt файлов...")
    print("=" * 50)

    all_files = []

    for search_path in SEARCH_PATHS:
        print(f"\\n📂 Сканирование: {search_path}")
        files = find_txt_files(search_path)
        print(f"   Найдено файлов: {len(files)}")
        for f in files:
            print(f"   📄 {f.relative_to(search_path)}")
        all_files.extend(files)

    print(f"\\n{'=' * 50}")
    print(f"📊 Всего найдено .txt файлов: {len(all_files)}")

    if not all_files:
        print("❌ Файлы не найдены. Нечего объединять.")
        return

    # Фильтрация: для файлов с datetime в имени оставляем только самый свежий
    print(f"\\n🔄 Фильтрация дубликатов (выбор самых свежих)...")
    selected_files, group_details = select_newest_per_group(all_files)

    # Выводим информацию о пропущенных файлах
    if group_details:
        print(f"\\n   ⚡ Обнаружено {len(group_details)} групп(а) с несколькими версиями:")
        for group_key, details in group_details.items():
            base = group_key.split("::")[-1]
            dt_str = details["selected_dt"].strftime("%d.%m.%Y %H:%M") if details["selected_dt"] else "без даты"
            print(f"\\n   📌 Группа «{base}»:")
            print(f"      ✅ Выбран: {details['selected'].name}  ({dt_str})")
            for skipped, skipped_dt in details["skipped"]:
                skipped_dt_str = skipped_dt.strftime("%d.%m.%Y %H:%M") if skipped_dt else "без даты"
                print(f"      ⏭️  Пропущен: {skipped.name}  ({skipped_dt_str})")
    else:
        print("   ℹ️  Дубликатов не обнаружено.")

    skipped_count = len(all_files) - len(selected_files)
    print(f"\\n   📋 Для слияния отобрано: {len(selected_files)} файлов")
    if skipped_count > 0:
        print(f"   🗑️  Пропущено (устаревшие версии): {skipped_count}")

    # Создаём директорию для вывода
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Имя выходного файла
    output_filename = "bibl.txt"
    output_path = OUTPUT_DIR / output_filename

    print(f"\\n📝 Объединение файлов...")
    print(f"📁 Выходной файл: {output_path}")

    merge_files(selected_files, output_path)

    # Размер итогового файла
    size = output_path.stat().st_size
    size_kb = size / 1024

    print(f"\\n✅ Готово!")
    print(f"📄 Файл: {output_path}")
    print(f"📏 Размер: {size_kb:.1f} КБ ({size} байт)")
    print(f"📚 Файлов объединено: {len(selected_files)}")


if __name__ == "__main__":
    main()`

function App() {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(pythonCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 text-white p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            📜 Merge TXT Script
          </h1>
          <p className="text-gray-400 text-lg">
            Python скрипт для объединения .txt файлов из подпапок
          </p>
          <p className="text-amber-400 text-sm mt-2">
            ⚡ С автоматическим выбором самой свежей версии файла
          </p>
        </div>

        {/* Info Cards */}
        <div className="grid md:grid-cols-3 gap-4 mb-6">
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
            <div className="text-blue-400 font-semibold mb-1">📂 Источники</div>
            <div className="text-sm text-gray-300 space-y-1">
              <div className="font-mono text-xs bg-slate-900/50 px-2 py-1 rounded">
                .../Нулевой/Референсы/
              </div>
              <div className="font-mono text-xs bg-slate-900/50 px-2 py-1 rounded">
                .../Нулевой/Novells/
              </div>
            </div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
            <div className="text-green-400 font-semibold mb-1">📁 Результат</div>
            <div className="text-sm text-gray-300">
              <div className="font-mono text-xs bg-slate-900/50 px-2 py-1 rounded">
                .../Нулевой/Библия/
              </div>
              <div className="font-mono text-xs bg-slate-900/50 px-2 py-1 rounded mt-1">
                bibl.txt
              </div>
            </div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
            <div className="text-purple-400 font-semibold mb-1">⚙️ Функции</div>
            <div className="text-sm text-gray-300">
              <ul className="space-y-1">
                <li>• Рекурсивный поиск</li>
                <li>• Фильтр дубликатов</li>
                <li>• Выбор свежей версии</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Dedup explanation */}
        <div className="bg-amber-900/20 border border-amber-700/50 rounded-xl p-4 mb-6">
          <h2 className="text-lg font-semibold text-amber-400 mb-2">⚡ Логика дедупликации</h2>
          <p className="text-gray-300 text-sm mb-3">
            Если в одной папке есть несколько файлов с одинаковым базовым именем и разными датами,
            скрипт извлекает дату из имени и оставляет только самую свежую версию:
          </p>
          <div className="bg-slate-900/70 rounded-lg p-3 font-mono text-xs space-y-1.5 mb-3">
            <div className="text-gray-400">
              📄 <span className="text-gray-300">Вечер</span><span className="text-amber-400">_(04:13_01.11.2026)</span>.txt
              <span className="text-red-400 ml-2">⏭️ пропущен</span>
            </div>
            <div className="text-gray-400">
              📄 <span className="text-gray-300">Вечер</span><span className="text-amber-400">_(04:13_03.11.2026)</span>.txt
              <span className="text-green-400 ml-2">✅ выбран (самый свежий)</span>
            </div>
          </div>
          <p className="text-gray-400 text-xs mb-2">
            Основной формат: <code className="text-blue-300">Имя_(HH:MM_DD.MM.YYYY).txt</code>
          </p>
          <p className="text-gray-400 text-xs">
            Также поддерживаются: <code className="text-blue-300">YYYYMMDD-HHMMSS</code>,{' '}
            <code className="text-blue-300">YYYY-MM-DD</code>, <code className="text-blue-300">YYYYMMDD</code> и другие
          </p>
        </div>

        {/* Usage */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 mb-6">
          <h2 className="text-lg font-semibold text-yellow-400 mb-2">🚀 Запуск</h2>
          <code className="block bg-slate-900 px-4 py-2 rounded-lg text-green-400 font-mono text-sm">
            python3 merge_txt.py
          </code>
        </div>

        {/* Code Block */}
        <div className="relative">
          <div className="flex items-center justify-between bg-slate-800 border border-slate-700 rounded-t-xl px-4 py-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="ml-3 text-sm text-gray-400 font-mono">merge_txt.py</span>
            </div>
            <button
              onClick={handleCopy}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                copied
                  ? 'bg-green-600 text-white'
                  : 'bg-blue-600 hover:bg-blue-500 text-white'
              }`}
            >
              {copied ? '✓ Скопировано!' : '📋 Копировать'}
            </button>
          </div>
          <div className="bg-slate-900 border border-t-0 border-slate-700 rounded-b-xl overflow-auto max-h-[600px]">
            <pre className="p-4 text-sm leading-relaxed">
              <code className="text-gray-300 font-mono whitespace-pre">{pythonCode}</code>
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Скрипт создаёт разделители между файлами и заголовки с путями</p>
          <p className="mt-1">Итоговый файл: bibl.txt</p>
        </div>
      </div>
    </div>
  )
}

export default App
