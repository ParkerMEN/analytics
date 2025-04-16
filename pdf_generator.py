import os
import re
import matplotlib
matplotlib.use('Agg')  # Установка не-интерактивного бэкенда
import matplotlib.pyplot as plt
from fpdf import FPDF
import numpy as np

class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        # Добавляем шрифт с поддержкой кириллицы
        self.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        
    def chapter_title(self, title):
        self.set_font('DejaVu', '', 16)
        self.cell(0, 10, title, 0, 1, 'C')
        self.ln(10)
        
    def chapter_body(self, text):
        self.set_font('DejaVu', '', 12)
        self.multi_cell(0, 8, text)
        self.ln()

def extract_python_code(response_file):
    """Извлекает Python-код для построения диаграммы из файла ответа"""
    try:
        with open(response_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Поиск кода между ```python и ```
        code_pattern = r'```python(.*?)```'
        match = re.search(code_pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    except Exception as e:
        print(f"Ошибка при извлечении Python-кода: {e}")
        return None

def generate_plot(code, output_path):
    """Генерирует изображение графика из кода Python"""
    try:
        # Закрываем все предыдущие фигуры
        plt.close('all')
        
        # Подготавливаем код с необходимыми импортами и улучшенными настройками
        modified_code = """
import matplotlib
matplotlib.use('Agg')  # Не-интерактивный режим
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors

# Настройки для улучшения читаемости и предотвращения наложения
plt.rcParams['figure.figsize'] = (12, 8)  # Увеличиваем размер фигуры по умолчанию
plt.rcParams['figure.autolayout'] = True  # Автоматический макет
plt.rcParams['font.size'] = 12  # Размер шрифта для общего текста
plt.rcParams['axes.titlesize'] = 18  # Увеличиваем размер названия диаграммы
plt.rcParams['lines.linewidth'] = 0.8  # Делаем линии тоньше
plt.rcParams['axes.linewidth'] = 0.5  # Тонкие границы осей
plt.rcParams['axes.edgecolor'] = '#888888'  # Менее контрастные оси
plt.rcParams['grid.linewidth'] = 0.3  # Тонкие линии сетки
plt.rcParams['patch.linewidth'] = 0.5  # Тонкие линии для патчей (например, в круговых диаграммах)
plt.rcParams['xtick.major.width'] = 0.5  # Тонкие отметки на осях
plt.rcParams['ytick.major.width'] = 0.5  # Тонкие отметки на осях

# Функция для улучшения разметки графика
def improve_layout():
    fig = plt.gcf()
    for ax in fig.axes:
        # Обрабатываем подписи осей X
        if hasattr(ax, 'get_xticklabels'):
            labels = ax.get_xticklabels()
            # Поворачиваем подписи только если они накладываются
            if len(labels) > 4:
                # Получаем границы оси X
                x_min, x_max = ax.get_xlim()
                label_width = (x_max - x_min) / len(labels)
                
                # Проверяем средний размер текста подписей
                total_text_width = sum(len(l.get_text()) for l in labels)
                avg_char_width = total_text_width / len(labels) if labels else 0
                
                # Если подписи могут накладываться, поворачиваем их
                if avg_char_width > 4 and label_width < avg_char_width * 0.8:
                    plt.setp(labels, rotation=30, ha='right', fontsize=12)
            else:
                plt.setp(labels, fontsize=12)  # Увеличиваем размер шрифта для меньшего количества подписей
                
        # Регулируем расстояние между подписями на оси Y без удаления
        if hasattr(ax, 'get_yticklabels'):
            y_labels = ax.get_yticklabels()
            if len(y_labels) > 8:
                plt.setp(y_labels, fontsize=11)  # Уменьшаем размер при большом количестве
            else:
                plt.setp(y_labels, fontsize=12)  # Увеличиваем для меньшего количества
                
        # Увеличиваем отступ названия графика
        if ax.get_title():
            ax.set_title(ax.get_title(), pad=15, fontsize=18, fontweight='bold')
            
        # Настраиваем сетку, если она есть
        if ax.get_xgridlines() or ax.get_ygridlines():
            ax.grid(True, linestyle='--', alpha=0.5, linewidth=0.3)

# Проверка наличия seaborn
try:
    import seaborn as sns
    # Настраиваем стиль seaborn
    sns.set_style("whitegrid", {'grid.linestyle': '--', 'grid.alpha': 0.3, 'grid.linewidth': 0.3})
except ImportError:
    # Если seaborn не установлен, создаем улучшенную "заглушку" для heatmap
    class MockSeaborn:
        def heatmap(self, data, **kwargs):
            fig = plt.figure(figsize=(10, max(4, data.shape[0] * 0.5)))  # Динамический размер для heatmap
            plt.imshow(data, aspect='auto', cmap='YlGnBu')
            if 'annot' in kwargs and kwargs['annot']:
                height, width = data.shape
                for i in range(height):
                    for j in range(width):
                        # Устанавливаем минимальный размер шрифта 10
                        fontsize = 11 if height * width < 100 else 10
                        plt.text(j, i, str(data[i, j]), 
                                 ha="center", va="center", 
                                 fontsize=fontsize)
            if 'xticklabels' in kwargs:
                # Адаптивное вращение подписей в зависимости от их количества
                x_labels = kwargs['xticklabels']
                plt.xticks(range(len(x_labels)), x_labels)
                if len(x_labels) > 4:
                    plt.xticks(rotation=30, ha='right', fontsize=12)
                else:
                    plt.xticks(fontsize=12)
            if 'yticklabels' in kwargs:
                y_labels = kwargs['yticklabels']
                plt.yticks(range(len(y_labels)), y_labels, fontsize=12)
            plt.colorbar(label='Значения', fraction=0.046, pad=0.04)
            plt.tight_layout(pad=1.5)  # Больший отступ
            return plt.gca()
    sns = MockSeaborn()

# Функция для настройки круговых диаграмм
def improve_pie_chart():
    fig = plt.gcf()
    for ax in fig.axes:
        # Проверяем, является ли текущая ось круговой диаграммой
        if hasattr(ax, 'patches') and ax.patches:
            # Устанавливаем меньшую толщину линий для всех сегментов
            for patch in ax.patches:
                patch.set_linewidth(0.3)
                patch.set_edgecolor('#888888')  # Светло-серый цвет границ
            
            # Проверяем существование текста для легенды
            if hasattr(ax, 'texts') and ax.texts:
                # Делаем текст процентов более читаемым
                for text in ax.texts:
                    if '%' in text.get_text():  # Это текст с процентами
                        text.set_fontsize(11)
            
            # Если есть легенда, настраиваем её
            if ax.get_legend():
                legend = ax.get_legend()
                legend.set_frame_on(False)  # Убираем рамку
                # Увеличиваем размер текста в легенде
                for text in legend.get_texts():
                    text.set_fontsize(12)
"""
        
        # Модифицируем код: убираем plt.show() и добавляем сохранение
        modified_code += code.replace("plt.show()", "")
        
        # Добавляем улучшения для круговой диаграммы
        if "plt.pie" in modified_code:
            improved_save = """
# Применяем улучшения для круговой диаграммы
improve_pie_chart()
"""
        else:
            improved_save = ""
            
        if "plt.savefig" not in modified_code:
            modified_code += improved_save
            modified_code += "\n# Улучшаем компоновку перед сохранением"
            modified_code += "\nimprove_layout()"
            modified_code += "\nplt.tight_layout(pad=1.5)"  # Увеличиваем отступ
            modified_code += f"\nplt.savefig('{output_path}', bbox_inches='tight', dpi=150)"  # Увеличиваем DPI
        else:
            # Если в коде уже есть сохранение, добавляем улучшение компоновки перед ним
            save_index = modified_code.find("plt.savefig")
            if save_index > 0:
                modified_code = modified_code[:save_index] + improved_save + "\n# Улучшаем компоновку перед сохранением\nimprove_layout()\nplt.tight_layout(pad=1.5)\n" + modified_code[save_index:]
                # Заменяем параметры в существующем plt.savefig
                modified_code = modified_code.replace("plt.savefig(", "plt.savefig(bbox_inches='tight', dpi=150, ")
                
        modified_code += "\nplt.close('all')"
        
        # Выполняем код
        exec(modified_code)
        
        # Проверяем, был ли создан файл и имеет ли он ненулевой размер
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            print("Изображение не было создано или имеет нулевой размер")
            return False
    except Exception as e:
        print(f"Ошибка при выполнении кода для диаграммы: {e}")
        return False

def generate_pdf_from_response(response_file, chart_file=None, output_pdf=None):
    """Создает PDF с текстом и диаграммой из файла ответа"""
    if not os.path.exists(response_file):
        print(f"Файл ответа не найден: {response_file}")
        return False
    
    try:
        # Загружаем ответ
        with open(response_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Получаем описание (текст до блока кода)
        if '```python' in content:
            description = content.split('```python')[0].strip()
            
            # Если есть текст после блока кода, добавляем его к описанию
            after_code = ""
            if '```\n' in content:
                parts = content.split('```\n', 1)
                if len(parts) > 1:
                    after_code = parts[1].strip()
            
            if after_code:
                description += "\n\n" + after_code
        else:
            description = content.strip()
        
        # Определяем имя выходного PDF-файла, если не указано
        if not output_pdf:
            pdf_dir = "pdf_reports"
            os.makedirs(pdf_dir, exist_ok=True)
            output_pdf = os.path.join(pdf_dir, f"{os.path.splitext(os.path.basename(response_file))[0]}.pdf")
        
        # Создаем директорию для выходного файла, если её нет
        output_dir = os.path.dirname(output_pdf)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Проверяем наличие шрифта
        font_path = 'DejaVuSansCondensed.ttf'
        if not os.path.exists(font_path):
            print(f"Шрифт {font_path} не найден. Скачайте его для поддержки кириллицы.")
            return False
        
        # Создаем PDF
        pdf = PDF()
        pdf.add_font('DejaVu', '', font_path, uni=True)
        pdf.add_page()
        
        # Добавляем описание
        pdf.chapter_body(description)
        
        # Добавляем изображение, если оно есть
        if chart_file and os.path.exists(chart_file) and os.path.getsize(chart_file) > 0:
            try:
                pdf.image(chart_file, x=10, w=180)
                print(f"Изображение добавлено в PDF: {chart_file}")
            except Exception as e:
                print(f"Ошибка при добавлении изображения в PDF: {e}")
        
        # Сохраняем PDF
        pdf.output(output_pdf)
        return True
        
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
        return False

def merge_pdf_reports(output_filename=None, source_dir='pdf_reports'):
    """
    Объединяет все PDF-файлы из указанной директории в один файл
    
    Args:
        output_filename (str): Имя результирующего файла (без расширения)
        source_dir (str): Директория с PDF-файлами для объединения
    
    Returns:
        bool: Успешность операции
    """
    try:
        from PyPDF2 import PdfMerger
        import glob
        
        # Проверяем наличие директории с отчетами
        if not os.path.exists(source_dir):
            print(f"Директория {source_dir} не найдена")
            return False
        
        # Получаем список PDF-файлов в директории
        pdf_files = sorted(glob.glob(os.path.join(source_dir, "*.pdf")))
        
        if not pdf_files:
            print(f"В директории {source_dir} не найдено PDF-файлов для объединения")
            return False
        
        # Если имя выходного файла не указано, используем 'merged_report'
        if not output_filename:
            output_filename = 'merged_report'
        
        # Добавляем расширение .pdf, если его нет
        if not output_filename.lower().endswith('.pdf'):
            output_filename += '.pdf'
        
        # Создаем объект для объединения PDF
        merger = PdfMerger()
        
        # Добавляем все PDF-файлы
        for pdf in pdf_files:
            try:
                merger.append(pdf)
                print(f"Добавлен файл: {pdf}")
            except Exception as e:
                print(f"Ошибка при добавлении файла {pdf}: {e}")
        
        # Сохраняем объединенный файл
        merger.write(output_filename)
        merger.close()
        
        print(f"Объединенный PDF-отчет сохранен: {output_filename}")
        return True
        
    except ImportError:
        print("Для объединения PDF требуется установить PyPDF2: pip install PyPDF2")
        return False
    except Exception as e:
        print(f"Ошибка при объединении PDF-файлов: {e}")
        return False

if __name__ == "__main__":
    # Для тестирования
    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        chart_file = sys.argv[2] if len(sys.argv) > 2 else None
        output_pdf = sys.argv[3] if len(sys.argv) > 3 else None
        generate_pdf_from_response(input_file, chart_file, output_pdf)
    else:
        print("Использование: python pdf_generator.py <input_file> [chart_file] [output_pdf]")