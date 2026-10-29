import { useState } from 'react'

const pythonCode = `#!/usr/bin/env python3
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
                outfile.write("\\n" + "=" * 60 + "\\n\\n")
            
            # Записываем имя файла как заголовок
            outfile.write(f"--- {filepath.name} ---\\n")
            outfile.write(f"--- Путь: {filepath} ---\\n\\n")
            
            # Читаем и записываем содержимое
            try:
                with open(filepath, "r", encoding="utf-8") as infile:
                    content = infile.read()
                    outfile.write(content)
                    # Добавляем перенос строки, если файл не заканчивается на него
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
    
    # Создаём директорию для вывода, если она не существует
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Формируем имя выходного файла с датой и временем
    datetime_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_filename = f"bibl-{datetime_str}.txt"
    output_path = OUTPUT_DIR / output_filename
    
    print(f"\\n📝 Объединение файлов...")
    print(f"📁 Выходной файл: {output_path}")
    
    merge_files(all_files, output_path)
    
    # Размер итогового файла
    size = output_path.stat().st_size
    size_kb = size / 1024
    
    print(f"\\n✅ Готово!")
    print(f"📄 Файл: {output_path}")
    print(f"📏 Размер: {size_kb:.1f} КБ ({size} байт)")
    print(f"📚 Файлов объединено: {len(all_files)}")


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
        </div>

        {/* Info Cards */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
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
                bibl-YYYYMMDD-HHMMSS.txt
              </div>
            </div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
            <div className="text-purple-400 font-semibold mb-1">⚙️ Функции</div>
            <div className="text-sm text-gray-300">
              <ul className="space-y-1">
                <li>• Рекурсивный поиск</li>
                <li>• Разделители между файлами</li>
                <li>• Обработка ошибок</li>
              </ul>
            </div>
          </div>
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
          <p className="mt-1">Имя файла содержит дату и время создания</p>
        </div>
      </div>
    </div>
  )
}

export default App
