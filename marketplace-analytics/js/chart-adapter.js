/**
 * chart-adapter.js
 * 
 * Адаптивное изменение размеров визуализаций Plotly
 * Обеспечивает корректное отображение графиков в различных контейнерах
 * и при изменении размеров окна
 * 
 * @version 1.0.0
 */

(function() {
    'use strict';

    // Конфигурация
    const config = {
        // Селекторы для поиска элементов
        selectors: {
            visualizationCard: '.visualization-card',
            visualizationContent: '.visualization-content',
            iframe: '.visualization-iframe'
        },
        // Префикс имени файлов визуализаций
        vizFilePrefix: 'viz_',
        // Задержка перед ресайзом (для оптимизации производительности)
        resizeDelay: 200,
        // Периодичность проверки графиков в iframe (мс)
        checkInterval: 500,
        // Максимальное количество попыток проверки
        maxCheckAttempts: 10
    };

    // Хранилище ссылок на графики и их контейнеры
    const chartRegistry = new Map();
    
    // Утилиты
    const utils = {
        // Debounce для оптимизации обработки событий ресайза
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Получение реальных размеров контейнера с учетом padding и border
        getContentSize: function(element) {
            const style = window.getComputedStyle(element);
            const paddingX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
            const paddingY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
            
            return {
                width: element.clientWidth - paddingX,
                height: element.clientHeight - paddingY
            };
        },
        
        // Логирование с префиксом для отладки
        log: function(message, level = 'info') {
            const prefix = '[ChartAdapter]';
            if (level === 'error') {
                console.error(`${prefix} ${message}`);
            } else if (level === 'warn') {
                console.warn(`${prefix} ${message}`);
            } else {
                console.log(`${prefix} ${message}`);
            }
        }
    };

    // Обработчик обычных графиков Plotly (не в iframe)
    const directChartHandler = {
        // Инициализация обработки прямых графиков Plotly на странице
        init: function() {
            // Поиск всех контейнеров с графиками Plotly на странице
            const plotlyContainers = document.querySelectorAll('.plotly-graph-div');
            
            if (plotlyContainers.length > 0) {
                utils.log(`Найдено ${plotlyContainers.length} графиков Plotly на странице`);
                
                plotlyContainers.forEach((container, index) => {
                    const parentElement = container.closest('.visualization-content') || container.parentElement;
                    
                    // Регистрация графика для последующего изменения размеров
                    chartRegistry.set(container.id || `direct-chart-${index}`, {
                        type: 'direct',
                        container: container,
                        parent: parentElement
                    });
                });
                
                // Начальное изменение размеров графиков
                this.resizeAllCharts();
            }
        },
        
        // Изменение размера всех прямых графиков
        resizeAllCharts: function() {
            for (const [id, chartInfo] of chartRegistry.entries()) {
                if (chartInfo.type === 'direct') {
                    this.resizeChart(chartInfo.container, chartInfo.parent);
                }
            }
        },
        
        // Изменение размера конкретного графика
        resizeChart: function(chartElement, parentElement) {
            if (!chartElement || !parentElement || !window.Plotly) {
                return;
            }
            
            try {
                const size = utils.getContentSize(parentElement);
                
                // Изменение размера через Plotly API
                window.Plotly.relayout(chartElement, {
                    width: size.width,
                    height: size.height
                });
                
                utils.log(`Изменен размер графика: ${size.width}x${size.height}`);
            } catch (e) {
                utils.log(`Ошибка при изменении размера графика: ${e.message}`, 'error');
            }
        }
    };

    // Обработчик iframe с графиками Plotly
    const iframeChartHandler = {
        // Инициализация системы адаптации для iframe
        init: function() {
            // Поиск всех iframe с визуализациями
            this.findAndRegisterIframes();
            
            // Обработка сообщений от iframe
            window.addEventListener('message', this.handleIframeMessage.bind(this));
        },
        
        // Поиск и регистрация iframe с визуализациями
        findAndRegisterIframes: function() {
            const iframes = document.querySelectorAll(config.selectors.iframe);
            
            if (iframes.length > 0) {
                utils.log(`Найдено ${iframes.length} iframe с визуализациями`);
                
                iframes.forEach((iframe, index) => {
                    const parentContent = iframe.closest(config.selectors.visualizationContent);
                    
                    if (parentContent) {
                        const iframeId = iframe.id || `iframe-chart-${index}`;
                        
                        // Регистрация iframe для последующей обработки
                        chartRegistry.set(iframeId, {
                            type: 'iframe',
                            element: iframe,
                            parent: parentContent,
                            ready: false,
                            checkAttempts: 0
                        });
                        
                        // Запуск проверки наличия графика в iframe
                        this.checkIframeChart(iframeId);
                    }
                });
            }
        },
        
        // Проверка загрузки графика в iframe
        checkIframeChart: function(iframeId) {
            const chartInfo = chartRegistry.get(iframeId);
            
            if (!chartInfo) return;
            
            // Увеличиваем счетчик попыток
            chartInfo.checkAttempts++;
            
            try {
                const iframe = chartInfo.element;
                
                // Проверяем, загружен ли iframe и доступен ли контент
                if (iframe.contentDocument && iframe.contentWindow) {
                    // Находим график Plotly в iframe
                    const plotlyDiv = iframe.contentDocument.querySelector('.plotly-graph-div');
                    
                    if (plotlyDiv) {
                        utils.log(`График в iframe ${iframeId} найден`);
                        chartInfo.plotlyDiv = plotlyDiv.id;
                        chartInfo.ready = true;
                        
                        // Изменение размера графика
                        this.resizeIframeChart(iframeId);
                        return;
                    }
                }
                
                // Если не достигнуто максимальное количество попыток, пробуем снова
                if (chartInfo.checkAttempts < config.maxCheckAttempts) {
                    setTimeout(() => {
                        this.checkIframeChart(iframeId);
                    }, config.checkInterval);
                } else {
                    utils.log(`Не удалось найти график в iframe ${iframeId} после ${config.maxCheckAttempts} попыток`, 'warn');
                }
            } catch (e) {
                utils.log(`Ошибка при проверке iframe ${iframeId}: ${e.message}`, 'error');
            }
        },
        
        // Изменение размера графика в iframe
        resizeIframeChart: function(iframeId) {
            const chartInfo = chartRegistry.get(iframeId);
            
            if (!chartInfo || !chartInfo.ready) return;
            
            try {
                const iframe = chartInfo.element;
                const parentSize = utils.getContentSize(chartInfo.parent);
                
                // Отправляем сообщение в iframe для изменения размера графика
                iframe.contentWindow.postMessage({
                    type: 'resize-plotly',
                    width: parentSize.width,
                    height: parentSize.height,
                    plotlyDiv: chartInfo.plotlyDiv
                }, '*');
                
                utils.log(`Отправлен запрос на изменение размера графика в iframe ${iframeId}: ${parentSize.width}x${parentSize.height}`);
            } catch (e) {
                utils.log(`Ошибка при изменении размера iframe ${iframeId}: ${e.message}`, 'error');
            }
        },
        
        // Изменение размеров всех iframe-графиков
        resizeAllIframeCharts: function() {
            for (const [id, chartInfo] of chartRegistry.entries()) {
                if (chartInfo.type === 'iframe' && chartInfo.ready) {
                    this.resizeIframeChart(id);
                }
            }
        },
        
        // Обработка сообщений от iframe
        handleIframeMessage: function(event) {
            try {
                const data = event.data;
                
                if (data && data.type === 'plotly-ready') {
                    utils.log('Получено сообщение о готовности Plotly в iframe');
                    
                    // Находим iframe по источнику сообщения
                    for (const [id, chartInfo] of chartRegistry.entries()) {
                        if (chartInfo.type === 'iframe' && chartInfo.element.contentWindow === event.source) {
                            chartInfo.plotlyDiv = data.plotlyDiv;
                            chartInfo.ready = true;
                            
                            // Изменение размера графика
                            this.resizeIframeChart(id);
                            break;
                        }
                    }
                }
            } catch (e) {
                utils.log(`Ошибка при обработке сообщения от iframe: ${e.message}`, 'error');
            }
        }
    };

    // Настройка наблюдателей за изменениями
    const observers = {
        // Настройка Intersection Observer для ленивой инициализации
        setupIntersectionObserver: function() {
            const options = {
                root: null,
                rootMargin: '0px',
                threshold: 0.1
            };
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const card = entry.target;
                        const iframe = card.querySelector(config.selectors.iframe);
                        
                        if (iframe && iframe.src) {
                            // Если это новый iframe, регистрируем его
                            const iframeId = iframe.id || `iframe-chart-${Date.now()}`;
                            if (!iframe.id) iframe.id = iframeId;
                            
                            if (!chartRegistry.has(iframeId)) {
                                const parentContent = iframe.closest(config.selectors.visualizationContent);
                                if (parentContent) {
                                    chartRegistry.set(iframeId, {
                                        type: 'iframe',
                                        element: iframe,
                                        parent: parentContent,
                                        ready: false,
                                        checkAttempts: 0
                                    });
                                    
                                    iframeChartHandler.checkIframeChart(iframeId);
                                }
                            }
                        }
                        
                        // Отключаем наблюдение после обработки
                        observer.unobserve(card);
                    }
                });
            }, options);
            
            // Начинаем наблюдение за всеми карточками визуализаций
            document.querySelectorAll(config.selectors.visualizationCard).forEach(card => {
                observer.observe(card);
            });
            
            return observer;
        },
        
        // Настройка Resize Observer для отслеживания изменений размеров
        setupResizeObserver: function() {
            if (!window.ResizeObserver) {
                utils.log('ResizeObserver не поддерживается в этом браузере', 'warn');
                return null;
            }
            
            const observer = new ResizeObserver(utils.debounce((entries) => {
                entries.forEach(entry => {
                    const content = entry.target;
                    
                    // Находим все графики в этом контейнере
                    for (const [id, chartInfo] of chartRegistry.entries()) {
                        if (chartInfo.parent === content) {
                            if (chartInfo.type === 'direct') {
                                directChartHandler.resizeChart(chartInfo.container, content);
                            } else if (chartInfo.type === 'iframe' && chartInfo.ready) {
                                iframeChartHandler.resizeIframeChart(id);
                            }
                        }
                    }
                });
            }, config.resizeDelay));
            
            // Начинаем наблюдение за всеми контейнерами контента
            document.querySelectorAll(config.selectors.visualizationContent).forEach(content => {
                observer.observe(content);
            });
            
            return observer;
        },
        
        // Настройка MutationObserver для отслеживания динамически добавленных элементов
        setupMutationObserver: function() {
            const observer = new MutationObserver((mutations) => {
                let needsUpdate = false;
                
                mutations.forEach(mutation => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // Проверяем, добавлена ли карточка визуализации
                                if (node.matches(config.selectors.visualizationCard) || 
                                    node.querySelector(config.selectors.visualizationCard)) {
                                    needsUpdate = true;
                                }
                            }
                        });
                    }
                });
                
                if (needsUpdate) {
                    utils.log('Обнаружены новые элементы визуализации, обновляем...');
                    init();
                }
            });
            
            // Наблюдаем за изменениями в контейнере визуализаций
            const container = document.querySelector('#visualizations-grid') || document.body;
            observer.observe(container, { 
                childList: true, 
                subtree: true 
            });
            
            return observer;
        }
    };

    // Улучшенный скрипт для инъекции в iframe
    function injectEnhancedIframeScript() {
        const script = `
        (function() {
            // Проверяем, был ли скрипт уже загружен
            if (window.__plotlyResizeHandlerInitialized) return;
            window.__plotlyResizeHandlerInitialized = true;
            
            // Функция для изменения размера графика Plotly
            function resizePlotlyChart(plotlyDiv, width, height) {
                if (window.Plotly && document.getElementById(plotlyDiv)) {
                    try {
                        console.log('[PlotlyResize] Изменение размеров графика ' + plotlyDiv + ' до ' + width + 'x' + height);
                        
                        // Получаем текущий макет
                        const currentLayout = JSON.parse(JSON.stringify(window.Plotly.getLayout(plotlyDiv) || {}));
                        
                        // Создаем новый макет с обновленными размерами
                        const newLayout = Object.assign({}, currentLayout, {
                            width: width,
                            height: height,
                            autosize: false
                        });
                        
                        // Применяем новый макет
                        window.Plotly.relayout(plotlyDiv, newLayout)
                            .then(() => {
                                console.log('[PlotlyResize] График успешно изменен');
                            })
                            .catch(e => {
                                console.error('[PlotlyResize] Ошибка при изменении размера:', e);
                            });
                    } catch (e) {
                        console.error('[PlotlyResize] Ошибка при изменении размера:', e);
                    }
                } else {
                    console.warn('[PlotlyResize] Plotly или элемент графика не найден');
                }
            }
            
            // Улучшенный обработчик сообщений
            window.addEventListener('message', function(event) {
                try {
                    var data = event.data;
                    
                    if (data && data.type === 'resize-plotly') {
                        console.log('[PlotlyResize] Получено сообщение для изменения размера:', data);
                        
                        // Если plotlyDiv не указан, находим его
                        let plotlyDiv = data.plotlyDiv;
                        if (!plotlyDiv) {
                            const plotlyElements = document.querySelectorAll('.plotly-graph-div');
                            if (plotlyElements.length > 0) {
                                plotlyDiv = plotlyElements[0].id;
                            }
                        }
                        
                        if (plotlyDiv) {
                            resizePlotlyChart(plotlyDiv, data.width, data.height);
                        }
                    }
                } catch (e) {
                    console.error('[PlotlyResize] Ошибка при обработке сообщения:', e);
                }
            });
            
            // Улучшенная функция уведомления родительского окна
            function notifyParentWhenPlotlyReady() {
                // Проверяем доступность Plotly
                if (typeof window.Plotly !== 'undefined' || document.querySelector('.plotly-graph-div')) {
                    const plotlyElements = document.querySelectorAll('.plotly-graph-div');
                    if (plotlyElements.length > 0) {
                        const plotlyDiv = plotlyElements[0].id;
                        
                        // Проверяем, является ли окно частью модального окна
                        const isModal = window.location.href.includes('modal=true') || 
                                       window.parent.document.getElementById('viz-container') !== null;
                        
                        window.parent.postMessage({
                            type: isModal ? 'plotly-modal-ready' : 'plotly-ready',
                            plotlyDiv: plotlyDiv,
                            dimensions: {
                                width: plotlyElements[0].clientWidth,
                                height: plotlyElements[0].clientHeight
                            }
                        }, '*');
                        
                        console.log('[PlotlyResize] Уведомление о готовности отправлено (' + (isModal ? 'модальное' : 'стандартное') + ')');
                    } else {
                        setTimeout(notifyParentWhenPlotlyReady, 200);
                    }
                } else {
                    setTimeout(notifyParentWhenPlotlyReady, 200);
                }
            }
            
            // MutationObserver для отслеживания изменений в DOM
            function setupMutationObserver() {
                const observer = new MutationObserver((mutations) => {
                    for (const mutation of mutations) {
                        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                            for (const node of mutation.addedNodes) {
                                if (node.nodeType === Node.ELEMENT_NODE && 
                                   (node.classList?.contains('plotly-graph-div') || 
                                    node.querySelector?.('.plotly-graph-div'))) {
                                    notifyParentWhenPlotlyReady();
                                    return;
                                }
                            }
                        }
                    }
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            }
            
            // Запуск проверки готовности Plotly
            if (document.readyState === 'complete' || document.readyState === 'interactive') {
                notifyParentWhenPlotlyReady();
                setupMutationObserver();
            } else {
                document.addEventListener('DOMContentLoaded', () => {
                    notifyParentWhenPlotlyReady();
                    setupMutationObserver();
                });
            }
        })();
        `;
        
        const scriptElement = document.createElement('script');
        scriptElement.id = 'enhanced-plotly-resizer';
        scriptElement.textContent = script;
        document.head.appendChild(scriptElement);
    }

    // Обработчик сообщений для модальных окон
    function handleModalMessages(event) {
        try {
            const data = event.data;
            
            if (data && data.type === 'plotly-modal-ready') {
                utils.log('Получено сообщение о готовности Plotly в модальном окне');
                
                // Находим iframe в модальном окне
                const modalIframe = document.querySelector('#viz-container iframe');
                if (modalIframe && modalIframe.contentWindow === event.source) {
                    // Получаем размеры контейнера
                    const container = document.getElementById('viz-container');
                    if (container) {
                        const width = container.clientWidth;
                        const height = container.clientHeight;
                        
                        // Отправляем сообщение о размерах
                        event.source.postMessage({
                            type: 'resize-plotly',
                            width: width,
                            height: height,
                            plotlyDiv: data.plotlyDiv
                        }, '*');
                        
                        utils.log(`Отправлен запрос на изменение размера графика в модальном окне: ${width}x${height}`);
                    }
                }
            }
        } catch (e) {
            utils.log(`Ошибка при обработке сообщения: ${e.message}`, 'error');
        }
    }

    // Основная функция инициализации
    function init() {
        utils.log('Инициализация адаптера графиков...');
        
        // Инъекция скрипта для iframe с улучшенным обработчиком
        injectEnhancedIframeScript();
        
        // Инициализация обработчиков
        directChartHandler.init();
        iframeChartHandler.init();
        
        // Настройка наблюдателей
        const intersectionObserver = observers.setupIntersectionObserver();
        const resizeObserver = observers.setupResizeObserver();
        const mutationObserver = observers.setupMutationObserver();
        
        // Обработчик изменения размера окна
        const windowResizeHandler = utils.debounce(() => {
            utils.log('Изменение размера окна, обновляем все графики...');
            directChartHandler.resizeAllCharts();
            iframeChartHandler.resizeAllIframeCharts();
        }, config.resizeDelay);
        
        // Добавляем слушатель события resize
        window.addEventListener('resize', windowResizeHandler);
        
        // Добавляем слушатель сообщений для модальных окон
        window.addEventListener('message', handleModalMessages);
        
        utils.log('Инициализация адаптера графиков завершена');
    }

    // Запуск инициализации при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();