import os
import sys
import re
import json
import logging
import tempfile
import subprocess
import traceback
import time
import asyncio  # Добавляем импорт asyncio
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Импортируем GPTScriptFixerAgent
from gpt_script_fixer import GPTScriptFixerAgent

class VisualizationExecutionAgent:
    """
    Агент для выполнения скриптов визуализаций и обеспечения правильного именования файлов.
    Транслитерирует кириллические символы в латиницу в именах файлов.
    При обнаружении ошибок автоматически исправляет скрипты с помощью GPT.
    Поддерживает асинхронное выполнение для ускорения процесса.
    """
    
    def __init__(self, 
                 code_dir: str = "analytics_output/visualizations/code", 
                 output_dir: str = "analytics_output/visualizations",
                 metadata_file: str = "analytics_output/visualizations_metadata.json",
                 api_key: Optional[str] = None,
                 max_concurrent: int = 3):
        self.code_dir = code_dir
        self.output_dir = output_dir
        self.metadata_file = metadata_file
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.max_concurrent = max_concurrent
        
        # Настройка логирования
        self.logger = logging.getLogger('VisualizationExecutionAgent')
        self.logger.propagate = False  # Добавить эту строку
        self.logger.setLevel(logging.INFO)
        
        # Проверяем, добавлены ли уже обработчики к логгеру
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(console_handler)
            
            file_handler = logging.FileHandler("visualization_execution.log", encoding="utf-8")
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
        
        # Создаем директории, если они не существуют
        os.makedirs(self.code_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Создаем директорию для логов ошибок
        self.error_logs_dir = os.path.join(self.output_dir, "error_logs")
        os.makedirs(self.error_logs_dir, exist_ok=True)
        
        # Инициализируем GPTScriptFixerAgent, если указан API-ключ
        if self.api_key:
            self.script_fixer = GPTScriptFixerAgent(
                api_key=self.api_key,
                error_logs_dir=self.error_logs_dir,
                code_dir=self.code_dir
            )
        else:
            self.script_fixer = None
            self.logger.warning("API ключ не указан. GPTScriptFixerAgent не будет использоваться.")
    
    def transliterate(self, text: str) -> str:
        """
        Транслитерация кириллических символов в латиницу.
        """
        cyrillic_to_latin = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
            'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
        }
        
        result = ""
        for char in text:
            result += cyrillic_to_latin.get(char, char)
            
        result = re.sub(r'[^a-zA-Z0-9_.]', '_', result)
        
        return result
        
    def load_metadata(self) -> List[Dict[str, Any]]:
        """
        Загружает метаданные визуализаций.
        """
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки метаданных: {str(e)}")
                return []
        else:
            self.logger.warning(f"Файл метаданных {self.metadata_file} не найден.")
            return []
        
    def save_metadata(self, metadata: List[Dict[str, Any]]) -> None:
        """
        Сохраняет обновленные метаданные визуализаций.
        """
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Метаданные сохранены в {self.metadata_file}")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения метаданных: {str(e)}")
            
    def get_visualization_files(self) -> List[str]:
        """
        Возвращает список файлов скриптов визуализации.
        """
        files = []
        if os.path.exists(self.code_dir):
            for filename in os.listdir(self.code_dir):
                if filename.endswith('.py') and filename.startswith('viz_'):
                    files.append(os.path.join(self.code_dir, filename))
        return files
        
    def modify_script_paths(self, content: str) -> str:
        """
        Модифицирует содержимое скрипта для использования транслитерированных путей файлов.
        """
        viz_file_pattern = r'([\'\"])(.*?viz_)(.*?)(\.(?:html|png)[\'\"])'
        
        def replace_match(match):
            quote, prefix, name, suffix = match.groups()
            transliterated_name = self.transliterate(name)
            return f"{quote}{prefix}{transliterated_name}{suffix}"
        
        modified_content = re.sub(viz_file_pattern, replace_match, content)
        
        return modified_content
        
    def execute_script(self, script_path: str, retry_after_fix: bool = True) -> bool:
        """
        Синхронная версия выполнения скрипта визуализации.
        
        Args:
            script_path: Путь к скрипту
            retry_after_fix: Повторить после исправления
            
        Returns:
            True если выполнение успешно
        """
        try:
            self.logger.info(f"Выполняется скрипт: {script_path}")
            
            # Читаем содержимое скрипта
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Модифицируем пути для использования транслитерированных имен
            modified_content = self.modify_script_paths(content)
            
            # Создаем временный файл с модифицированным содержимым
            temp_script = tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8')
            temp_script.write(modified_content)
            temp_script_path = temp_script.name
            temp_script.close()
            
            # Выполняем временный скрипт
            result = subprocess.run(
                [sys.executable, temp_script_path],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            # Удаляем временный файл
            os.unlink(temp_script_path)
            
            if result.returncode == 0:
                self.logger.info(f"Успешно выполнен {script_path}")
                return True
            else:
                # Сохраняем подробные логи ошибки для анализа
                error_msg = result.stderr
                script_filename = os.path.basename(script_path)
                error_log_path = os.path.join(self.error_logs_dir, f"{script_filename}.error.log")
                
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write(f"Ошибка выполнения скрипта: {script_path}\n\n")
                    f.write(f"Дата и время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Сообщение об ошибке:\n{error_msg}\n\n")
                    f.write("Модифицированный код:\n")
                    f.write(modified_content)
                
                self.logger.error(f"Ошибка выполнения {script_path}: {error_msg}")
                
                # Если указано повторить после исправления и GPTScriptFixerAgent инициализирован
                if retry_after_fix and hasattr(self, 'script_fixer'):
                    self.logger.info(f"Пытаемся исправить скрипт с помощью GPT: {script_path}")
                    
                    # Пытаемся исправить скрипт с помощью GPT
                    success, fixed_code = self.script_fixer.fix_script_with_gpt(script_path)
                    
                    if success:
                        # Сохраняем исправленный скрипт
                        if self.script_fixer.save_fixed_script(script_path, fixed_code):
                            self.logger.info(f"Скрипт успешно исправлен, повторная попытка выполнения: {script_path}")
                            
                            # Повторно выполняем исправленный скрипт (без повторного исправления)
                            return self.execute_script(script_path, retry_after_fix=False)
                        else:
                            self.logger.error(f"Не удалось сохранить исправленный скрипт: {script_path}")
                    else:
                        self.logger.error(f"Не удалось исправить скрипт с помощью GPT: {script_path}")
                
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка при подготовке скрипта {script_path}: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    async def execute_script_async(self, script_path: str, semaphore: asyncio.Semaphore, 
                                  retry_after_fix: bool = True) -> bool:
        """
        Асинхронно выполняет скрипт визуализации с безопасной обработкой ошибок.
        
        Args:
            script_path: Путь к скрипту визуализации
            semaphore: Семафор для ограничения параллельного выполнения
            retry_after_fix: Повторно выполнить скрипт после исправления (только при первой попытке)
            
        Returns:
            bool: True если скрипт успешно выполнен, иначе False
        """
        async with semaphore:
            try:
                self.logger.info(f"Выполняется скрипт: {script_path}")
                
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                modified_content = self.modify_script_paths(content)
                
                temp_script = tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8')
                temp_script.write(modified_content)
                temp_script_path = temp_script.name
                temp_script.close()
                
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda: subprocess.run(
                        [sys.executable, temp_script_path],
                        capture_output=True,
                        text=True,
                        encoding='utf-8'
                    )
                )
                
                os.unlink(temp_script_path)
                
                if result.returncode == 0:
                    self.logger.info(f"Успешно выполнен {script_path}")
                    if result.stdout:
                        self.logger.debug(f"Вывод: {result.stdout}")
                    return True
                else:
                    error_msg = result.stderr
                    script_filename = os.path.basename(script_path)
                    error_log_path = os.path.join(self.error_logs_dir, f"{script_filename}.error.log")
                    
                    with open(error_log_path, "w", encoding="utf-8") as f:
                        f.write(f"Ошибка выполнения скрипта: {script_path}\n\n")
                        f.write(f"Дата и время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Сообщение об ошибке:\n{error_msg}\n\n")
                        f.write("Модифицированный код:\n")
                        f.write(modified_content)
                    
                    self.logger.error(f"Ошибка выполнения {script_path}: {error_msg}")
                    
                    if retry_after_fix:
                        self.logger.info(f"Пытаемся исправить скрипт с помощью GPT: {script_path}")
                        
                        success, fixed_code = self.script_fixer.fix_script_with_gpt(script_path)
                        
                        if success:
                            if self.script_fixer.save_fixed_script(script_path, fixed_code):
                                self.logger.info(f"Скрипт успешно исправлен, повторная попытка выполнения: {script_path}")
                                return await self.execute_script_async(script_path, semaphore, False)
                            else:
                                self.logger.error(f"Не удалось сохранить исправленный скрипт: {script_path}")
                        else:
                            self.logger.error(f"Не удалось исправить скрипт с помощью GPT: {script_path}")
                    
                    return False
                    
            except Exception as e:
                self.logger.error(f"Ошибка при подготовке скрипта {script_path}: {str(e)}")
                self.logger.error(traceback.format_exc())
                return False
    
    async def process_async(self) -> Dict[str, Any]:
        """
        Асинхронная версия метода process для параллельного выполнения скриптов.
        
        Returns:
            Dict[str, Any]: Результаты процесса
        """
        start_time = time.time()
        results = {
            'total_scripts': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'successful_files': [],
            'failed_files': [],
            'fixed_scripts': []
        }
        
        viz_files = self.get_visualization_files()
        results['total_scripts'] = len(viz_files)
        
        self.logger.info(f"Найдено {len(viz_files)} скриптов визуализации.")
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        tasks = [self.execute_script_async(script_path, semaphore) for script_path in viz_files]
        
        execution_results = await asyncio.gather(*tasks)
        
        for script_path, success in zip(viz_files, execution_results):
            if success:
                results['successful_executions'] += 1
                results['successful_files'].append(script_path)
            else:
                results['failed_executions'] += 1
                results['failed_files'].append(script_path)
        
        metadata = self.load_metadata()
        updated_metadata = self.update_metadata_paths(metadata)
        self.save_metadata(updated_metadata)
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Выполнение завершено за {elapsed_time:.2f} сек: "
                       f"{results['successful_executions']} успешных, "
                       f"{results['failed_executions']} неудачных.")
        return results
    
    def process(self, use_async: bool = True) -> Dict[str, Any]:
        """
        Основной метод обработки для запуска генерации визуализаций.
        
        Args:
            use_async: Использовать ли асинхронное выполнение
            
        Returns:
            Dict[str, Any]: Результаты процесса
        """
        if use_async:
            return asyncio.run(self.process_async())
        else:
            start_time = time.time()
            results = {
                'total_scripts': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'successful_files': [],
                'failed_files': [],
            }
            
            viz_files = self.get_visualization_files()
            results['total_scripts'] = len(viz_files)
            
            self.logger.info(f"Найдено {len(viz_files)} скриптов визуализации.")
            
            for script_path in viz_files:
                if self.execute_script(script_path):
                    results['successful_executions'] += 1
                    results['successful_files'].append(script_path)
                else:
                    results['failed_executions'] += 1
                    results['failed_files'].append(script_path)
                    
            metadata = self.load_metadata()
            updated_metadata = self.update_metadata_paths(metadata)
            self.save_metadata(updated_metadata)
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Выполнение завершено за {elapsed_time:.2f} сек: "
                           f"{results['successful_executions']} успешных, "
                           f"{results['failed_executions']} неудачных.")
            return results

    def update_metadata_paths(self, metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обновляет пути файлов в метаданных для использования транслитерированных имен.
        
        Args:
            metadata: Исходные метаданные
            
        Returns:
            Обновленные метаданные с транслитерированными путями
        """
        updated_metadata = []
        
        for item in metadata:
            # Проверяем, что это не пустой элемент с timestamp
            if not item or (len(item) <= 1 and "timestamp" in item):
                updated_metadata.append(item)
                continue
                
            # Обновляем HTML-путь
            if 'html_path' in item:
                path = Path(item['html_path'])
                filename = path.name
                if filename.startswith('viz_'):
                    name_part = filename[4:-5]  # Удаляем 'viz_' и '.html'
                    transliterated_name = self.transliterate(name_part)
                    new_filename = f"viz_{transliterated_name}.html"
                    item['html_path'] = str(path.parent / new_filename)
                    
            # Обновляем путь к изображению
            if 'image_path' in item:
                path = Path(item['image_path'])
                filename = path.name
                if filename.startswith('viz_'):
                    name_part = filename[4:-4]  # Удаляем 'viz_' и '.png'
                    transliterated_name = self.transliterate(name_part)
                    new_filename = f"viz_{transliterated_name}.png"
                    item['image_path'] = str(path.parent / new_filename)
                    
            updated_metadata.append(item)
            
        return updated_metadata


def main():
    """
    Основная функция для запуска агента выполнения визуализаций.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Выполняет скрипты визуализации')
    parser.add_argument('--sync', action='store_true', help='Использовать последовательное выполнение вместо асинхронного')
    parser.add_argument('--max-concurrent', type=int, default=3, help='Максимальное количество параллельных запусков')
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("visualization_execution.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("visualization_execution")
    logger.info("Запуск процесса выполнения визуализаций...")
    
    try:
        api_key = os.environ.get('OPENAI_API_KEY', "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")
        
        agent = VisualizationExecutionAgent(
            api_key=api_key,
            max_concurrent=args.max_concurrent
        )
        
        results = agent.process(use_async=not args.sync)
        
        logger.info(f"Выполнение визуализаций завершено.")
        logger.info(f"Всего скриптов: {results['total_scripts']}")
        logger.info(f"Успешно выполнено: {results['successful_executions']}")
        logger.info(f"Неудачно выполнено: {results['failed_executions']}")
        
        if results['failed_executions'] > 0:
            logger.warning("Неудачные скрипты:")
            for script in results['failed_files']:
                logger.warning(f"  - {script}")
        
        return results
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении процесса: {str(e)}")
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    main()