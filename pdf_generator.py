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
        self.add_font('DejaVu', 'B', 'DejaVuSansCondensed.ttf', uni=True)
        # Устанавливаем отступы
        self.set_margins(15, 15, 15)
        
    def chapter_title(self, title):
        self.set_font('DejaVu', 'B', 16)
        self.set_text_color(44, 44, 44)  # Тёмно-серый цвет для заголовков
        self.cell(0, 10, title, 0, 1, 'C')
        self.ln(5)  # Уменьшенный отступ после заголовка
        
    def chapter_body(self, text):
        self.set_font('DejaVu', '', 12)
        self.set_text_color(0, 0, 0)  # Черный текст для основного содержания
        self.multi_cell(0, 7, text)  # Немного уменьшенный межстрочный интервал
        self.ln(5)  # Отступ после текста

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
        
        # Подготавливаем код с необходимыми импортами и улучшениями
        modified_code = """
import matplotlib
matplotlib.use('Agg')  # Не-интерактивный режим
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors

# Улучшения для диаграмм
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 12

# Профессиональная цветовая палитра
colors = ['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000', '#5B9BD5', '#70AD47']

# Проверка наличия seaborn
try:
    import seaborn as sns
except ImportError:
    # Если seaborn не установлен, создаем "заглушку" для heatmap
    class MockSeaborn:
        def heatmap(self, data, **kwargs):
            plt.figure(figsize=(8, 4))
            plt.imshow(data, aspect='auto', cmap='coolwarm')
            # Добавляем сетку для тепловой карты
            for i in range(data.shape[0]+1):
                plt.axhline(i-0.5, color='white', lw=1)
            for i in range(data.shape[1]+1):
                plt.axvline(i-0.5, color='white', lw=1)
            if 'annot' in kwargs and kwargs['annot']:
                height, width = data.shape
                for i in range(height):
                    for j in range(width):
                        plt.text(j, i, str(data[i, j]), 
                                ha="center", va="center")
            if 'xticklabels' in kwargs:
                plt.xticks(range(len(kwargs['xticklabels'])), kwargs['xticklabels'])
            if 'yticklabels' in kwargs:
                plt.yticks(range(len(kwargs['yticklabels'])), kwargs['yticklabels'])
            plt.colorbar(label='Значения')
            return plt.gca()
        
        def boxplot(self, data=None, **kwargs):
            # Убедимся, что данные правильного формата
            if isinstance(data, list) and not isinstance(data[0], list):
                data = [[x] for x in data]
            fig = plt.figure(figsize=(8, 6))
            ax = plt.boxplot(data, **kwargs)
            # Добавляем сетку для box plot
            plt.grid(True, linestyle='--', alpha=0.7, axis='y')
            return ax
            
    sns = MockSeaborn()

# Функция для автоматического добавления сетки к диаграммам
def enhance_chart(ax=None):
    if ax is None:
        ax = plt.gca()
    # Добавляем сетку
    ax.grid(True, linestyle='--', alpha=0.7, color='gray', zorder=0)
    # Улучшаем оси
    ax.spines['bottom'].set_linewidth(1.5)
    ax.spines['left'].set_linewidth(1.5)
    return ax

# Установка стиля по умолчанию
plt.style.use('seaborn-v0_8-whitegrid')
"""
        
        # Вставляем оригинальный код
        modified_code += code.replace("plt.show()", "")
        
        # Добавляем автоматическое добавление сетки, если её нет в коде
        if "plt.grid" not in modified_code and "ax.grid" not in modified_code:
            modified_code += "\n# Автоматически добавляем сетку\nenhance_chart()"
        
        # Добавляем сохранение, если оно отсутствует
        if "plt.savefig" not in modified_code:
            modified_code += f"\nplt.savefig('{output_path}', bbox_inches='tight', dpi=300)"
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
                # Улучшенное отображение изображения - центрирование и оптимальный размер
                img_width = 180  # 180мм - почти вся ширина A4
                pdf.image(chart_file, x=(210-img_width)/2, w=img_width)  # Центрирование
                print(f"Изображение добавлено в PDF: {chart_file}")
            except Exception as e:
                print(f"Ошибка при добавлении изображения в PDF: {e}")
        
        # Сохраняем PDF
        pdf.output(output_pdf)
        return True
        
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
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