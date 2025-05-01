/**
 * Универсальный обработчик для адаптивных визуализаций
 * @author MarketAnalytics Team
 * @version 1.0.0
 */
(function() {
    'use strict';
    
    // Конфигурация по умолчанию
    const config = {
        vizSelector: '[id^="viz_"], .plotly-graph-div, [class*="visualization"]',
        minWidth: 300,
        minHeight: 200,
        observeResize: true,
        scaleLabels: true,
        debugMode: false
    };
    
    // Основной класс для работы с визуализациями
    class VisualizationManager {
        constructor(options = {}) {
            this.config = {...config, ...options};
            this.visualizations = [];
            this.resizeObserver = null;
            
            this.init();
        }
        
        init() {
            this.log('Initializing visualization manager');
            this.findVisualizations();
            
            if (this.config.observeResize) {
                this.setupResizeObserver();
            }
            
            // Обработка начального рендеринга после загрузки DOM
            window.addEventListener('DOMContentLoaded', () => this.adjustAllVisualizations());
            
            // Обработка изменения размера окна
            window.addEventListener('resize', this.debounce(() => {
                this.log('Window resize detected');
                this.adjustAllVisualizations();
            }, 250));
            
            // Проверка iframe загрузки
            document.addEventListener('load', event => {
                if (event.target.tagName === 'IFRAME') {
                    this.log('Iframe loaded:', event.target);
                    this.adjustIframeVisualization(event.target);
                }
            }, true);
        }
        
        findVisualizations() {
            const elements = document.querySelectorAll(this.config.vizSelector);
            this.log(`Found ${elements.length} visualization elements`);
            
            elements.forEach(element => {
                this.visualizations.push({
                    element,
                    originalWidth: element.offsetWidth,
                    originalHeight: element.offsetHeight,
                    container: this.findClosestContainer(element)
                });
            });
            
            // Поиск iframe с визуализациями
            document.querySelectorAll('iframe').forEach(iframe => {
                if (this.isVisualizationIframe(iframe)) {
                    this.log('Found visualization iframe:', iframe);
                    this.addIframeLoadListener(iframe);
                }
            });
        }
        
        isVisualizationIframe(iframe) {
            // Проверка на iframe с визуализациями по атрибутам
            if (!iframe.src) return false;
            
            return iframe.src.includes('viz_') || 
                   iframe.className.includes('visualization') ||
                   iframe.parentElement.className.includes('visualization');
        }
        
        addIframeLoadListener(iframe) {
            // Если iframe уже загружен
            if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
                this.adjustIframeVisualization(iframe);
                return;
            }
            
            // Добавляем слушатель загрузки
            iframe.addEventListener('load', () => {
                this.log('Iframe loaded via event listener');
                this.adjustIframeVisualization(iframe);
            });
        }
        
        adjustIframeVisualization(iframe) {
            try {
                // Получаем документ внутри iframe
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                
                // Находим элементы визуализации внутри iframe
                const vizElements = iframeDoc.querySelectorAll(this.config.vizSelector);
                
                if (vizElements.length === 0) {
                    // Если не нашли по селектору, ищем конкретно Plotly элемент
                    const plotlyElements = iframeDoc.querySelectorAll('.plotly-graph-div');
                    
                    if (plotlyElements.length > 0) {
                        this.log(`Found ${plotlyElements.length} Plotly elements in iframe`);
                        plotlyElements.forEach(element => this.adjustPlotlyElement(element, iframe));
                    }
                } else {
                    this.log(`Found ${vizElements.length} visualization elements in iframe`);
                    vizElements.forEach(element => this.adjustVisualizationElement(element, iframe));
                }
                
                // Подстраиваем высоту iframe под содержимое
                this.resizeIframeToContent(iframe);
            } catch (e) {
                this.log('Error adjusting iframe visualization:', e);
            }
        }
        
        adjustPlotlyElement(element, iframe) {
            // Сохраняем оригинальные размеры, если их еще нет
            if (!element.getAttribute('data-original-width')) {
                element.setAttribute('data-original-width', element.offsetWidth);
                element.setAttribute('data-original-height', element.offsetHeight);
            }
            
            const containerWidth = iframe.parentElement.offsetWidth;
            const containerHeight = iframe.parentElement.offsetHeight;
            const originalWidth = parseInt(element.getAttribute('data-original-width'), 10);
            
            // Вычисляем масштаб
            const scale = Math.min(1, containerWidth / originalWidth);
            
            this.log(`Adjusting Plotly element: scale=${scale}, container=${containerWidth}x${containerHeight}`);
            
            // Применяем масштабирование
            if (scale < 1) {
                element.style.transform = `scale(${scale})`;
                element.style.transformOrigin = 'top left';
                element.style.width = `${originalWidth}px`;
                element.style.height = 'auto';
                
                // Обновляем размер контейнера
                const scaledHeight = element.offsetHeight * scale;
                iframe.style.height = `${scaledHeight + 20}px`; // +20px для запаса
            } else {
                element.style.transform = '';
                element.style.width = '100%';
                element.style.height = 'auto';
            }
            
            // Пытаемся обновить layout через Plotly API если возможно
            if (iframe.contentWindow.Plotly) {
                try {
                    const plotId = element.id;
                    iframe.contentWindow.Plotly.relayout(plotId, {
                        'xaxis.automargin': true,
                        'yaxis.automargin': true
                    });
                } catch (e) {
                    this.log('Error updating Plotly layout:', e);
                }
            }
        }
        
        adjustVisualizationElement(element, container) {
            // Реализация масштабирования для обычного DOM элемента
            const containerWidth = container.offsetWidth || 
                                 container.clientWidth || 
                                 container.parentElement.offsetWidth;
                                 
            if (containerWidth <= 0) return;
            
            // Сохраняем оригинальный размер если не сохранен
            if (!element.getAttribute('data-original-width')) {
                element.setAttribute('data-original-width', element.offsetWidth || 
                                   element.clientWidth || containerWidth);
            }
            
            const originalWidth = parseInt(element.getAttribute('data-original-width'), 10);
            const scale = Math.min(1, containerWidth / originalWidth);
            
            // Применяем масштабирование
            if (scale < 1 && originalWidth > containerWidth) {
                element.style.transform = `scale(${scale})`;
                element.style.transformOrigin = 'top left';
                element.style.width = `${originalWidth}px`;
                
                // Масштабируем текст и метки если нужно
                if (this.config.scaleLabels) {
                    const textElements = element.querySelectorAll('text, .tick text, .axis-label');
                    textElements.forEach(textEl => {
                        const currentSize = parseFloat(window.getComputedStyle(textEl).fontSize);
                        textEl.style.fontSize = `${currentSize * scale}px`;
                    });
                }
            } else {
                element.style.transform = '';
                element.style.width = '100%';
            }
        }
        
        resizeIframeToContent(iframe) {
            try {
                const body = iframe.contentDocument.body;
                const html = iframe.contentDocument.documentElement;
                
                const height = Math.max(
                    body.scrollHeight, body.offsetHeight,
                    html.clientHeight, html.scrollHeight, html.offsetHeight
                );
                
                // Устанавливаем высоту с запасом
                iframe.style.height = `${height + 20}px`;
            } catch (e) {
                this.log('Error resizing iframe:', e);
            }
        }
        
        findClosestContainer(element) {
            // Ищем ближайший контейнер для визуализации
            let container = element.parentElement;
            while (container && !this.isVisualizationContainer(container)) {
                container = container.parentElement;
            }
            return container || element.parentElement;
        }
        
        isVisualizationContainer(element) {
            // Проверяем, является ли элемент контейнером для визуализации
            const classes = element.className || '';
            return classes.includes('visualization-content') || 
                   classes.includes('chart-container') ||
                   classes.includes('card-body');
        }
        
        setupResizeObserver() {
            if (!window.ResizeObserver) {
                this.log('ResizeObserver not supported');
                return;
            }
            
            this.resizeObserver = new ResizeObserver(entries => {
                entries.forEach(entry => {
                    const container = entry.target;
                    const iframe = container.querySelector('iframe');
                    
                    if (iframe) {
                        this.adjustIframeVisualization(iframe);
                    } else {
                        const vizElement = container.querySelector(this.config.vizSelector);
                        if (vizElement) {
                            this.adjustVisualizationElement(vizElement, container);
                        }
                    }
                });
            });
            
            // Наблюдаем за изменениями контейнеров
            document.querySelectorAll('.visualization-content, .chart-container').forEach(
                container => this.resizeObserver.observe(container)
            );
        }
        
        adjustAllVisualizations() {
            // Обрабатываем все найденные визуализации
            this.visualizations.forEach(viz => {
                this.adjustVisualizationElement(viz.element, viz.container);
            });
            
            // Обрабатываем все iframe
            document.querySelectorAll('iframe').forEach(iframe => {
                if (this.isVisualizationIframe(iframe)) {
                    this.adjustIframeVisualization(iframe);
                }
            });
        }
        
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    timeout = null;
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
        
        log(...args) {
            if (this.config.debugMode) {
                console.log('[VizManager]', ...args);
            }
        }
    }
    
    // Автоматический запуск по готовности DOM
    document.addEventListener('DOMContentLoaded', () => {
        window.vizManager = new VisualizationManager({
            debugMode: true
        });
    });
    
    // Экспортируем в глобальный объект для возможного использования извне
    window.VisualizationManager = VisualizationManager;
})();