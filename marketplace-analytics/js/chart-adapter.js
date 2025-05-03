/**
 * chart-adapter.js
 * 
 * Адаптивное изменение размеров визуализаций Plotly
 * Обеспечивает корректное отображение графиков в различных контейнерах
 * и при изменении размеров окна
 * 
 * @version 1.1.0
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
                    timeout = null;
                    func.apply(this, args);
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
            // Логика инициализации...
        },
        
        // Изменение размера всех прямых графиков
        resizeAllCharts: function() {
            // Логика изменения размера...
        },
        
        // Изменение размера конкретного графика
        resizeChart: function(chartElement, parentElement) {
            // Логика изменения размера конкретного графика...
        }
    };

    // Обработчик iframe с графиками Plotly
    const iframeChartHandler = {
        // Инициализация системы адаптации для iframe
        init: function() {
            // Исправленный метод findAndRegisterIframes
            this.findAndRegisterIframes = function() {
                const iframes = document.querySelectorAll(config.selectors.iframe);
                if (iframes.length === 0) {
                    utils.log('Не найдены iframe с визуализациями', 'warn');
                    return;
                }
                
                utils.log(`Найдено ${iframes.length} iframe для регистрации`);
                iframes.forEach(iframe => {
                    // Добавление уникального ID, если его нет
                    if (!iframe.id) {
                        iframe.id = 'chart-iframe-' + Math.random().toString(36).substring(2, 15);
                    }
                    
                    // Регистрация iframe для последующей обработки
                    chartRegistry.set(iframe.id, {
                        iframe: iframe,
                        container: iframe.parentElement
                    });
                    
                    // Инжекция скрипта для адаптивности
                    this.injectScriptToIframe(iframe);
                });
            };
            
            // Вызываем метод поиска и регистрации iframe
            this.findAndRegisterIframes();
            
            // Обработка сообщений от iframe
            window.addEventListener('message', this.handleIframeMessage.bind(this));
        },
        
        // Обработка сообщений от iframe для ресайзинга
        handleIframeMessage: function(event) {
            try {
                const message = event.data;
                if (message && message.type === 'resize-request') {
                    const iframeId = message.iframeId;
                    if (iframeId && chartRegistry.has(iframeId)) {
                        utils.log(`Получен запрос на изменение размера от iframe ${iframeId}`);
                        // Дополнительная логика по необходимости
                    }
                }
            } catch (error) {
                utils.log(`Ошибка обработки сообщения от iframe: ${error.message}`, 'error');
            }
        },
        
        // Метод для изменения размера всех iframe с диаграммами
        resizeAllIframeCharts: function() {
            chartRegistry.forEach((info, iframeId) => {
                if (info.iframe && info.container) {
                    try {
                        const containerSize = utils.getContentSize(info.container);
                        utils.log(`Изменение размера iframe ${iframeId}: ${containerSize.width}x${containerSize.height}`);
                        // Дополнительная логика изменения размера
                    } catch (e) {
                        utils.log(`Ошибка при изменении размера iframe ${iframeId}: ${e.message}`, 'error');
                    }
                }
            });
        },
        
        // Метод, который использует injectEnhancedIframeScript
        // Теперь использует модуль iframeScriptInjector
        injectScriptToIframe: function(iframe) {
            try {
                // Проверяем доступность модуля инжекции скриптов
                if (window.iframeScriptInjector && window.iframeScriptInjector.injectEnhancedIframeScript) {
                    // Используем модуль для инжекции скрипта
                    window.iframeScriptInjector.injectEnhancedIframeScript();
                    return true;
                } else {
                    utils.log('Модуль iframeScriptInjector недоступен', 'warn');
                    return false;
                }
            } catch (e) {
                utils.log(`Ошибка при инжекции скрипта: ${e.message}`, 'error');
                return false;
            }
        }
        
        // Остальные методы...
    };

    // Настройка наблюдателей за изменениями
    const observers = {
        // Настройка Intersection Observer для ленивой инициализации
        setupIntersectionObserver: function() {
            // Логика настройки...
        },
        
        // Настройка Resize Observer для отслеживания изменений размеров
        setupResizeObserver: function() {
            // Логика настройки...
        },
        
        // Настройка MutationObserver для отслеживания динамически добавленных элементов
        setupMutationObserver: function() {
            // Логика настройки...
        }
    };

    // Обработчик сообщений для модальных окон
    function handleModalMessages(event) {
        // Логика обработки сообщений...
    }

    // Функция для явного повторного запроса на изменение размеров
    window.resizeModalChart = function(modalId) {
        // Логика изменения размера...
    };

    // Основная функция инициализации
    function init() {
        // Проверка зависимостей
        if (!window.iframeScriptInjector) {
            utils.log('Необходимая зависимость iframeScriptInjector не найдена, пробуем загрузить.', 'warn');
            
            // Динамическая загрузка модуля, если его нет
            const script = document.createElement('script');
            script.src = 'js/iframe-script-injector.js';
            script.async = true;
            script.onload = function() {
                utils.log('Модуль iframe-script-injector.js успешно загружен');
                initAfterDependencies();
            };
            script.onerror = function() {
                utils.log('Не удалось загрузить iframe-script-injector.js', 'error');
            };
            document.head.appendChild(script);
        } else {
            // Если зависимости доступны, продолжаем инициализацию
            initAfterDependencies();
        }
        
        function initAfterDependencies() {
            // Инициализация обработчиков
            directChartHandler.init();
            iframeChartHandler.init();
            
            // Настройка наблюдателей
            observers.setupIntersectionObserver();
            observers.setupResizeObserver();
            observers.setupMutationObserver();
            
            // Обработчик изменения размера окна
            window.addEventListener('resize', utils.debounce(() => {
                directChartHandler.resizeAllCharts();
                iframeChartHandler.resizeAllIframeCharts();
            }, config.resizeDelay));
            
            // Делаем iframeChartHandler доступным глобально для использования в других модулях
            window.iframeChartHandler = iframeChartHandler;
            
            utils.log('chart-adapter.js успешно инициализирован');
        }
    }

    // Запуск инициализации при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();