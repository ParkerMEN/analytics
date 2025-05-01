import os
import re
import json
import logging
import argparse
import traceback
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import openai
from datetime import datetime

class GPTScriptFixerAgent:
    """
    Агент для исправления неработающих скриптов визуализации через GPT.
    Отправляет код с ошибкой в GPT, получает исправленный код и сохраняет его.
    """
    
    def __init__(self, api_key: str, 
                 model: str = "gpt-4.1-mini", 
                 error_logs_dir: str = "analytics_output/visualizations/error_logs",
                 code_dir: str = "analytics_output/visualizations/code"):
        """
        Инициализирует GPTScriptFixerAgent.
        
        Args:
            api_key (str): API ключ для OpenAI
            model (str): Модель GPT для использования
            error_logs_dir (str): Директория с логами ошибок
            code_dir (str): Директория с кодом визуализаций
        """
        self.api_key = api_key
        self.model = model
        self.error_logs_dir = error_logs_dir
        self.code_dir = code_dir
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Настройка логирования
        self.logger = logging.getLogger('GPTScriptFixerAgent')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # Добавляем обработчик для консоли
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(console_handler)
            
            # Добавляем файловый обработчик
            file_handler = logging.FileHandler("gpt_script_fixer.log", encoding="utf-8")
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)

    def find_failed_scripts(self) -> List[str]:
        """
        Находит скрипты, которые не удалось выполнить.
        
        Returns:
            List[str]: Список путей к файлам с ошибками
        """
        failed_scripts = []
        
        # Проверяем лог-файлы с ошибками
        if os.path.exists(self.error_logs_dir):
            for filename in os.listdir(self.error_logs_dir):
                if filename.endswith(".error.log"):
                    script_name = filename.replace(".error.log", "")
                    script_path = os.path.join(self.code_dir, script_name)
                    if os.path.exists(script_path):
                        failed_scripts.append(script_path)
                        self.logger.info(f"Найден скрипт с ошибкой: {script_path}")
        
        return failed_scripts
    
    def extract_error_message(self, script_path: str) -> str:
        """
        Извлекает сообщение об ошибке из лог-файла.
        
        Args:
            script_path (str): Путь к скрипту
            
        Returns:
            str: Сообщение об ошибке
        """
        script_name = os.path.basename(script_path)
        error_log_path = os.path.join(self.error_logs_dir, f"{script_name}.error.log")
        
        if os.path.exists(error_log_path):
            with open(error_log_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Ищем сообщение об ошибке
                error_match = re.search(r'Сообщение об ошибке:\s*(.*?)(?:\n\n|$)', content, re.DOTALL)
                if error_match:
                    return error_match.group(1).strip()
        
        return "Неизвестная ошибка"
    
    def read_script_content(self, script_path: str) -> str:
        """
        Считывает содержимое скрипта.
        
        Args:
            script_path (str): Путь к скрипту
            
        Returns:
            str: Содержимое скрипта
        """
        with open(script_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def fix_script_with_gpt(self, script_path: str) -> Tuple[bool, str]:
        """
        Исправляет скрипт с помощью GPT.
        
        Args:
            script_path (str): Путь к скрипту
            
        Returns:
            Tuple[bool, str]: (успех операции, исправленный код или сообщение об ошибке)
        """
        # Считываем скрипт
        code = self.read_script_content(script_path)
        
        # Получаем сообщение об ошибке
        error_message = self.extract_error_message(script_path)
        
        # Формируем промпт для GPT
        prompt = f"""
Я отправляю тебе Python-скрипт для визуализации данных, который вызывает ошибку:
{error_message}

Вот код скрипта:

```python
{code}
Пожалуйста, исправь ошибку, но вноси только минимально необходимые изменения:

Если это ошибка "keyword argument repeated", найди и удали повторяющиеся именованные аргументы в вызовах функций
Не меняй логику, структуру или функциональность кода
Не добавляй новые функции или изменения, не связанные с ошибкой
Внешний вид и функциональность визуализации должны остаться прежними
Верни только исправленный код без объяснений. """
        try:
            # Отправляем запрос к GPT
            self.logger.info(f"Отправка скрипта {script_path} в GPT для исправления")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты опытный Python-разработчик, специализирующийся на библиотеках визуализации данных (plotly, matplotlib). Тебе нужно исправить ошибку в коде, сохраняя его структуру и функциональность."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            # Получаем ответ GPT
            fixed_code = response.choices[0].message.content
            
            # Извлекаем только код из ответа, если он обернут в блок кода
            code_match = re.search(r'```(?:python)?(.*?)```', fixed_code, re.DOTALL)
            if code_match:
                fixed_code = code_match.group(1).strip()
            
            return True, fixed_code
            
        except Exception as e:
            self.logger.error(f"Ошибка при исправлении скрипта с помощью GPT: {str(e)}")
            return False, str(e)

    def save_fixed_script(self, script_path: str, fixed_code: str) -> bool:
        """
        Сохраняет исправленный скрипт.
        
        Args:
            script_path (str): Путь к исходному скрипту
            fixed_code (str): Исправленный код
            
        Returns:
            bool: Успех операции
        """
        try:
            # Создаем резервную копию оригинального скрипта
            backup_dir = os.path.join(os.path.dirname(script_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            script_name = os.path.basename(script_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"{script_name}.{timestamp}.bak")
            
            # Копируем оригинальный скрипт в резервную копию
            with open(script_path, "r", encoding="utf-8") as src, open(backup_path, "w", encoding="utf-8") as dst:
                dst.write(src.read())
            
            # Сохраняем исправленный скрипт
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            
            self.logger.info(f"Скрипт {script_path} успешно исправлен и сохранен")
            self.logger.info(f"Резервная копия сохранена в {backup_path}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении исправленного скрипта: {str(e)}")
            return False

    def process(self, specific_script: Optional[str] = None) -> Dict[str, Any]:
        """
        Основной метод для исправления скриптов с ошибками.
        
        Args:
            specific_script (Optional[str]): Путь к конкретному скрипту для исправления
            
        Returns:
            Dict[str, Any]: Результаты процесса исправления
        """
        results = {
            'processed': 0,
            'fixed': 0,
            'failed': 0,
            'fixed_scripts': [],
            'failed_scripts': []
        }
        
        # Получаем список скриптов для исправления
        if specific_script:
            if os.path.exists(specific_script):
                scripts_to_fix = [specific_script]
            else:
                self.logger.error(f"Указанный скрипт не существует: {specific_script}")
                return results
        else:
            scripts_to_fix = self.find_failed_scripts()
        
        results['processed'] = len(scripts_to_fix)
        
        # Исправляем каждый скрипт
        for script_path in scripts_to_fix:
            self.logger.info(f"Обработка скрипта: {script_path}")
            
            success, fixed_code = self.fix_script_with_gpt(script_path)
            
            if success:
                if self.save_fixed_script(script_path, fixed_code):
                    results['fixed'] += 1
                    results['fixed_scripts'].append(script_path)
                else:
                    results['failed'] += 1
                    results['failed_scripts'].append(script_path)
            else:
                results['failed'] += 1
                results['failed_scripts'].append(script_path)
                self.logger.error(f"Не удалось исправить скрипт: {script_path}")
        
        return results

def main():
    """
    Основная функция для запуска агента исправления скриптов.
    """
    parser = argparse.ArgumentParser(description='Исправляет неработающие скрипты визуализации с помощью GPT')
    parser.add_argument('--api-key', dest='api_key', help='API ключ для OpenAI', default="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")
    parser.add_argument('--script', dest='script', help='Путь к конкретному скрипту для исправления', default=None)
    args = parser.parse_args()

    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("gpt_script_fixer.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger("gpt_script_fixer")
    logger.info("Запуск процесса исправления скриптов...")

    try:
        fixer = GPTScriptFixerAgent(api_key=args.api_key)
        results = fixer.process(args.script)
        
        logger.info(f"Процесс завершен. Обработано скриптов: {results['processed']}")
        logger.info(f"Успешно исправлено: {results['fixed']}")
        logger.info(f"Не удалось исправить: {results['failed']}")
        
        if results['fixed_scripts']:
            logger.info("Список исправленных скриптов:")
            for script in results['fixed_scripts']:
                logger.info(f"  - {script}")
                
        if results['failed_scripts']:
            logger.warning("Список скриптов, которые не удалось исправить:")
            for script in results['failed_scripts']:
                logger.warning(f"  - {script}")

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()