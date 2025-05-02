/**
 * Генератор статических миниатюр для визуализаций
 * 
 * Использует предзагруженные PNG файлы в качестве миниатюр.
 */
(function() {
    'use strict';
    
    // Конфигурация
    const config = {
        selectors: {
            visualizationCard: '.visualization-card',
            visualizationContent: '.visualization-content',
            visualizationLoader: '.visualization-loader',
            iframe: '.visualization-iframe',
            thumbnail: '.viz-thumbnail' // Класс для контейнера миниатюры
        },
        paths: {
            visualizationsBase: '../analytics_output/visualizations/' // Базовый путь к визуализациям
        },
        fallbackImage: 'img/placeholder.png' // Путь к изображению-заглушке (если нужно)
    };
    
    // Инициализация миниатюр
    function initStaticThumbnails() {
        console.log('Инициализация статических PNG миниатюр...');
        
        if (window.visualizationManager && window.visualizationManager.getVisualizations) {
            const visualizations = window.visualizationManager.getVisualizations();
            
            document.querySelectorAll(config.selectors.visualizationCard).forEach(card => {
                const vizId = card.dataset.vizId;
                
                if (vizId) {
                    // Находим данные визуализации
                    const vizData = visualizations.find(v => v.id === vizId);
                    
                    if (vizData) {
                        // Создаем миниатюру
                        createStaticThumbnail(card, vizData);
                    } else {
                        console.warn(`Не найдены данные для визуализации с ID: ${vizId}`);
                    }
                }
            });
        } else {
            console.error('visualizationManager не доступен для инициализации миниатюр');
        }
    }
    
    // Создание статической миниатюры для карточки
    function createStaticThumbnail(card, vizData) {
        // Находим контейнер для контента
        const content = card.querySelector(config.selectors.visualizationContent);
        if (!content) return;
        
        // Скрываем индикатор загрузки
        const loader = content.querySelector(config.selectors.visualizationLoader);
        if (loader) {
            loader.style.display = 'none';
        }
        
        // Скрываем iframe, если он есть (на случай, если он был создан ранее)
        const iframe = content.querySelector(config.selectors.iframe);
        if (iframe) {
            iframe.style.display = 'none';
        }
        
        // Удаляем старый canvas, если он есть
        const oldCanvas = content.querySelector('canvas');
        if (oldCanvas) {
            oldCanvas.parentElement.remove(); // Удаляем родительский div миниатюры
        }
         // Удаляем старый контейнер миниатюры, если он есть
        const oldThumbnail = content.querySelector(config.selectors.thumbnail);
        if (oldThumbnail) {
            oldThumbnail.remove();
        }

        // Создаем контейнер для миниатюры
        const thumbnail = document.createElement('div');
        thumbnail.className = config.selectors.thumbnail.substring(1); // Убираем точку из селектора
        thumbnail.style.width = '100%';
        thumbnail.style.height = '100%';
        thumbnail.style.position = 'absolute';
        thumbnail.style.top = '0';
        thumbnail.style.left = '0';
        thumbnail.style.zIndex = '1';
        thumbnail.style.cursor = 'pointer';
        thumbnail.style.backgroundColor = '#f8f9fa'; // Легкий фон на случай ошибки загрузки
        thumbnail.style.display = 'flex';
        thumbnail.style.alignItems = 'center';
        thumbnail.style.justifyContent = 'center';

        // Создаем img элемент для PNG
        const img = document.createElement('img');
        img.style.display = 'block';
        img.style.maxWidth = '100%';
        img.style.maxHeight = '100%';
        img.style.objectFit = 'contain'; // Масштабируем изображение, сохраняя пропорции
        img.alt = vizData.title || `Визуализация ${vizData.id}`;

        // Формируем путь к PNG файлу
        // Просто заменяем расширение .html на .png
        const pngPath = config.paths.visualizationsBase + vizData.path.replace(/\.html$/, '.png');
        img.src = pngPath;

        // Обработчик ошибок загрузки изображения
        img.onerror = function() {
            console.error(`Не удалось загрузить миниатюру: ${pngPath}`);
            img.style.display = 'none'; // Скрываем сломанное изображение
            // Можно показать текст ошибки или заглушку
            const errorText = document.createElement('span');
            errorText.textContent = 'Ошибка загрузки превью';
            errorText.style.color = '#dc3545';
            errorText.style.fontSize = '12px';
            thumbnail.appendChild(errorText);
            // Или установить src на заглушку:
            // img.src = config.fallbackImage;
            // img.style.display = 'block';
        };
        
        // Добавляем img в контейнер
        thumbnail.appendChild(img);
        content.appendChild(thumbnail);
        
        // Добавляем обработчик клика для открытия визуализации
        thumbnail.addEventListener('click', function() {
            if (window.visualizationManager && window.visualizationManager.openVisualization) {
                window.visualizationManager.openVisualization(vizData.id);
            } else {
                console.error('Метод openVisualization не найден в visualizationManager');
                // Можно добавить резервный механизм открытия, если он нужен
            }
            
            // Улучшаем обработчики закрытия после открытия модалки
            setTimeout(() => {
                if (window.modalHelpers) {
                    window.modalHelpers.enhanceModalClose();
                }
            }, 100);
        });
    }

    // --- Удаленные функции отрисовки Canvas ---
    // function drawBarChart(canvas, vizData) { ... }
    // function drawLineChart(canvas, vizData) { ... }
    // function drawScatterChart(canvas, vizData) { ... }
    // function drawPieChart(canvas, vizData) { ... }
    // function drawDefaultChart(canvas, vizData) { ... }
    // function drawViewIcon(ctx, x, y) { ... }
    // function truncateText(text, maxLength) { ... } // Оставляем, если используется где-то еще, иначе удаляем

    // Инициализация при загрузке DOM
    function init() {
        // Проверяем наличие нового менеджера миниатюр
        if (window.thumbnailManager) {
            // Используем новый менеджер миниатюр
            console.log('Используем централизованный менеджер миниатюр');
            // Ничего не делаем, все управление миниатюрами теперь через thumbnailManager
            return;
        }
        
        // Запускаем старую логику только если нет нового менеджера
        console.log('Нет централизованного менеджера миниатюр, используем старую логику');
        
        // Старая логика инициализации...
        // Проверяем наличие visualizationManager
        if (window.visualizationManager) {
            // Инициализируем миниатюры
            initStaticThumbnails();
        } else {
            // Если visualizationManager еще не готов, ожидаем его инициализации
            console.log('Ожидание инициализации visualizationManager для статических миниатюр...');
            
            // Проверяем каждые 200мс наличие visualizationManager
            const checkInterval = setInterval(() => {
                if (window.visualizationManager) {
                    clearInterval(checkInterval);
                    initStaticThumbnails();
                }
            }, 200);
            
            // Максимальное время ожидания - 5 секунд
            setTimeout(() => {
                if (!window.visualizationManager) { // Проверяем еще раз перед выводом ошибки
                   clearInterval(checkInterval);
                   console.error('Тайм-аут ожидания visualizationManager для статических миниатюр');
                }
            }, 5000);
        }
        // ...сохраняем остальную часть функции без изменений

        // Обработчик событий изменения фильтров
        function handleFilterChange() {
            // Отменяем предыдущую инициализацию
            clearTimeout(window.staticThumbnailsTimeout);
            // Даем время фильтрам применить изменения
            window.staticThumbnailsTimeout = setTimeout(() => {
                // Сбрасываем состояние загрузки
                document.querySelectorAll('.visualization-loader').forEach(loader => {
                    loader.style.display = 'none';
                });
                // Повторно инициализируем миниатюры
                initStaticThumbnails();
            }, 300);
        }

        // Добавляем слушатели событий на фильтры
        document.querySelectorAll('select, input[type="search"], button.reset-filters').forEach(element => {
            element.addEventListener('change', handleFilterChange);
            element.addEventListener('click', handleFilterChange);
            element.addEventListener('input', handleFilterChange);
        });
    }
    
    // Запускаем инициализацию
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM уже загружен
        init();
    }

    // Делаем функцию инициализации доступной глобально
    window.initStaticThumbnails = initStaticThumbnails;
})();