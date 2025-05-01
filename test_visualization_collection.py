import logging
import os
import glob
import re
import shutil
from bs4 import BeautifulSoup
import markdown
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("visualization_collection_test.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_visualization_collection")

class VisualizationCollectionTester:
    """Тестер для проверки сбора визуализаций."""

    def __init__(self, visualizations_dir="analytics_output/visualizations"):
        self.visualizations_dir = visualizations_dir
        self.visualization_images = []
        self.logger = logging.getLogger("VisualizationCollectionTester")
        
    async def _run_visualization_scripts_async(self):
        """Асинхронно запускает скрипты для создания визуализаций."""
        script_files = glob.glob(os.path.join(self.visualizations_dir, "code", "*.py"))
        self.logger.info(f"Найдено {len(script_files)} скриптов визуализаций для асинхронного запуска")
        
        import subprocess
        import sys
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # Функция для запуска одного скрипта
        async def run_script(script):
            self.logger.info(f"Запуск скрипта: {script}")
            try:
                # Используем ThreadPoolExecutor для выполнения блокирующих операций
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    # Запускаем скрипт асинхронно
                    process = await loop.run_in_executor(
                        executor,
                        lambda: subprocess.run(
                            [sys.executable, script],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                    )
                    
                    if process.returncode == 0:
                        self.logger.info(f"Скрипт выполнен успешно: {script}")
                        if process.stdout and len(process.stdout.strip()) > 0:
                            self.logger.debug(f"Вывод скрипта: {process.stdout[:500]}...")
                    else:
                        error_msg = process.stderr if process.stderr else "Нет информации об ошибке"
                        # Обрабатываем ошибки kaleido отдельно - они не критичны, если нам нужны только HTML
                        if "kaleido" in error_msg:
                            self.logger.warning(f"Предупреждение при выполнении {script}: Не удалось создать PNG (отсутствует kaleido)")
                        else:
                            self.logger.error(f"Ошибка при выполнении скрипта {script}. Код возврата: {process.returncode}")
                            self.logger.error(f"Ошибка: {error_msg}")
                    
                return script
            except Exception as e:
                self.logger.error(f"Ошибка при запуске скрипта {script}: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                return None
        
        # Запускаем все скрипты асинхронно и ждем завершения
        tasks = [run_script(script) for script in script_files]
        results = await asyncio.gather(*tasks)
        
        # Проверяем созданные файлы
        successful_scripts = [r for r in results if r]
        self.logger.info(f"Успешно выполнено {len(successful_scripts)} из {len(script_files)} скриптов")
        
        # Проверяем созданные визуализации после выполнения всех скриптов
        for script_path in successful_scripts:
            script_basename = os.path.basename(script_path).replace(".py", "")
            html_found = False
            png_found = False
            
            # Ищем созданные HTML и PNG файлы в разных местах
            for search_dir in [self.visualizations_dir, os.path.join(self.visualizations_dir, "output")]:
                if os.path.exists(search_dir):
                    # Проверяем HTML
                    html_files = glob.glob(os.path.join(search_dir, f"*{script_basename}*.html"))
                    html_files.extend(glob.glob(os.path.join(search_dir, "viz_*.html")))
                    if html_files:
                        self.logger.info(f"Скрипт {script_basename} создал HTML файлы: {[os.path.basename(f) for f in html_files]}")
                        html_found = True
                    
                    # Проверяем PNG
                    png_files = glob.glob(os.path.join(search_dir, f"*{script_basename}*.png"))
                    png_files.extend(glob.glob(os.path.join(search_dir, "viz_*.png")))
                    if png_files:
                        self.logger.info(f"Скрипт {script_basename} создал PNG файлы: {[os.path.basename(f) for f in png_files]}")
                        png_found = True
            
            if not html_found and not png_found:
                self.logger.warning(f"Скрипт {script_basename} выполнен, но визуализации не найдены")
        
    def _run_visualization_scripts(self):
        try:
            import asyncio
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Если цикла событий нет, создаем новый
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._run_visualization_scripts_async())

    def _normalize_html_files(self, html_files):
        """Нормализует HTML-файлы для правильной работы с CDN Plotly."""
        self.logger.info(f"Нормализация {len(html_files)} HTML-файлов")
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                modified = False
                
                # Проверяем наличие Plotly, но отсутствие CDN
                if 'PlotlyConfig' in content and 'cdn.plot.ly' not in content:
                    self.logger.info(f"Модифицируем {os.path.basename(html_file)} для использования CDN")
                    
                    # Находим <head> и добавляем CDN
                    if '<head>' in content and 'plotly-latest.min.js' not in content:
                        modified_content = content.replace(
                            '<head>',
                            '<head>\n<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
                        )
                        modified = True
                    # Если нет <head>, но есть window.PlotlyConfig
                    elif '<script type="text/javascript">window.PlotlyConfig' in content:
                        modified_content = content.replace(
                            '<script type="text/javascript">window.PlotlyConfig',
                            '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>\n<script type="text/javascript">window.PlotlyConfig'
                        )
                        modified = True
                
                # Проверяем, есть ли закрывающий тег body и html
                if '</body>' not in content:
                    if modified:
                        modified_content += '\n</body>'
                    else:
                        modified_content = content + '\n</body>'
                        modified = True
                        
                if '</html>' not in content:
                    if modified:
                        modified_content += '\n</html>'
                    else:
                        modified_content = content + '\n</html>'
                        modified = True
                
                # Сохраняем модифицированную версию
                if modified:
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    self.logger.info(f"HTML-файл {os.path.basename(html_file)} успешно нормализован")
                    
            except Exception as e:
                self.logger.warning(f"Ошибка при нормализации файла {os.path.basename(html_file)}: {str(e)}")

    def _extract_visualization_info(self, report_file):
        """Извлекает информацию о визуализации из отчета."""
        try:
            self.logger.debug(f"Извлечение информации из отчета: {report_file}")
            
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            info = {
                'title': '',
                'type': '',
                'description': '',
                'insights': '',
                'image_path': '',
                'html_path': '',
                'is_interactive': False
            }
            
            # Извлекаем заголовок
            title_match = re.search(r'# (.*?)$', content, re.MULTILINE)
            if title_match:
                info['title'] = title_match.group(1).strip()
                self.logger.debug(f"Извлечен заголовок: {info['title']}")
            else:
                # Если заголовка нет, используем имя файла
                base_name = os.path.basename(report_file).replace('report_', '').replace('.md', '')
                viz_match = re.search(r'(\d+)_(.+)', base_name)
                if viz_match:
                    viz_num = viz_match.group(1)
                    viz_name = viz_match.group(2).replace('_', ' ')
                    info['title'] = f"Визуализация {viz_num}: {viz_name}"
                else:
                    info['title'] = f"Визуализация {base_name}"
                self.logger.debug(f"Заголовок не найден, используем: {info['title']}")
            
            # Извлекаем тип визуализации
            type_match = re.search(r'## Тип визуализации\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
            if type_match:
                info['type'] = type_match.group(1).strip()
                self.logger.debug(f"Извлечен тип: {info['type']}")
            
            # Извлекаем описание
            desc_match = re.search(r'## Описание\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
            if desc_match:
                info['description'] = desc_match.group(1).strip()
                self.logger.debug(f"Извлечено описание, длина: {len(info['description'])}")
            
            # Извлекаем инсайты (с различными вариантами заголовка)
            insights_match = re.search(r'## (?:Ожидаемые )?[Ии]нсайты\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
            if insights_match:
                info['insights'] = insights_match.group(1).strip()
                self.logger.debug(f"Извлечены инсайты, длина: {len(info['insights'])}")
            
            return info
                
        except Exception as e:
            self.logger.error(f"Ошибка при обработке файла {report_file}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def _find_template_file(self):
        """Ищет шаблон отчета в нескольких местах."""
        possible_locations = [
            self.template_file,                        # Стандартное местоположение
            os.path.join(os.getcwd(), "analytics_report.html"),  # В корне проекта
            os.path.join(os.path.dirname(os.getcwd()), "analytics_report.html"),  # Уровнем выше
            os.path.join(os.path.dirname(self.output_file), "analytics_report.html")  # В папке с отчетом
        ]
        
        for location in possible_locations:
            self.logger.debug(f"Проверка наличия шаблона в: {location}")
            if os.path.exists(location):
                self.logger.info(f"Найден шаблон отчета: {location}")
                return location
        
        self.logger.warning("Шаблон отчета не найден. Будет создан базовый шаблон.")
        return None

    async def generate_analysis_report_async(self):
        """Асинхронно генерирует аналитический отчет."""
        self.logger.info("Начинаем генерацию аналитического отчета...")
        
        # Сначала собираем все визуализации
        self.visualizations = self.collect_visualizations()
        
        # Количество найденных визуализаций
        viz_count = len(self.visualizations)
        self.logger.info(f"Найдено {viz_count} визуализаций для отчета")
        
        # Загружаем шаблон отчета
        template_path = "analytics_report.html"
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_html = f.read()
            self.logger.info(f"Загружен шаблон отчета из {template_path}")
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке шаблона отчета: {e}")
            return None
        
        # Заменяем плейсхолдеры актуальными данными
        from datetime import datetime
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        report_html = template_html.replace("ТЕКУЩАЯ_ДАТА", current_date)
        report_html = report_html.replace("КОЛИЧЕСТВО_ВИЗУАЛИЗАЦИЙ", str(viz_count))
        
        # Генерируем HTML-код для визуализаций
        visualizations_html = ""
        for viz_info in self.visualizations:
            viz_html = self._generate_visualization_card(viz_info)
            visualizations_html += viz_html
        
        # Вставляем визуализации в отчет
        report_html = report_html.replace("<!-- Здесь будут размещаться визуализации -->", visualizations_html)
        
        # Сохраняем финальный отчет
        output_dir = "analytics_output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "visualization_report.html")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_html)
            self.logger.info(f"Аналитический отчет сохранен: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении аналитического отчета: {e}")
            return None

    def _generate_visualization_card(self, viz_info):
        """Создает HTML-карточку для одной визуализации."""
        title = viz_info.get('title', 'Без названия')
        html_path = viz_info.get('html_path', '')
        image_path = viz_info.get('image_path', '')
        
        # Относительный путь для включения в отчет
        if html_path:
            relative_path = os.path.basename(html_path)
        elif image_path:
            relative_path = os.path.basename(image_path)
        else:
            return ""
        
        # Создаем HTML для карточки визуализации
        viz_type = "Интерактивная визуализация" if html_path else "Статическая визуализация"
        
        card_html = f"""
<div class="visualization-card" data-rating="{viz_info.get('rating', '')}" data-title="{title}" data-topics="{','.join(viz_info.get('topics', []))}">
<div class="visualization-header">
<h3>
   {title}
  </h3>
<div class="visualization-type">
   Тип: {viz_type}
  </div>
</div>
<div class="visualization-content">
"""
        
        if html_path:
            card_html += f'<iframe class="plotly-iframe" src="{relative_path}">\n</iframe>\n'
        elif image_path:
            card_html += f'<img src="{relative_path}" alt="{title}">\n'
            
        card_html += """</div>
<div class="visualization-insights">
<h4>
   Ключевые выводы
  </h4>
<p>
   """ + viz_info.get('description', 'Нет описания') + """
  </p>
</div>
</div>
"""
        
        return card_html

    def generate_analysis_report(self):
        """Обертка для асинхронной функции, чтобы сохранить совместимость кода."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Если цикла событий нет, создаем новый
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self.generate_analysis_report_async())

    def collect_visualizations(self):
        """Собирает информацию о всех визуализациях."""
        self.logger.info("Начало сбора информации о визуализациях...")
        
        # Получение списка всех отчетов о визуализациях
        report_files = glob.glob(os.path.join(self.visualizations_dir, "reports", "*.md"))
        self.logger.info(f"Найдено {len(report_files)} отчетов о визуализациях")
        
        # Поиск файлов визуализаций во всех возможных местах
        # Этот метод находит все возможные файлы визуализаций и записывает их в переменные
        image_files = []
        html_files = []
        
        # 1. Поиск файлов в корневой директории
        for ext in ['png', 'jpg', 'jpeg', 'svg', 'html']:
            pattern = os.path.join(self.visualizations_dir, f"*.{ext}")
            found_files = glob.glob(pattern)
            self.logger.debug(f"Найдено {len(found_files)} файлов по паттерну {pattern}")
            if ext == 'html':
                html_files.extend(found_files)
            else:
                image_files.extend(found_files)
        
        # 2. Поиск во всех поддиректориях
        for subdir in ["output", "images", "plots", ""]:
            search_dir = os.path.join(self.visualizations_dir, subdir)
            if os.path.exists(search_dir):
                for ext in ['png', 'jpg', 'jpeg', 'svg', 'html']:
                    pattern = os.path.join(search_dir, f"viz_*.{ext}")
                    found_files = glob.glob(pattern)
                    if found_files:
                        self.logger.debug(f"Найдено {len(found_files)} файлов по паттерну {pattern}")
                        if ext == 'html':
                            html_files.extend(found_files)
                        else:
                            image_files.extend(found_files)
        
        # Удаляем дубликаты
        image_files = list(set(image_files))
        html_files = list(set(html_files))
        
        self.logger.info(f"Найдено уникальных файлов: {len(image_files)} изображений и {len(html_files)} HTML")
        
        # Нормализация HTML-файлов для использования CDN Plotly
        self._normalize_html_files(html_files)
        
        # Если файлов визуализаций нет, запускаем скрипты
        if not image_files and not html_files:
            self.logger.info("Визуализации не найдены. Запускаем скрипты для их создания...")
            self._run_visualization_scripts()
            
            # Повторный поиск после запуска скриптов
            self.logger.info("Повторный поиск файлов после запуска скриптов...")
            return self.collect_visualizations()  # Рекурсивный вызов для поиска
        
        # Сопоставление отчетов с визуализациями
        self.visualization_images = []
        
        # Строим карту соответствия отчет -> визуализация
        viz_map = {}
        
        # Для каждого отчета
        for report_file in report_files:
            report_basename = os.path.basename(report_file)
            # Извлекаем номер визуализации, если возможно
            viz_number_match = re.search(r'report_(\d+)_', report_basename)
            viz_number = viz_number_match.group(1) if viz_number_match else None
            
            # Извлекаем метаданные из отчета
            viz_info = self._extract_visualization_info(report_file)
            
            # Если номер извлечен, ищем соответствующие файлы
            if viz_number:
                # Формируем список возможных базовых имен
                possible_basenames = [
                    f"viz_{viz_number}_",
                    f"viz_Визуализация {viz_number}",
                    f"viz_Визуализация{viz_number}",
                    f"viz_{viz_number}",
                    "viz_"
                ]
                
                # Ищем HTML первым приоритетом
                html_found = False
                for html_file in html_files:
                    html_basename = os.path.basename(html_file)
                    if any(basename in html_basename for basename in possible_basenames):
                        viz_info['html_path'] = html_file
                        viz_info['is_interactive'] = True
                        html_found = True
                        self.logger.info(f"Для визуализации #{viz_number} ({viz_info['title']}) найден HTML: {html_basename}")
                        break
                
                # Если HTML не найден по номеру, ищем по ключевым словам из названия
                if not html_found and 'title' in viz_info:
                    title_words = re.sub(r'[^\w\s]', '', viz_info['title'].lower()).split()
                    significant_words = [w for w in title_words if len(w) > 3]  # Только слова длиннее 3 символов
                    
                    for html_file in html_files:
                        html_basename = os.path.basename(html_file).lower()
                        if any(word in html_basename for word in significant_words):
                            viz_info['html_path'] = html_file
                            viz_info['is_interactive'] = True
                            html_found = True
                            self.logger.info(f"Для визуализации #{viz_number} ({viz_info['title']}) найден HTML по ключевым словам: {html_basename}")
                            break
                
                # Если HTML все еще не найден, берем последнюю попытку - проверяем неразобранные HTML
                if not html_found:
                    for html_file in html_files:
                        if 'Визуализация' in os.path.basename(html_file):
                            viz_info['html_path'] = html_file
                            viz_info['is_interactive'] = True
                            html_found = True
                            self.logger.info(f"Для визуализации #{viz_number} ({viz_info['title']}) назначен HTML: {os.path.basename(html_file)}")
                            # Удаляем использованный файл из списка доступных
                            html_files.remove(html_file)
                            break
                
                # Аналогичный подход для изображений
                image_found = False
                for img_file in image_files:
                    img_basename = os.path.basename(img_file)
                    if any(basename in img_basename for basename in possible_basenames):
                        viz_info['image_path'] = img_file
                        image_found = True
                        self.logger.info(f"Для визуализации #{viz_number} ({viz_info['title']}) найдено изображение: {img_basename}")
                        break
                
                # Добавляем визуализацию, если найден хотя бы один файл
                if html_found or image_found:
                    self.visualization_images.append(viz_info)
                else:
                    self.logger.warning(f"Не найдены файлы для визуализации #{viz_number} ({viz_info['title']})")
            else:
                # Если номер не извлечен, используем базовую информацию из отчета
                self.logger.warning(f"Не удалось извлечь номер визуализации из {report_basename}")
                if 'title' in viz_info:
                    # Пытаемся найти подходящие файлы по ключевым словам из названия
                    title_words = re.sub(r'[^\w\s]', '', viz_info['title'].lower()).split()
                    significant_words = [w for w in title_words if len(w) > 3]
                    
                    for html_file in html_files:
                        html_basename = os.path.basename(html_file).lower()
                        if any(word in html_basename for word in significant_words):
                            viz_info['html_path'] = html_file
                            viz_info['is_interactive'] = True
                            self.logger.info(f"Для визуализации [{viz_info['title']}] найден HTML: {html_basename}")
                            # Удаляем из доступных
                            html_files.remove(html_file)
                            break
                    
                    if 'html_path' in viz_info:
                        self.visualization_images.append(viz_info)
        
        # Проверяем неиспользованные HTML-файлы и добавляем их как дополнительные визуализации
        for html_file in html_files:
            html_basename = os.path.basename(html_file)
            self.logger.info(f"Добавление неиспользованного HTML: {html_basename}")
            
            # Создаем базовую визуализацию для неразобранного HTML
            viz_info = {
                'title': f"Визуализация {html_basename}",
                'type': 'Интерактивная визуализация',
                'description': f"Автоматически добавленная визуализация",
                'insights': 'Информация отсутствует',
                'html_path': html_file,
                'is_interactive': True
            }
            
            self.visualization_images.append(viz_info)
        
        if len(self.visualization_images) > 0:
            self.logger.info(f"Успешно добавлено {len(self.visualization_images)} визуализаций")
            return True
        else:
            self.logger.warning("Не удалось найти визуализации")
            return False

def main():
    """Основная функция для тестирования сбора визуализаций."""
    logger.info("Запуск тестирования сбора визуализаций...")
    
    # Создание экземпляра тестера
    tester = VisualizationCollectionTester()
    
    # Запуск сбора визуализаций
    if tester.collect_visualizations():
        logger.info("Тест успешно выполнен, визуализации собраны!")
        logger.info(f"Всего найдено визуализаций: {len(tester.visualization_images)}")
    else:
        logger.error("Тест не удался, визуализации не собраны.")

if __name__ == "__main__":
    main()