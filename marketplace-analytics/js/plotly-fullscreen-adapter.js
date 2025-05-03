/**
 * Plotly Fullscreen Adapter
 * 
 * Специализированный модуль для оптимизации диаграмм Plotly в полноэкранном режиме.
 * Анализирует типы диаграмм и применяет оптимальные настройки для корректного отображения
 * с учётом специфики различных типов визуализаций.
 * 
 * @version 1.0.0
 */

(function() {
    'use strict';
    
    // ========================
    // Конфигурация
    // ========================
    const config = {
        // Пути к ресурсам
        paths: {
            visualizations: '../analytics_output/visualizations/'
        },
        
        // Селекторы
        selectors: {
            fullscreenModal: '#vizFullscreenModal',
            fullscreenContainer: '#fullscreen-viz-container',
            iframe: '.viz-modal-iframe'
        },
        
        // Настройки типов диаграмм
        chartTypes: {
            pie: {
                margins: {
                    l: 30,
                    r: 160,
                    t: 50,
                    b: 50
                },
                legendConfig: {
                    orientation: 'v',
                    xanchor: 'left',
                    x: 1.05
                }
            },
            bar: {
                margins: {
                    l: 80,
                    r: 40,
                    t: 60,
                    b: 100
                }
            },
            line: {
                margins: {
                    l: 60,
                    r: 20,
                    t: 50,
                    b: 60
                }
            },
            // Добавляем специальные настройки для scatter-диаграмм
            scatter: {
                margins: {
                    l: 70,  // Увеличенный отступ слева для меток оси Y
                    r: 30,  // Умеренный отступ справа
                    t: 50,  // Отступ сверху для заголовка
                    b: 70   // Увеличенный отступ снизу для меток оси X
                },
                // Добавляем специфические настройки для scatter-диаграмм
                scatterConfig: {
                    mode: 'markers',
                    marker: {
                        size: 12,
                        opacity: 0.8
                    }
                }
            },
            default: {
                margins: {
                    l: 50,
                    r: 50,
                    t: 50,
                    b: 50
                }
            }
        },
        
        // Режим отладки (true/false)
        debug: false
    };
    
    // ========================
    // Вспомогательные функции
    // ========================
    const utils = {
        // Логирование с префиксом
        log: function(message, level = 'info') {
            if (!config.debug && level !== 'error') return;
            
            const prefix = '[PlotlyFullscreen]';
            
            switch (level) {
                case 'error':
                    console.error(`${prefix} ${message}`);
                    break;
                case 'warn':
                    console.warn(`${prefix} ${message}`);
                    break;
                case 'info':
                default:
                    console.log(`${prefix} ${message}`);
                    break;
            }
        },
        
        // Получение DOM элемента
        getElement: function(selector, parent = document) {
            try {
                return parent.querySelector(selector);
            } catch (e) {
                utils.log(`Ошибка при получении элемента ${selector}: ${e.message}`, 'error');
                return null;
            }
        },
        
        // Определение типа диаграммы
        detectChartType: function(iframeDocument) {
            if (!iframeDocument) return 'unknown';
            
            const plotlyDivs = iframeDocument.querySelectorAll('.plotly-graph-div');
            if (plotlyDivs.length === 0) return 'unknown';
            
            const plotlyDiv = plotlyDivs[0];
            
            try {
                // Проверка по DOM элементам
                if (plotlyDiv.querySelector('.pielayer')) {
                    return 'pie';
                } else if (plotlyDiv.querySelector('.barlayer')) {
                    return 'bar';
                } else if (plotlyDiv.querySelector('.scatterlayer')) {
                    // Улучшенная логика определения scatter vs line
                    // Проверяем наличие линий и маркеров
                    const hasLines = plotlyDiv.querySelector('.scatterlayer .lines');
                    const hasMarkers = plotlyDiv.querySelector('.scatterlayer .points');
                    
                    // Если есть только маркеры без линий - это scatter
                    // Если есть и линии, и маркеры - это line+markers (считаем как line)
                    // Если есть только линии - это line
                    if (hasMarkers && !hasLines) {
                        return 'scatter';
                    } else if (hasLines) {
                        return 'line';
                    } else {
                        // По умолчанию считаем как scatter, если не смогли точно определить
                        return 'scatter';
                    }
                }
            } catch (e) {
                utils.log(`Ошибка при определении типа диаграммы: ${e.message}`, 'warn');
            }
            
            return 'unknown';
        },
        
        // Расчет оптимизированных настроек
        getOptimizedLayout: function(chartType, width, height) {
            const typeConfig = config.chartTypes[chartType] || config.chartTypes.default;
            const fontSize = Math.max(10, Math.min(14, width / 60));
            
            // Базовые настройки для всех типов
            const layout = {
                width: width,
                height: height,
                autosize: true,
                font: {
                    family: 'Inter, sans-serif',
                    size: fontSize
                },
                margin: { ...typeConfig.margins }
            };
            
            // Специфичные настройки для типа диаграммы
            switch (chartType) {
                case 'pie':
                    Object.assign(layout, {
                        legend: {
                            font: { size: fontSize },
                            ...typeConfig.legendConfig
                        }
                    });
                    break;
                    
                case 'bar':
                    Object.assign(layout, {
                        xaxis: {
                            tickangle: width < 500 ? -45 : 0,
                            tickfont: { size: fontSize }
                        },
                        yaxis: {
                            tickfont: { size: fontSize }
                        }
                    });
                    break;
                    
                case 'line':
                    Object.assign(layout, {
                        xaxis: {
                            tickfont: { size: fontSize }
                        },
                        yaxis: {
                            tickfont: { size: fontSize }
                        },
                        legend: {
                            font: { size: fontSize }
                        }
                    });
                    break;
                    
                case 'scatter':
                    // Специальные настройки для scatter-диаграмм
                    Object.assign(layout, {
                        xaxis: {
                            tickfont: { size: fontSize },
                            showgrid: true,
                            gridcolor: 'rgba(0,0,0,0.1)',
                            zeroline: true,
                            zerolinecolor: 'rgba(0,0,0,0.2)'
                        },
                        yaxis: {
                            tickfont: { size: fontSize },
                            showgrid: true,
                            gridcolor: 'rgba(0,0,0,0.1)',
                            zeroline: true,
                            zerolinecolor: 'rgba(0,0,0,0.2)'
                        },
                        legend: {
                            font: { size: fontSize },
                            bgcolor: 'rgba(255,255,255,0.7)',
                            bordercolor: 'rgba(0,0,0,0.1)',
                            borderwidth: 1
                        }
                    });
                    break;
            }
            
            return layout;
        }
    };
    
    // ========================
    // Основная функциональность
    // ========================
    const plotlyFullscreenAdapter = {
        // Инициализация всех обработчиков
        init: function() {
            utils.log('Инициализация адаптера полноэкранного режима');
            
            // Добавление обработчика событий для модального окна
            const fullscreenModal = utils.getElement(config.selectors.fullscreenModal);
            if (fullscreenModal) {
                fullscreenModal.addEventListener('shown.bs.modal', this.handleModalShown.bind(this));
                window.addEventListener('resize', this.handleResize.bind(this));
            }
            
            // Сохраняем ссылку на старую функцию setupFullscreenButton, если она существует
            if (window.setupFullscreenButton) {
                this._originalSetupFullscreenButton = window.setupFullscreenButton;
            }
            
            utils.log('Адаптер полноэкранного режима инициализирован');
        },
        
        // Обработка события открытия модального окна
        handleModalShown: function() {
            utils.log('Модальное окно открыто, оптимизируем диаграмму');
            
            // Добавляем многократные попытки оптимизации с возрастающими интервалами
            this.scheduleResizeAttempts();
        },

        // Новый метод для планирования нескольких попыток оптимизации
        scheduleResizeAttempts: function() {
            const container = utils.getElement(config.selectors.fullscreenContainer);
            if (!container) {
                utils.log('Контейнер не найден', 'error');
                return;
            }
            
            const iframe = utils.getElement(config.selectors.iframe, container);
            if (!iframe) {
                utils.log('iframe не найден', 'error');
                return;
            }
            
            // Пробуем получить тип диаграммы из URL
            const urlParams = new URLSearchParams(iframe.src.split('?')[1] || '');
            const chartTypeFromUrl = urlParams.get('chart_type');
            
            // Поэтапные попытки с экспоненциально увеличивающимся интервалом
            const attemptIntervals = [100, 300, 600, 1000, 1500];
            let attemptCount = 0;
            
            const attemptResize = () => {
                utils.log(`Попытка оптимизации #${attemptCount + 1}`);
                
                try {
                    this.optimizeChart(iframe, chartTypeFromUrl)
                        .then(() => utils.log(`Попытка #${attemptCount + 1} успешна`))
                        .catch(err => utils.log(`Ошибка в попытке #${attemptCount + 1}: ${err.message}`, 'warn'));
                } catch (e) {
                    utils.log(`Исключение в попытке #${attemptCount + 1}: ${e.message}`, 'error');
                }
                
                attemptCount++;
                if (attemptCount < attemptIntervals.length) {
                    setTimeout(attemptResize, attemptIntervals[attemptCount]);
                }
            };
            
            // Начинаем первую попытку
            setTimeout(attemptResize, attemptIntervals[0]);
        },
        
        // Обработка события изменения размера окна
        handleResize: function() {
            const fullscreenModal = utils.getElement(config.selectors.fullscreenModal);
            if (!fullscreenModal || !fullscreenModal.classList.contains('show')) return;
            
            const container = utils.getElement(config.selectors.fullscreenContainer);
            if (!container) return;
            
            const iframe = utils.getElement(config.selectors.iframe, container);
            if (!iframe) return;
            
            // Используем debounce для оптимизации
            clearTimeout(this._resizeTimer);
            this._resizeTimer = setTimeout(() => {
                this.optimizeChart(iframe);
            }, 250);
        },
        
        // Оптимизация диаграммы с возможностью указать тип
        optimizeChart: function(iframe, knownChartType) {
            if (!iframe || !iframe.contentWindow) {
                utils.log('Iframe не предоставлен или недоступен', 'error');
                return Promise.reject(new Error('Iframe недоступен'));
            }
            
            // Добавляем проверку видимости и размеров контейнера
            const container = iframe.parentElement;
            if (!container || container.clientWidth === 0 || container.clientHeight === 0) {
                utils.log('Контейнер не виден или имеет нулевые размеры', 'error');
                return Promise.reject(new Error('Недопустимые размеры контейнера'));
            }
            
            // Далее идет существующий код с дополнительными проверками и обработкой ошибок
            return this._waitForIframeLoad(iframe)
                .then(() => {
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    const iframeWin = iframe.contentWindow;
                    
                    // Проверяем доступность Plotly
                    if (!iframeWin.Plotly) {
                        throw new Error('Plotly не найден в iframe');
                    }
                    
                    // Находим элемент диаграммы
                    const plotlyDiv = iframeDoc.querySelector('.plotly-graph-div');
                    if (!plotlyDiv) {
                        throw new Error('Элемент диаграммы не найден');
                    }
                    
                    // Определяем тип диаграммы, используя известный тип если указан
                    const chartType = knownChartType || utils.detectChartType(iframeDoc);
                    utils.log(`Обнаружен тип диаграммы: ${chartType}`);
                    
                    // Получаем размеры контейнера
                    const width = container.clientWidth;
                    const height = container.clientHeight;
                    
                    // Дополнительная проверка размеров после получения
                    if (width < 50 || height < 50) {
                        utils.log(`Слишком малые размеры контейнера: ${width}x${height}`, 'warn');
                        // Используем резервные размеры, если фактические слишком малы
                        width = Math.max(width, 800);
                        height = Math.max(height, 600);
                    }
                    
                    // Создаем оптимизированный layout
                    const optimizedLayout = utils.getOptimizedLayout(chartType, width, height);
                    
                    // Применяем layout
                    utils.log('Применяем оптимизированный layout');
                    return iframeWin.Plotly.relayout(plotlyDiv, optimizedLayout);
                })
                .then(() => {
                    utils.log('Диаграмма успешно оптимизирована');
                    return true;
                })
                .catch(err => {
                    // Улучшенная обработка ошибок
                    utils.log(`Ошибка при оптимизации: ${err.message}`, 'error');
                    
                    // Применяем запасной вариант для решения проблемы
                    this._tryFallbackOptimization(iframe, knownChartType);
                    
                    // Возвращаем отклоненный Promise для обработки ошибки вызывающей стороной
                    return Promise.reject(err);
                });
        },

        // Новый метод для запасной стратегии оптимизации
        _tryFallbackOptimization: function(iframe, chartType) {
            try {
                utils.log('Применяем запасную стратегию оптимизации', 'warn');
                
                if (!iframe || !iframe.contentWindow) return;
                
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const plotlyDiv = iframeDoc.querySelector('.plotly-graph-div');
                
                if (!plotlyDiv || !iframe.contentWindow.Plotly) return;
                
                // Получаем размеры контейнера
                const container = iframe.parentElement;
                const width = container.clientWidth;
                const height = container.clientHeight;
                
                // Принудительно устанавливаем размеры через прямой вызов API
                iframe.contentWindow.Plotly.relayout(plotlyDiv, {
                    width: width,
                    height: height,
                    'autosize': true
                });
                
                utils.log('Запасная оптимизация применена', 'info');
            } catch (e) {
                utils.log(`Ошибка в запасной оптимизации: ${e.message}`, 'error');
            }
        },
        
        // Ожидание загрузки iframe
        _waitForIframeLoad: function(iframe, timeout = 2000) {
            return new Promise((resolve, reject) => {
                // Если iframe уже загружен
                if (iframe.contentDocument && 
                    iframe.contentWindow && 
                    iframe.contentWindow.document.readyState === 'complete') {
                    resolve();
                    return;
                }
                
                // Устанавливаем таймаут
                const timeoutId = setTimeout(() => {
                    utils.log('Таймаут ожидания загрузки iframe', 'warn');
                    reject(new Error('Таймаут ожидания загрузки iframe'));
                }, timeout);
                
                // Ожидаем загрузки
                const handleLoad = () => {
                    clearTimeout(timeoutId);
                    iframe.removeEventListener('load', handleLoad);
                    resolve();
                };
                
                iframe.addEventListener('load', handleLoad);
            });
        }
    };
    
    // ========================
    // Инициализация и экспорт
    // ========================
    
    // Интеграция с существующим модальным окном
    function enhanceModalHelpers() {
        if (typeof window.setupFullscreenButton === 'function') {
            // Сохраняем оригинальную функцию
            const originalSetupFullscreenButton = window.setupFullscreenButton;
            
            // Расширяем функцию
            window.setupFullscreenButton = function() {
                // Вызываем оригинальную функцию
                originalSetupFullscreenButton.apply(this, arguments);
                
                const fullscreenBtn = document.getElementById('fullscreen-btn');
                if (!fullscreenBtn) return;
                
                // Удаляем все существующие обработчики
                const newBtn = fullscreenBtn.cloneNode(true);
                if (fullscreenBtn.parentNode) {
                    fullscreenBtn.parentNode.replaceChild(newBtn, fullscreenBtn);
                }
                
                // Добавляем обработчик
                newBtn.addEventListener('click', function() {
                    const vizModal = document.getElementById('vizModal');
                    const vizFullscreenModal = document.getElementById('vizFullscreenModal');
                    
                    // Копирование содержимого между модальными окнами
                    const sourceContainer = document.getElementById('viz-container');
                    const targetContainer = document.getElementById('fullscreen-viz-container');
                    
                    if (sourceContainer && targetContainer) {
                        const originalIframe = sourceContainer.querySelector('iframe');
                        if (!originalIframe) return;
                        
                        // Очищаем целевой контейнер
                        targetContainer.innerHTML = '';
                        
                        // Создаем новый iframe
                        const newIframe = document.createElement('iframe');
                        newIframe.className = 'viz-modal-iframe';
                        newIframe.id = 'fullscreen-viz-iframe-' + Date.now();
                        newIframe.style.width = '100%';
                        newIframe.style.height = '100%';
                        newIframe.style.border = 'none';
                        newIframe.src = originalIframe.src;
                        
                        // Добавляем loader
                        const loaderDiv = document.createElement('div');
                        loaderDiv.className = 'visualization-loader';
                        loaderDiv.innerHTML = '<div class="visualization-spinner"></div>';
                        targetContainer.appendChild(loaderDiv);
                        
                        // Добавляем iframe в целевой контейнер
                        targetContainer.appendChild(newIframe);
                        
                        // Закрываем обычное модальное окно
                        if (window.bootstrap && vizModal) {
                            const modalInstance = bootstrap.Modal.getInstance(vizModal);
                            if (modalInstance) modalInstance.hide();
                        }
                        
                        // Открываем полноэкранное модальное окно
                        if (window.bootstrap && vizFullscreenModal) {
                            const fullscreenModalInstance = new bootstrap.Modal(vizFullscreenModal);
                            fullscreenModalInstance.show();
                        }
                        
                        // Скрываем лоадер после загрузки iframe
                        newIframe.onload = function() {
                            loaderDiv.style.display = 'none';
                        };
                    }
                });
            };
        }
    }
    
    // Автоматическая инициализация при загрузке документа
    function init() {
        try {
            // Усиление модальных хелперов
            enhanceModalHelpers();
            
            // Инициализация адаптера
            plotlyFullscreenAdapter.init();
            
            // Если модальные хелперы уже инициализированы, повторяем настройку
            if (document.getElementById('fullscreen-btn')) {
                window.setupFullscreenButton();
            }
        } catch (e) {
            utils.log(`Ошибка инициализации: ${e.message}`, 'error');
        }
    }
    
    // Инициализация после загрузки DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Экспорт публичного API
    window.plotlyFullscreenAdapter = {
        optimizeChart: function(iframe) {
            return plotlyFullscreenAdapter.optimizeChart(iframe);
        }
    };
})();