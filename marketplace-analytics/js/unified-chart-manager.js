/**
 * Unified Chart Manager
 * 
 * Централизованное управление визуализациями с явной архитектурой зависимостей
 * Обеспечивает:
 * - Единый контроль жизненного цикла диаграмм
 * - Оптимизированное обновление с минимальным количеством рендеров
 * - Кэширование конфигураций для различных диаграмм
 * - Четкий интерфейс для сторонних модулей
 * 
 * @version 1.0.0
 */
(function() {
    'use strict';

    // ========================
    // Конфигурация
    // ========================
    const config = {
        // Селекторы для поиска элементов
        selectors: {
            visualizationCard: '.visualization-card',
            visualizationContent: '.visualization-content',
            iframe: '.visualization-iframe, .viz-modal-iframe',
            fullscreenModal: '#vizFullscreenModal',
            fullscreenContainer: '#fullscreen-viz-container',
            standardModal: '#vizModal',
            standardContainer: '#viz-container'
        },
        
        // Настройки для диаграмм разных типов
        chartTypes: {
            pie: {
                margins: {
                    l: 30,
                    r: 160,
                    t: 50,
                    b: 50,
                    pad: 5
                },
                legend: {
                    orientation: 'v',
                    xanchor: 'left',
                    x: 1.05,
                    yanchor: 'middle',
                    y: 0.5
                }
            },
            bar: {
                margins: {
                    l: 80,
                    r: 40,
                    t: 60,
                    b: 100,
                    pad: 5
                },
                barmode: 'group'
            },
            line: {
                margins: {
                    l: 60,
                    r: 20,
                    t: 50,
                    b: 60,
                    pad: 5
                }
            },
            scatter: {
                margins: {
                    l: 60,
                    r: 20,
                    t: 50,
                    b: 60,
                    pad: 5
                }
            },
            default: {
                margins: {
                    l: 50,
                    r: 50,
                    t: 50,
                    b: 50,
                    pad: 5
                }
            }
        },
        
        // Таймауты
        timeouts: {
            resizeDelay: 200,
            analyzeDelay: 50,
            resizeRetryDelay: 100
        },
        
        // Настройки отладки
        debug: false
    };

    // ========================
    // Служебные объекты
    // ========================
    
    // Хранение состояния диаграмм
    const state = {
        // Кэш анализов диаграмм: Map<iframeId, {type, features, optimalLayout}>
        chartAnalysisCache: new Map(),
        
        // Текущие размеры диаграмм: Map<iframeId, {width, height}>
        chartSizes: new Map(),
        
        // Состояния отрисовки для избежания лишних обновлений: Map<iframeId, Boolean>
        renderingState: new Map(),
        
        // Информация о ресурсах, требующих очистки
        cleanupRegistry: {
            eventHandlers: [],
            observers: []
        }
    };
    
    // Утилиты
    const utils = {
        // Защищенный лог с уровнями и префиксом
        log: function(message, level = 'info') {
            const prefix = '[UnifiedChartMgr]';
            
            if (!config.debug && level !== 'error') return;
            
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
        
        // Debounce для оптимизации обработки частых событий
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
        
        // Получение элемента с обработкой ошибок
        getElement: function(selector, parent = document) {
            try {
                return parent.querySelector(selector);
            } catch (e) {
                utils.log(`Ошибка при получении элемента ${selector}: ${e.message}`, 'error');
                return null;
            }
        },
        
        // Безопасный доступ к содержимому iframe
        getIframeContents: function(iframe) {
            if (!iframe) return null;
            
            try {
                return {
                    document: iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document),
                    window: iframe.contentWindow
                };
            } catch (e) {
                utils.log(`Ошибка доступа к содержимому iframe: ${e.message}`, 'error');
                return null;
            }
        },
        
        // Вычисление оптимальных размеров для текстовых элементов
        calculateOptimalTextSizes: function(width, height) {
            return {
                title: Math.max(14, Math.min(20, width / 40)),
                axis: Math.max(10, Math.min(14, width / 60)),
                legend: Math.max(10, Math.min(12, width / 70)),
                annotation: Math.max(12, Math.min(16, width / 50))
            };
        },
        
        // Измерение размеров контейнера с учетом padding
        getContentSize: function(element) {
            if (!element) return { width: 0, height: 0 };
            
            const style = window.getComputedStyle(element);
            const paddingX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
            const paddingY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
            
            return {
                width: element.clientWidth - paddingX,
                height: element.clientHeight - paddingY
            };
        },
        
        // Регистрация обработчика события с возможностью очистки
        registerEventHandler: function(element, eventType, handler, options) {
            if (!element) return;
            
            element.addEventListener(eventType, handler, options);
            
            // Регистрируем для последующей очистки
            state.cleanupRegistry.eventHandlers.push({
                element,
                eventType,
                handler,
                options
            });
        },
        
        // Безопасная очистка всех зарегистрированных обработчиков
        cleanupEventHandlers: function() {
            state.cleanupRegistry.eventHandlers.forEach(entry => {
                try {
                    entry.element.removeEventListener(entry.eventType, entry.handler, entry.options);
                } catch (e) {
                    utils.log(`Ошибка при удалении обработчика: ${e.message}`, 'warn');
                }
            });
            
            state.cleanupRegistry.eventHandlers = [];
        },
        
        // Создание уникального идентификатора для элементов
        generateUniqueId: function(prefix = 'chart') {
            return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
        },
        
        // Определение типа диаграммы из iframe
        detectChartType: function(iframe) {
            const contents = utils.getIframeContents(iframe);
            if (!contents || !contents.document) return 'unknown';
            
            const plotlyDivs = contents.document.querySelectorAll('.plotly-graph-div');
            if (plotlyDivs.length === 0) return 'unknown';
            
            const plotlyDiv = plotlyDivs[0];
            
            // Попытка определения через DOM-элементы
            try {
                if (plotlyDiv.querySelector('.pielayer')) {
                    return 'pie';
                } else if (plotlyDiv.querySelector('.barlayer')) {
                    return 'bar';
                } else if (plotlyDiv.querySelector('.scatterlayer')) {
                    // Определяем: это линейный график или точечная диаграмма?
                    const hasLines = plotlyDiv.querySelector('.scatterlayer .lines');
                    return hasLines ? 'line' : 'scatter';
                }
            } catch (e) {
                utils.log(`Ошибка при анализе DOM диаграммы: ${e.message}`, 'warn');
            }
            
            // Попытка получения через API Plotly, если доступно
            try {
                if (contents.window.Plotly && plotlyDiv._fullData && plotlyDiv._fullData.length > 0) {
                    const firstTrace = plotlyDiv._fullData[0];
                    
                    if (firstTrace.type === 'pie') {
                        return 'pie';
                    } else if (firstTrace.type === 'bar') {
                        return 'bar';
                    } else if (firstTrace.type === 'scatter') {
                        return firstTrace.mode && firstTrace.mode.includes('lines') ? 'line' : 'scatter';
                    }
                }
            } catch (e) {
                utils.log(`Ошибка при анализе данных Plotly: ${e.message}`, 'warn');
            }
            
            return 'unknown';
        }
    };

    // ========================
    // Основные функции
    // ========================
    
    /**
     * Анализатор диаграмм
     * Собирает и кэширует информацию о диаграммах для оптимального отображения
     */
    const chartAnalyzer = {
        // Комплексный анализ диаграммы с кэшированием результатов
        analyzeChart: function(iframe) {
            if (!iframe) {
                utils.log('Не передан iframe для анализа', 'warn');
                return null;
            }
            
            const iframeId = iframe.id || utils.generateUniqueId('iframe');
            if (!iframe.id) iframe.id = iframeId;
            
            // Проверка кэша
            if (state.chartAnalysisCache.has(iframeId)) {
                utils.log(`Использую кэшированный анализ для ${iframeId}`);
                return state.chartAnalysisCache.get(iframeId);
            }
            
            utils.log(`Выполняю анализ диаграммы в iframe ${iframeId}`);
            
            const contents = utils.getIframeContents(iframe);
            if (!contents || !contents.document || !contents.window) {
                utils.log('Не удалось получить содержимое iframe', 'error');
                return null;
            }
            
            // Определяем тип диаграммы
            const chartType = utils.detectChartType(iframe);
            utils.log(`Определен тип диаграммы: ${chartType}`);
            
            // Собираем особенности диаграммы
            const features = this.collectChartFeatures(iframe, chartType);
            
            // Создаем результат анализа
            const analysisResult = {
                iframeId: iframeId,
                chartType: chartType,
                features: features,
                timestamp: Date.now()
            };
            
            // Кэшируем результат
            state.chartAnalysisCache.set(iframeId, analysisResult);
            
            return analysisResult;
        },
        
        // Сбор особенностей диаграммы для оптимизации отображения
        collectChartFeatures: function(iframe, chartType) {
            const features = {
                hasLegend: false,
                hasAnnotations: false,
                hasTitle: false,
                hasAxisTitles: false,
                dataPointsCount: 0,
                tracesCount: 0
            };
            
            try {
                const contents = utils.getIframeContents(iframe);
                if (!contents || !contents.document) return features;
                
                const plotlyDivs = contents.document.querySelectorAll('.plotly-graph-div');
                if (plotlyDivs.length === 0) return features;
                
                const plotlyDiv = plotlyDivs[0];
                
                // Проверка наличия легенды
                features.hasLegend = !!plotlyDiv.querySelector('.legend');
                
                // Проверка наличия аннотаций
                features.hasAnnotations = !!plotlyDiv.querySelector('.annotation');
                
                // Проверка наличия заголовка
                features.hasTitle = !!plotlyDiv.querySelector('.gtitle');
                
                // Проверка наличия заголовков осей
                features.hasAxisTitles = 
                    !!plotlyDiv.querySelector('.xtitle') || 
                    !!plotlyDiv.querySelector('.ytitle');
                
                // Анализ данных через API Plotly, если доступно
                if (contents.window.Plotly && plotlyDiv._fullData) {
                    features.tracesCount = plotlyDiv._fullData.length;
                    
                    if (chartType === 'bar' || chartType === 'line' || chartType === 'scatter') {
                        // Подсчет общего количества точек данных для оценки сложности
                        features.dataPointsCount = plotlyDiv._fullData.reduce((total, trace) => {
                            return total + (trace.x ? trace.x.length : 0);
                        }, 0);
                    } else if (chartType === 'pie') {
                        // Для круговых диаграмм считаем количество секторов
                        features.dataPointsCount = plotlyDiv._fullData.reduce((total, trace) => {
                            return total + (trace.values ? trace.values.length : 0);
                        }, 0);
                    }
                }
                
                // Для столбчатых диаграмм дополнительно оцениваем длину подписей
                if (chartType === 'bar') {
                    const xAxisLabels = plotlyDiv.querySelectorAll('.xtick text');
                    let maxLabelLength = 0;
                    
                    xAxisLabels.forEach(label => {
                        maxLabelLength = Math.max(maxLabelLength, label.textContent.length);
                    });
                    
                    features.maxLabelLength = maxLabelLength;
                }
            } catch (e) {
                utils.log(`Ошибка при сборе особенностей диаграммы: ${e.message}`, 'warn');
            }
            
            return features;
        }
    };

    /**
     * Оптимизатор диаграмм
     * Создает и применяет оптимальные настройки для диаграмм различных типов
     */
    const chartOptimizer = {
        // Создание оптимизированного макета для диаграммы
        createOptimalLayout: function(analysis, width, height) {
            if (!analysis) {
                utils.log('Нет данных анализа для создания оптимального макета', 'warn');
                return null;
            }
            
            const { chartType, features } = analysis;
            const typeConfig = config.chartTypes[chartType] || config.chartTypes.default;
            const fontSizes = utils.calculateOptimalTextSizes(width, height);
            
            // Базовый макет с настройками для всех типов
            const baseLayout = {
                width: width,
                height: height,
                autosize: true,
                font: {
                    family: 'Inter, sans-serif',
                    size: fontSizes.axis
                },
                margin: this._calculateMargins(typeConfig.margins, features, width, height)
            };
            
            // Добавляем специфические настройки в зависимости от типа диаграммы
            let specificLayout = {};
            
            switch (chartType) {
                case 'pie':
                    specificLayout = this._optimizePieLayout(typeConfig, features, fontSizes, width, height);
                    break;
                    
                case 'bar':
                    specificLayout = this._optimizeBarLayout(typeConfig, features, fontSizes, width, height);
                    break;
                    
                case 'line':
                    specificLayout = this._optimizeLineLayout(typeConfig, features, fontSizes, width, height);
                    break;
                    
                case 'scatter':
                    specificLayout = this._optimizeScatterLayout(typeConfig, features, fontSizes, width, height);
                    break;
            }
            
            // Объединяем базовые и специфические настройки
            return Object.assign({}, baseLayout, specificLayout);
        },
        
        // Оптимальный расчет отступов в зависимости от особенностей диаграммы
        _calculateMargins: function(baseMargins, features, width, height) {
            const margins = Object.assign({}, baseMargins);
            
            // Увеличиваем отступы для заголовков осей
            if (features.hasAxisTitles) {
                margins.l = Math.max(margins.l, Math.floor(width * 0.12));
                margins.b = Math.max(margins.b, Math.floor(height * 0.15));
            }
            
            // Корректировка для длинных меток на оси X
            if (features.maxLabelLength && features.maxLabelLength > 10) {
                margins.b = Math.max(margins.b, Math.floor(height * 0.18));
            }
            
            // Увеличиваем правый отступ для легенды при большом количестве трейсов
            if (features.hasLegend && features.tracesCount > 3) {
                margins.r = Math.max(margins.r, Math.floor(width * 0.25));
            }
            
            return margins;
        },
        
        // Специфичные оптимизации для круговых диаграмм
        _optimizePieLayout: function(typeConfig, features, fontSizes, width, height) {
            const isWide = width > height * 1.2;
            
            // Оптимальное расположение легенды в зависимости от соотношения сторон
            const legendConfig = {
                orientation: isWide ? 'v' : 'h',
                x: isWide ? 1.02 : 0.5,
                y: isWide ? 0.5 : -0.15,
                xanchor: isWide ? 'left' : 'center',
                yanchor: isWide ? 'middle' : 'top',
                font: {
                    family: 'Inter, sans-serif',
                    size: fontSizes.legend
                },
                bgcolor: 'rgba(255,255,255,0.7)',
                bordercolor: 'rgba(0,0,0,0.1)',
                borderwidth: 1
            };
            
            return {
                legend: legendConfig,
                // Настройки для отображения текста внутри секторов
                textinfo: features.dataPointsCount > 10 ? 'percent' : 'percent+label',
                textposition: features.dataPointsCount > 10 ? 'inside' : 'auto',
                hoverinfo: 'label+percent+value'
            };
        },
        
        // Специфичные оптимизации для столбчатых диаграмм
        _optimizeBarLayout: function(typeConfig, features, fontSizes, width, height) {
            // Угол наклона подписей в зависимости от их длины
            const tickAngle = features.maxLabelLength > 8 ? -45 : 0;
            
            return {
                xaxis: {
                    tickangle: tickAngle,
                    tickfont: {
                        family: 'Inter, sans-serif',
                        size: fontSizes.axis
                    }
                },
                yaxis: {
                    tickfont: {
                        family: 'Inter, sans-serif',
                        size: fontSizes.axis
                    },
                    zeroline: true,
                    zerolinecolor: 'rgba(0,0,0,0.2)',
                    gridcolor: 'rgba(0,0,0,0.1)',
                    showgrid: true
                },
                bargap: 0.2,
                bargroupgap: 0.1
            };
        },
        
        // Специфичные оптимизации для линейных графиков
        _optimizeLineLayout: function(typeConfig, features, fontSizes, width, height) {
            return {
                xaxis: {
                    showgrid: true,
                    gridcolor: 'rgba(0,0,0,0.1)',
                    tickfont: {
                        family: 'Inter, sans-serif',
                        size: fontSizes.axis
                    }
                },
                yaxis: {
                    showgrid: true,
                    gridcolor: 'rgba(0,0,0,0.1)',
                    tickfont: {
                        family: 'Inter, sans-serif',
                        size: fontSizes.axis
                    }
                },
                legend: {
                    orientation: 'h',
                    y: -0.2,
                    x: 0.5,
                    xanchor: 'center',
                    yanchor: 'top',
                    font: {
                        family: 'Inter, sans-serif',
                        size: fontSizes.legend
                    }
                }
            };
        },
        
        // Специфичные оптимизации для точечных диаграмм
        _optimizeScatterLayout: function(typeConfig, features, fontSizes, width, height) {
            return {
                xaxis: {
                    showgrid: true,
                    gridcolor: 'rgba(0,0,0,0.1)',
                    zeroline: true,
                    zerolinecolor: 'rgba(0,0,0,0.2)',
                    tickfont: {
                        family: 'Inter, sans-serif',
                        size: fontSizes.axis
                    }
                },
                yaxis: {
                    showgrid: true,
                    gridcolor: 'rgba(0,0,0,0.1)',
                    zeroline: true,
                    zerolinecolor: 'rgba(0,0,0,0.2)',
                    tickfont: {
                        family: 'Inter, sans-serif',
                        size: fontSizes.axis
                    }
                },
                legend: {
                    bgcolor: 'rgba(255,255,255,0.7)',
                    bordercolor: 'rgba(0,0,0,0.1)',
                    borderwidth: 1,
                    font: {
                        family: 'Inter, sans-serif',
                        size: fontSizes.legend
                    }
                }
            };
        }
    };

    /**
     * Основной менеджер диаграмм
     * Обеспечивает управление жизненным циклом диаграмм и оптимизацию отображения
     */
    const unifiedChartManager = {
        // Инициализация менеджера
        init: function() {
            utils.log('Инициализация унифицированного менеджера диаграмм');
            
            // Устанавливаем обработчики для модальных окон
            this._setupModalHandlers();
            
            // Устанавливаем обработчик для сообщений от iframe
            utils.registerEventHandler(window, 'message', this._handleIframeMessage.bind(this));
            
            // Устанавливаем обработчик изменения размера окна
            utils.registerEventHandler(window, 'resize', utils.debounce(() => {
                this._handleWindowResize();
            }, config.timeouts.resizeDelay));
            
            // Настраиваем наблюдатель за изменениями в DOM для динамически добавляемых элементов
            this._setupMutationObserver();
            
            utils.log('Менеджер диаграмм успешно инициализирован');
            
            // Возвращаем this для цепочки вызовов
            return this;
        },
        
        // Обработка изменения размера окна
        _handleWindowResize: function() {
            utils.log('Обработка изменения размера окна');
            
            // Определяем активное модальное окно
            const fullscreenModal = utils.getElement(config.selectors.fullscreenModal);
            const standardModal = utils.getElement(config.selectors.standardModal);
            
            // Проверяем, открыто ли полноэкранное модальное окно
            if (fullscreenModal && fullscreenModal.classList.contains('show')) {
                utils.log('Обнаружено открытое полноэкранное модальное окно');
                
                const container = utils.getElement(config.selectors.fullscreenContainer);
                if (container) {
                    const iframe = utils.getElement(config.selectors.iframe, container);
                    if (iframe) {
                        this.optimizeChartInIframe(iframe);
                    }
                }
            }
            // Проверяем, открыто ли стандартное модальное окно
            else if (standardModal && standardModal.classList.contains('show')) {
                utils.log('Обнаружено открытое стандартное модальное окно');
                
                const container = utils.getElement(config.selectors.standardContainer);
                if (container) {
                    const iframe = utils.getElement(config.selectors.iframe, container);
                    if (iframe) {
                        this.optimizeChartInIframe(iframe);
                    }
                }
            } 
            // Если модальные окна закрыты, проверяем все диаграммы на странице
            else {
                this.optimizeAllChartsOnPage();
            }
        },
        
        // Оптимизация всех диаграмм на странице
        optimizeAllChartsOnPage: function() {
            utils.log('Оптимизация всех диаграмм на странице');
            
            // Находим все фреймы с диаграммами
            const iframes = document.querySelectorAll(config.selectors.iframe);
            
            if (iframes.length === 0) {
                utils.log('Диаграммы на странице не найдены');
                return;
            }
            
            // Оптимизируем каждый найденный iframe
            iframes.forEach(iframe => {
                // Проверяем, отображается ли iframe (не скрыт)
                const isVisible = iframe.offsetParent !== null;
                
                if (isVisible) {
                    this.optimizeChartInIframe(iframe);
                }
            });
        },
        
        // Основной метод оптимизации диаграммы в iframe
        optimizeChartInIframe: function(iframe) {
            if (!iframe) {
                utils.log('iframe не предоставлен', 'error');
                return Promise.reject(new Error('iframe не предоставлен'));
            }
            
            const iframeId = iframe.id || utils.generateUniqueId('iframe');
            if (!iframe.id) iframe.id = iframeId;
            
            utils.log(`Оптимизация диаграммы в iframe ${iframeId}`);
            
            // Получаем размеры контейнера iframe
            const container = iframe.parentElement;
            if (!container) {
                utils.log('Не найден родительский контейнер для iframe', 'warn');
                return Promise.reject(new Error('Отсутствует родительский контейнер'));
            }
            
            const contentSize = utils.getContentSize(container);
            const { width, height } = contentSize;
            
            // Проверяем, изменились ли размеры с последнего обновления
            const lastSize = state.chartSizes.get(iframeId);
            const sizeChanged = !lastSize || 
                Math.abs(lastSize.width - width) > 5 || 
                Math.abs(lastSize.height - height) > 5;
            
            if (!sizeChanged) {
                utils.log(`Пропуск обновления - размеры не изменились для ${iframeId}`);
                return Promise.resolve(false);
            }
            
            // Обновляем информацию о размерах
            state.chartSizes.set(iframeId, { width, height });
            
            // Проверяем, не выполняется ли уже рендеринг для этого iframe
            if (state.renderingState.get(iframeId)) {
                utils.log(`Пропуск обновления - рендеринг уже выполняется для ${iframeId}`);
                return Promise.resolve(false);
            }
            
            // Устанавливаем флаг выполнения рендеринга
            state.renderingState.set(iframeId, true);
            
            // Анализируем диаграмму, если необходимо
            return this._ensureChartAnalyzed(iframe)
                .then(analysis => {
                    if (!analysis) {
                        throw new Error('Не удалось проанализировать диаграмму');
                    }
                    
                    // Создаем оптимальный макет
                    const layout = chartOptimizer.createOptimalLayout(analysis, width, height);
                    
                    // Применяем оптимизированный макет
                    return this._applyLayoutToChart(iframe, layout);
                })
                .then(success => {
                    // Сбрасываем флаг рендеринга
                    state.renderingState.set(iframeId, false);
                    return success;
                })
                .catch(error => {
                    // Сбрасываем флаг рендеринга при ошибке
                    state.renderingState.set(iframeId, false);
                    utils.log(`Ошибка оптимизации диаграммы в ${iframeId}: ${error.message}`, 'error');
                    
                    // Запускаем запасной вариант через установленный механизм
                    this._tryFallbackOptimization(iframe);
                    
                    throw error;
                });
        },
        
        // Удостоверяемся, что диаграмма проанализирована
        _ensureChartAnalyzed: function(iframe) {
            const iframeId = iframe.id;
            
            // Проверяем, есть ли в кэше анализ диаграммы
            if (state.chartAnalysisCache.has(iframeId)) {
                return Promise.resolve(state.chartAnalysisCache.get(iframeId));
            }
            
            // Если нет, выполняем новый анализ
            return new Promise((resolve, reject) => {
                // Задержка для гарантии полной загрузки iframe
                setTimeout(() => {
                    try {
                        const analysis = chartAnalyzer.analyzeChart(iframe);
                        resolve(analysis);
                    } catch (e) {
                        reject(e);
                    }
                }, config.timeouts.analyzeDelay);
            });
        },
        
        // Применение макета к диаграмме
        _applyLayoutToChart: function(iframe, layout) {
            if (!iframe || !layout) {
                return Promise.reject(new Error('Не предоставлены iframe или макет'));
            }
            
            return new Promise((resolve, reject) => {
                try {
                    const contents = utils.getIframeContents(iframe);
                    if (!contents || !contents.window || !contents.document) {
                        throw new Error('Не удалось получить содержимое iframe');
                    }
                    
                    const plotlyDiv = contents.document.querySelector('.plotly-graph-div');
                    if (!plotlyDiv) {
                        throw new Error('Элемент plotly-graph-div не найден в iframe');
                    }
                    
                    if (!contents.window.Plotly) {
                        throw new Error('Объект Plotly не найден в iframe');
                    }
                    
                    // Применяем новый макет через API Plotly
                    contents.window.Plotly.relayout(plotlyDiv, layout)
                        .then(() => {
                            utils.log(`Макет успешно применен к диаграмме в ${iframe.id}`);
                            resolve(true);
                        })
                        .catch(err => {
                            utils.log(`Ошибка при применении макета: ${err.message}`, 'error');
                            reject(err);
                        });
                } catch (error) {
                    utils.log(`Ошибка при обращении к iframe: ${error.message}`, 'error');
                    reject(error);
                }
            });
        },
        
        // Запасной вариант оптимизации через существующие механизмы
        _tryFallbackOptimization: function(iframe) {
            utils.log(`Попытка запасной оптимизации для ${iframe.id}`);
            
            // Пробуем через старый механизм iframeChartHandler
            if (window.iframeChartHandler && typeof window.iframeChartHandler.resizeIframeChart === 'function') {
                utils.log('Используем iframeChartHandler.resizeIframeChart');
                try {
                    window.iframeChartHandler.resizeIframeChart(iframe.id);
                } catch (e) {
                    utils.log(`Ошибка при использовании iframeChartHandler: ${e.message}`, 'warn');
                }
            }
            
            // Пробуем через механизм resizeModalChart
            if (typeof window.resizeModalChart === 'function') {
                utils.log('Используем window.resizeModalChart');
                try {
                    // Определяем ID модального окна
                    let modalId = null;
                    if (iframe.closest(config.selectors.fullscreenContainer)) {
                        modalId = 'vizFullscreenModal';
                    } else if (iframe.closest(config.selectors.standardContainer)) {
                        modalId = 'vizModal';
                    }
                    
                    if (modalId) {
                        window.resizeModalChart(modalId);
                    }
                } catch (e) {
                    utils.log(`Ошибка при использовании resizeModalChart: ${e.message}`, 'warn');
                }
            }
            
            // Прямая отправка сообщения в iframe
            try {
                const contents = utils.getIframeContents(iframe);
                if (contents && contents.window) {
                    const container = iframe.parentElement;
                    if (container) {
                        const { width, height } = utils.getContentSize(container);
                        
                        contents.window.postMessage({
                            type: 'resize-plotly',
                            width: width,
                            height: height
                        }, '*');
                    }
                }
            } catch (e) {
                utils.log(`Ошибка при отправке сообщения в iframe: ${e.message}`, 'warn');
            }
        },
        
        // Настройка обработчиков модальных окон
        _setupModalHandlers: function() {
            // Обработка событий полноэкранного модального окна
            const fullscreenModal = utils.getElement(config.selectors.fullscreenModal);
            if (fullscreenModal) {
                utils.registerEventHandler(fullscreenModal, 'shown.bs.modal', () => {
                    utils.log('Событие показа полноэкранного модального окна');
                    setTimeout(() => {
                        const container = utils.getElement(config.selectors.fullscreenContainer);
                        if (container) {
                            const iframe = utils.getElement(config.selectors.iframe, container);
                            if (iframe) {
                                this.optimizeChartInIframe(iframe);
                            }
                        }
                    }, config.timeouts.resizeDelay);
                });
                
                utils.registerEventHandler(fullscreenModal, 'hide.bs.modal', () => {
                    utils.log('Событие скрытия полноэкранного модального окна');
                });
            }
            
            // Обработка событий стандартного модального окна
            const standardModal = utils.getElement(config.selectors.standardModal);
            if (standardModal) {
                utils.registerEventHandler(standardModal, 'shown.bs.modal', () => {
                    utils.log('Событие показа стандартного модального окна');
                    setTimeout(() => {
                        const container = utils.getElement(config.selectors.standardContainer);
                        if (container) {
                            const iframe = utils.getElement(config.selectors.iframe, container);
                            if (iframe) {
                                this.optimizeChartInIframe(iframe);
                            }
                        }
                    }, config.timeouts.resizeDelay);
                });
            }
            
            // Обработка кнопки перехода в полноэкранный режим
            const enhanceFullscreenButton = () => {
                const fullscreenBtn = document.getElementById('fullscreen-btn');
                if (!fullscreenBtn || fullscreenBtn.getAttribute('data-enhanced')) return;
                
                fullscreenBtn.setAttribute('data-enhanced', 'true');
                
                // Используем шаблон декоратора для сохранения оригинальной функциональности
                const originalOnClick = fullscreenBtn.onclick;
                
                fullscreenBtn.onclick = (event) => {
                    // Вызываем оригинальный обработчик, если он был
                    if (typeof originalOnClick === 'function') {
                        originalOnClick.call(fullscreenBtn, event);
                    }
                    
                    // Добавляем нашу логику
                    utils.log('Клик по кнопке перехода в полноэкранный режим');
                    
                    // После открытия полноэкранного модального окна дополнительно оптимизируем
                    setTimeout(() => {
                        const container = utils.getElement(config.selectors.fullscreenContainer);
                        if (container) {
                            const iframe = utils.getElement(config.selectors.iframe, container);
                            if (iframe) {
                                this.optimizeChartInIframe(iframe);
                                
                                // Запускаем несколько попыток оптимизации с возрастающими задержками
                                // для гарантии оптимального отображения после всех CSS-анимаций
                                [300, 600, 1000].forEach(delay => {
                                    setTimeout(() => {
                                        this.optimizeChartInIframe(iframe);
                                    }, delay);
                                });
                            }
                        }
                    }, config.timeouts.resizeDelay);
                };
            };
            
            // Применяем сразу и с задержкой для динамически добавленных кнопок
            enhanceFullscreenButton();
            setTimeout(enhanceFullscreenButton, 1000);
        },
        
        // Обработка сообщений от iframe
        _handleIframeMessage: function(event) {
            try {
                if (!event.data || typeof event.data !== 'object') return;
                
                const data = event.data;
                
                // Обрабатываем уведомление о готовности Plotly
                if (data.type === 'plotly-ready' || data.type === 'plotly-modal-ready') {
                    utils.log(`Получено сообщение о готовности Plotly: ${data.type}`);
                    
                    // Находим соответствующий iframe
                    let iframe = null;
                    document.querySelectorAll(config.selectors.iframe).forEach(element => {
                        if (element.contentWindow === event.source) {
                            iframe = element;
                        }
                    });
                    
                    if (iframe) {
                        // Запускаем оптимизацию с небольшой задержкой для гарантии полной загрузки
                        setTimeout(() => {
                            this.optimizeChartInIframe(iframe);
                        }, config.timeouts.analyzeDelay);
                    }
                }
                
                // Обрабатываем завершение изменения размера
                if (data.type === 'plotly-resize-complete') {
                    utils.log(`Получено подтверждение изменения размера: ${data.plotlyDiv}`);
                    
                    // Здесь можно добавить логику для обработки завершения ресайза
                }
            } catch (e) {
                utils.log(`Ошибка при обработке сообщения от iframe: ${e.message}`, 'error');
            }
        },
        
        // Настройка наблюдателя за изменениями в DOM
        _setupMutationObserver: function() {
            try {
                const observer = new MutationObserver(mutations => {
                    let needsOptimization = false;
                    
                    mutations.forEach(mutation => {
                        if (mutation.type === 'childList') {
                            // Проверяем добавление iframe
                            mutation.addedNodes.forEach(node => {
                                if (node.tagName === 'IFRAME' || (node.nodeType === 1 && node.querySelector('iframe'))) {
                                    needsOptimization = true;
                                }
                            });
                            
                            // Проверяем добавление контейнеров с iframe
                            if (mutation.target && (
                                mutation.target.id === 'viz-container' || 
                                mutation.target.id === 'fullscreen-viz-container'
                            )) {
                                needsOptimization = true;
                            }
                        }
                    });
                    
                    if (needsOptimization) {
                        utils.log('Обнаружены изменения в DOM, требующие оптимизации диаграмм');
                        // Небольшая задержка для завершения всех DOM-операций
                        setTimeout(() => {
                            this.optimizeAllChartsOnPage();
                        }, config.timeouts.analyzeDelay);
                    }
                });
                
                // Наблюдаем за изменениями в важных контейнерах
                const containers = [
                    document.body,
                    utils.getElement(config.selectors.standardContainer),
                    utils.getElement(config.selectors.fullscreenContainer)
                ].filter(Boolean); // Отфильтровываем несуществующие элементы
                
                containers.forEach(container => {
                    observer.observe(container, { 
                        childList: true, 
                        subtree: true 
                    });
                });
                
                // Сохраняем для последующей очистки
                state.cleanupRegistry.observers.push(observer);
                
                return observer;
            } catch (e) {
                utils.log(`Ошибка при настройке MutationObserver: ${e.message}`, 'error');
                return null;
            }
        },
        
        // Очистка ресурсов, выделенных менеджером диаграмм
        cleanup: function() {
            utils.log('Очистка ресурсов менеджера диаграмм');
            
            // Отмена всех обработчиков событий
            utils.cleanupEventHandlers();
            
            // Остановка всех наблюдателей
            state.cleanupRegistry.observers.forEach(observer => {
                try {
                    observer.disconnect();
                } catch (e) {
                    utils.log(`Ошибка при остановке наблюдателя: ${e.message}`, 'warn');
                }
            });
            
            // Очистка кэша
            state.chartAnalysisCache.clear();
            state.chartSizes.clear();
            state.renderingState.clear();
            state.cleanupRegistry.observers = [];
            
            utils.log('Очистка ресурсов завершена');
        }
    };
    
    // ========================
    // Инициализация и экспорт
    // ========================
    
    // Автоматическая инициализация
    function initialize() {
        try {
            // Расширяем существующие объекты с помощью шаблона декоратора
            
            // 1. Если существует iframeChartHandler, дополняем его функциональность
            if (window.iframeChartHandler) {
                utils.log('Расширение существующего iframeChartHandler');
                
                const originalResizeIframeChart = window.iframeChartHandler.resizeIframeChart;
                
                // Подключаем наш оптимизированный метод
                window.iframeChartHandler.resizeIframeChart = function(iframeId, chartType) {
                    // Попытка использовать унифицированный менеджер
                    const iframe = document.getElementById(iframeId);
                    if (iframe) {
                        unifiedChartManager.optimizeChartInIframe(iframe)
                            .catch(() => {
                                // В случае ошибки используем оригинальный метод
                                if (originalResizeIframeChart) {
                                    originalResizeIframeChart.call(this, iframeId, chartType);
                                }
                            });
                    } else if (originalResizeIframeChart) {
                        // Если iframe не найден, вызываем оригинальный метод
                        originalResizeIframeChart.call(this, iframeId, chartType);
                    }
                };
            }
            
            // 2. Если существует resizeModalChart, дополняем его функциональность
            if (typeof window.resizeModalChart === 'function') {
                utils.log('Расширение существующего resizeModalChart');
                
                const originalResizeModalChart = window.resizeModalChart;
                
                window.resizeModalChart = function(modalId) {
                    // Пытаемся найти iframe в модальном окне
                    const modal = document.getElementById(modalId);
                    if (modal) {
                        const container = modal.querySelector('#fullscreen-viz-container') || 
                                          modal.querySelector('#viz-container');
                        if (container) {
                            const iframe = container.querySelector('iframe');
                            if (iframe) {
                                // Используем унифицированный менеджер для оптимизации
                                unifiedChartManager.optimizeChartInIframe(iframe)
                                    .catch(() => {
                                        // В случае ошибки используем оригинальный метод
                                        originalResizeModalChart.call(window, modalId);
                                    });
                                return;
                            }
                        }
                    }
                    
                    // Если не нашли iframe, используем оригинальный метод
                    originalResizeModalChart.call(window, modalId);
                };
            }
            
            // Инициализируем унифицированный менеджер диаграмм
            unifiedChartManager.init();
            
            // Если есть plotlyFullscreenAdapter, интегрируемся с ним
            if (window.plotlyFullscreenAdapter) {
                utils.log('Расширение plotlyFullscreenAdapter');
                
                const originalOptimizeChart = window.plotlyFullscreenAdapter.optimizeChart;
                
                window.plotlyFullscreenAdapter.optimizeChart = function(iframe) {
                    return unifiedChartManager.optimizeChartInIframe(iframe)
                        .catch(() => {
                            // В случае ошибки используем оригинальный метод
                            if (originalOptimizeChart) {
                                return originalOptimizeChart.call(window.plotlyFullscreenAdapter, iframe);
                            }
                            return Promise.reject(new Error('Не удалось оптимизировать диаграмму'));
                        });
                };
            }
            
        } catch (e) {
            utils.log(`Ошибка при инициализации: ${e.message}`, 'error');
        }
    }
    
    // Экспорт публичного API
    window.unifiedChartManager = {
        // Инициализация менеджера
        init: function() {
            return unifiedChartManager.init();
        },
        
        // Оптимизация конкретной диаграммы
        optimizeChart: function(iframeOrSelector) {
            let iframe;
            
            if (typeof iframeOrSelector === 'string') {
                iframe = document.querySelector(iframeOrSelector);
            } else {
                iframe = iframeOrSelector;
            }
            
            if (!iframe) {
                return Promise.reject(new Error('iframe не найден'));
            }
            
            return unifiedChartManager.optimizeChartInIframe(iframe);
        },
        
        // Оптимизация всех диаграмм
        optimizeAllCharts: function() {
            return unifiedChartManager.optimizeAllChartsOnPage();
        },
        
        // Управление отладкой
        setDebug: function(enabled) {
            config.debug = !!enabled;
            return this;
        },
        
        // Очистка ресурсов
        cleanup: function() {
            unifiedChartManager.cleanup();
            return this;
        },
        
        // Получение информации о диаграмме
        getChartInfo: function(iframeOrSelector) {
            let iframe;
            
            if (typeof iframeOrSelector === 'string') {
                iframe = document.querySelector(iframeOrSelector);
            } else {
                iframe = iframeOrSelector;
            }
            
            if (!iframe || !iframe.id) return null;
            
            return state.chartAnalysisCache.get(iframe.id);
        }
    };
    
    // Инициализируем при загрузке страницы
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        // DOM уже загружен
        initialize();
    }
})();