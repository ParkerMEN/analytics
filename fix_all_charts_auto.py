#!/usr/bin/env python3
# filepath: c:\projects\fix_all_charts_auto.py

import os
import glob
import re
import sys

def find_visualization_files(base_dir, pattern="viz_*.html"):
    """Находит все файлы визуализаций по заданному шаблону рекурсивно"""
    print(f"Поиск файлов визуализаций в {base_dir}...")
    
    all_files = []
    for root, _, _ in os.walk(base_dir):
        path_pattern = os.path.join(root, pattern)
        files = glob.glob(path_pattern)
        all_files.extend(files)
    
    print(f"Найдено {len(all_files)} файлов визуализаций")
    return all_files

def fix_chart_file(file_path):
    """Исправляет все проблемы с фиксированными размерами в одном файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Проверки и замены для разных вариаций проблемы
        replacements = [
            # 1. Основной вариант проблемы (как в проблемном файле)
            {
                'pattern': r'"plot_bgcolor"\s*:\s*"white"\s*,\s*"height"\s*:\s*\d+\s*,\s*"width"\s*:\s*\d+\s*,\s*"annotations"',
                'replacement': r'"plot_bgcolor":"white","autosize":true,"annotations"'
            },
            # 2. Вариант с height и width в других местах (в начале layout)
            {
                'pattern': r'"height"\s*:\s*\d+\s*,\s*"width"\s*:\s*\d+\s*,(.+?"plot_bgcolor"\s*:\s*"white")',
                'replacement': r'"autosize":true,\1'
            },
            # 3. Только height без width
            {
                'pattern': r'"plot_bgcolor"\s*:\s*"white"\s*,\s*"height"\s*:\s*\d+\s*,\s*"annotations"',
                'replacement': r'"plot_bgcolor":"white","autosize":true,"annotations"'
            },
            # 4. Только width без height
            {
                'pattern': r'"plot_bgcolor"\s*:\s*"white"\s*,\s*"width"\s*:\s*\d+\s*,\s*"annotations"',
                'replacement': r'"plot_bgcolor":"white","autosize":true,"annotations"'
            },
            # 5. Добавление responsive:true если есть config без responsive
            {
                'pattern': r'(\{[^{}]*"displayModeBar"\s*:[^{}]*\})',
                'check': lambda m: '"responsive"' not in m.group(1),
                'replacement': lambda m: m.group(1).replace('{', '{"responsive":true,')
            }
        ]
        
        modified = False
        for replacement in replacements:
            pattern = replacement['pattern']
            
            # Если есть функция check, используем её для дополнительной проверки
            if 'check' in replacement:
                matches = list(re.finditer(pattern, content))
                for match in matches:
                    if replacement['check'](match):
                        # Используем функцию замены если она есть, иначе строку замены
                        if callable(replacement.get('replacement')):
                            repl = replacement['replacement'](match)
                            # Заменяем только конкретное совпадение
                            content = content[:match.start()] + repl + content[match.end():]
                        else:
                            # В этом случае нужно делать полную замену шаблона
                            content = re.sub(pattern, replacement['replacement'], content)
                        modified = True
            else:
                # Простая замена по шаблону
                new_content = re.sub(pattern, replacement['replacement'], content)
                if new_content != content:
                    content = new_content
                    modified = True
        
        # Если контент был изменен, сохраняем изменения
        if modified:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"✅ ИСПРАВЛЕНО: {os.path.basename(file_path)}")
            return True
        else:
            print(f"✓ УЖЕ В ПОРЯДКЕ: {os.path.basename(file_path)}")
            return False
    
    except Exception as e:
        print(f"❌ ОШИБКА при обработке {os.path.basename(file_path)}: {str(e)}")
        return False

def process_all_files(base_dir):
    """Обрабатывает все файлы визуализаций в указанной директории"""
    files = find_visualization_files(base_dir)
    
    if not files:
        print("Файлы визуализаций не найдены!")
        return
    
    stats = {
        "total": len(files),
        "fixed": 0,
        "already_ok": 0,
        "errors": 0
    }
    
    print("\n" + "="*60)
    print("АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ФАЙЛОВ ВИЗУАЛИЗАЦИЙ")
    print("="*60)
    
    for file_path in files:
        try:
            if fix_chart_file(file_path):
                stats["fixed"] += 1
            else:
                stats["already_ok"] += 1
        except Exception as e:
            stats["errors"] += 1
            print(f"❌ Неожиданная ошибка при обработке {os.path.basename(file_path)}: {str(e)}")
    
    print("\n" + "="*60)
    print("ИТОГИ ОБРАБОТКИ ФАЙЛОВ")
    print("="*60)
    print(f"Всего обработано: {stats['total']}")
    print(f"Исправлено: {stats['fixed']}")
    print(f"Уже в порядке: {stats['already_ok']}")
    print(f"Ошибок: {stats['errors']}")
    print("="*60)

if __name__ == "__main__":
    print("\n=== АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ДИАГРАММ PLOTLY ===\n")
    
    # Директория передается как аргумент или используется значение по умолчанию
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = "c:\\projects\\analytics_output\\visualizations"
    
    process_all_files(base_dir)
    
    print("\n=== ЗАВЕРШЕНО ===\n")