import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

class VisualizationStorage:
    """Хранилище метаданных о созданных визуализациях."""
    
    def __init__(self, storage_file="analytics_output/visualizations_metadata.json"):
        self.storage_file = storage_file
        self.visualizations = []
        
        # Настройка логирования
        self.logger = logging.getLogger('VisualizationStorage')
        self.logger.setLevel(logging.INFO)
        
        # Добавляем обработчик для консоли
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(console_handler)
            
            # Создаем директорию для файла хранилища, если она не существует
            os.makedirs(os.path.dirname(storage_file), exist_ok=True)
            
            # Добавляем файловый обработчик
            file_handler = logging.FileHandler("visualization_storage.log", encoding="utf-8")
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
        
        # Загружаем существующие данные, если они есть
        self.load()
        
    def load(self):
        """Загружает данные о визуализациях из JSON файла, если он существует."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.visualizations = json.load(f)
                self.logger.info(f"Загружено {len(self.visualizations)} визуализаций из {self.storage_file}")
            except Exception as e:
                self.logger.error(f"Ошибка при загрузке данных визуализаций: {str(e)}")
                self.visualizations = []
        else:
            self.logger.info(f"Файл {self.storage_file} не существует, создаем новое хранилище")
            self.visualizations = []
            
    def save(self):
        """Сохраняет данные о визуализациях в JSON файл."""
        try:
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.visualizations, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Сохранено {len(self.visualizations)} визуализаций в {self.storage_file}")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении данных визуализаций: {str(e)}")
    
    def add_visualization(self, viz_data: Dict[str, Any]):
        """Добавляет или обновляет данные о визуализации."""
        # Добавляем timestamp, если его еще нет
        if 'timestamp' not in viz_data:
            viz_data['timestamp'] = datetime.now().isoformat()
            
        # Проверяем, есть ли уже такая визуализация (по title и/или id)
        for i, viz in enumerate(self.visualizations):
            if (viz.get('title') == viz_data.get('title') or 
                (viz.get('id') and viz.get('id') == viz_data.get('id'))):
                self.visualizations[i] = viz_data
                self.logger.info(f"Обновлена визуализация: {viz_data.get('title')}")
                self.save()
                return
        
        # Если это новая визуализация, добавляем ее
        self.visualizations.append(viz_data)
        self.logger.info(f"Добавлена новая визуализация: {viz_data.get('title')}")
        self.save()
        
    def get_all_visualizations(self) -> List[Dict[str, Any]]:
        """Возвращает список всех визуализаций."""
        return self.visualizations
    
    def get_visualization_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Находит визуализацию по названию."""
        for viz in self.visualizations:
            if viz.get('title') == title:
                return viz
        return None
    
    def get_interactive_visualizations(self) -> List[Dict[str, Any]]:
        """Возвращает только интерактивные визуализации."""
        return [viz for viz in self.visualizations if viz.get('is_interactive', False)]