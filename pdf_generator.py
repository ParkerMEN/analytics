import os
import re
import tempfile
import matplotlib.pyplot as plt
from fpdf import FPDF

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
        self.multi_cell(0, 5, text)
        self.ln()

def extract_description_and_code(response_file):
    """Извлекает описание и код Python из файла ответа"""
    with open(response_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Извлекаем Python-код
    code_match = re.search(r'```python\s*(.*?)\s*```', content, re.DOTALL)
    if not code_match:
        # Если код не найден в формате ```python, ищем просто код между ```
        code_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if not code_match:
            return content, ""  # Возвращаем весь контент как описание
    
    code = code_match.group(1).strip()
    
    # Получаем описание, удаляя блок кода
    description = content.replace(f"```python\n{code}\n```", "").replace(f"```\n{code}\n```", "").strip()
    
    return description, code

def generate_pdf_with_plot(response_file, output_pdf):
    """Создает PDF-документ с описанием и диаграммой"""
    description, code = extract_description_and_code(response_file)
    
    if not code:
        print(f"В файле {response_file} не найден код Python для диаграммы.")
        # Если кода нет, создаем PDF только с описанием
        if description:
            try:
                # Проверяем наличие шрифта
                font_path = 'DejaVuSansCondensed.ttf'
                if not os.path.exists(font_path):
                    print(f"Шрифт {font_path} не найден. Скачайте его для поддержки кириллицы.")
                    return False
                
                pdf = PDF()
                pdf.add_page()
                pdf.chapter_body(description)
                pdf.output(output_pdf)
                return True
            except Exception as e:
                print(f"Ошибка при создании PDF только с описанием: {e}")
                return False
        return False
    
    # Создаем временный файл для сохранения диаграммы
    temp_dir = tempfile.gettempdir()
    tmp_img_path = os.path.join(temp_dir, "temp_plot.png")
    
    # Модифицируем код для сохранения диаграммы вместо отображения
    modified_code = code.replace('plt.show()', f'plt.savefig(r"{tmp_img_path}", dpi=300, bbox_inches="tight")')
    if 'plt.show()' not in code:
        # Если plt.show() не найден, добавляем сохранение диаграммы
        modified_code += f'\nplt.savefig(r"{tmp_img_path}", dpi=300, bbox_inches="tight")'
    
    # Выполняем код для создания диаграммы
    try:
        # Добавляем импорт matplotlib, если его нет в коде
        if 'import matplotlib.pyplot as plt' not in modified_code:
            modified_code = 'import matplotlib.pyplot as plt\n' + modified_code
            
        # Выполняем код с безопасными путями
        exec(modified_code)
        
        if not os.path.exists(tmp_img_path):
            print(f"Диаграмма не была создана по пути: {tmp_img_path}")
            return False
            
    except Exception as e:
        print(f"Ошибка при выполнении кода: {e}")
        return False
    
    # Создаем PDF с использованием FPDF и шрифта с поддержкой кириллицы
    try:
        # Проверяем наличие шрифта
        font_path = 'DejaVuSansCondensed.ttf'
        if not os.path.exists(font_path):
            print(f"Шрифт {font_path} не найден. Скачайте его для поддержки кириллицы.")
            return False
        
        pdf = PDF()
        pdf.add_page()
        
        # Добавляем описание
        if description:
            pdf.chapter_body(description)
        
        # Добавляем диаграмму, если она была создана
        if os.path.exists(tmp_img_path):
            pdf.image(tmp_img_path, x=10, w=180)
        
        # Сохраняем PDF
        pdf.output(output_pdf)
        
        # Удаляем временный файл
        if os.path.exists(tmp_img_path):
            os.remove(tmp_img_path)
        
        return True
        
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
        return False

if __name__ == "__main__":
    # Для тестирования
    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "output.pdf"
        generate_pdf_with_plot(input_file, output_file)
    else:
        print("Использование: python pdf_generator.py <input_file> [output_file]")