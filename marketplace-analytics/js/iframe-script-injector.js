/**
 * iframe-script-injector.js
 * 
 * Модуль для инжектирования скриптов адаптации графиков Plotly в iframe
 * Обеспечивает корректное изменение размеров и форматирование для разных типов диаграмм
 * 
 * @version 1.0.0
 */

(function() {
    'use strict';
    
    // Утилиты
    const utils = {
        log: function(message, level = 'info') {
            const prefix = '[IframeScriptInjector]';
            
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
        }
    };

    /**
     * Улучшенный скрипт для инъекции в iframe
     * Обеспечивает адаптивное изменение размеров графиков Plotly с учетом типа диаграмм
     */
    function injectEnhancedIframeScript() {
        const scriptText = `
        (function() {
            console.log('[PlotlyResize] Инициализация адаптера изменения размеров Plotly графика');
            
            // Предотвращаем повторную инициализацию
            if (window._plotlyResizeAdapterInitialized) return;
            window._plotlyResizeAdapterInitialized = true;
            
            // Определяем тип диаграммы для специфических настроек
            function detectChartType() {
                const plotlyDivs = document.querySelectorAll('.plotly-graph-div');
                if (plotlyDivs.length === 0) return 'unknown';
                
                // Попытка определения типа диаграммы по данным
                try {
                    const plotlyDiv = plotlyDivs[0];
                    if (plotlyDiv._fullData) {
                        // Проверяем первый trace для определения типа
                        const firstTrace = plotlyDiv._fullData[0];
                        if (firstTrace.type === 'pie' || firstTrace.type === 'donut') {
                            return 'pie';
                        } else if (firstTrace.type === 'bar') {
                            return 'bar';
                        } else if (firstTrace.type === 'scatter' && firstTrace.mode && firstTrace.mode.includes('lines')) {
                            return 'line';
                        } else if (firstTrace.type === 'scatter') {
                            return 'scatter';
                        }
                    }
                    
                    // Если не удалось определить по данным, пробуем по DOM
                    if (plotlyDiv.querySelector('.pielayer')) {
                        return 'pie';
                    } else if (plotlyDiv.querySelector('.barlayer')) {
                        return 'bar';
                    } else if (plotlyDiv.querySelector('.scatterlayer')) {
                        // Может быть как линейный график, так и точечный
                        return 'scatter';
                    }
                } catch (e) {
                    console.warn('[PlotlyResize] Ошибка при определении типа диаграммы:', e);
                }
                
                return 'unknown';
            }
            
            // Получаем оптимальные настройки для типа диаграммы
            function getOptimalLayoutSettings(chartType, containerWidth, containerHeight) {
                // Базовые настройки для всех типов диаграмм
                const baseSettings = {
                    autosize: true,
                    width: containerWidth,
                    height: containerHeight,
                };
                
                // Специальные настройки зависят от типа диаграммы
                switch (chartType) {
                    case 'pie':
                        // Для круговых диаграмм нужно больше места для легенды
                        return Object.assign({}, baseSettings, {
                            margin: {
                                l: Math.max(30, containerWidth * 0.05),
                                r: Math.max(30, containerWidth * 0.25), // Больше места для легенды справа
                                t: Math.max(30, containerHeight * 0.1),
                                b: Math.max(30, containerHeight * 0.1),
                                pad: 5
                            },
                            legend: {
                                // Улучшенные настройки легенды для круговых диаграмм
                                orientation: containerWidth > containerHeight ? 'v' : 'h',
                                x: containerWidth > containerHeight ? 1.05 : 0.5,
                                y: containerWidth > containerHeight ? 0.5 : -0.2,
                                xanchor: containerWidth > containerHeight ? 'left' : 'center',
                                font: {
                                    size: Math.max(10, Math.min(14, containerWidth / 50))
                                },
                                itemwidth: containerWidth * 0.15
                            },
                            annotations: [{
                                // Центральная метка для суммы или основной информации
                                font: {
                                    size: Math.max(14, containerWidth / 30)
                                },
                                showarrow: false
                            }]
                        });
                    
                    case 'bar':
                        // Для столбчатых диаграмм обеспечиваем пространство для подписей осей
                        return Object.assign({}, baseSettings, {
                            margin: {
                                l: Math.max(50, containerWidth * 0.1), // Для метки оси Y
                                r: Math.max(20, containerWidth * 0.05),
                                t: Math.max(40, containerHeight * 0.15), // Для заголовка
                                b: Math.max(60, containerHeight * 0.2), // Для меток оси X
                                pad: 5
                            },
                            xaxis: {
                                tickangle: containerWidth < 500 ? -45 : 0,
                                tickfont: {
                                    size: Math.max(10, Math.min(12, containerWidth / 60))
                                }
                            },
                            yaxis: {
                                tickfont: {
                                    size: Math.max(10, Math.min(12, containerWidth / 60))
                                }
                            },
                            title: {
                                font: {
                                    size: Math.max(14, containerWidth / 40)
                                }
                            }
                        });
                    
                    case 'line':
                    case 'scatter':
                        // Для линейных и точечных графиков
                        return Object.assign({}, baseSettings, {
                            margin: {
                                l: Math.max(45, containerWidth * 0.08), // Для метки оси Y
                                r: Math.max(20, containerWidth * 0.05),
                                t: Math.max(40, containerHeight * 0.12), // Для заголовка
                                b: Math.max(50, containerHeight * 0.15), // Для меток оси X
                                pad: 5
                            },
                            xaxis: {
                                tickangle: containerWidth < 500 ? -45 : 0,
                                tickfont: {
                                    size: Math.max(10, Math.min(12, containerWidth / 60))
                                }
                            },
                            yaxis: {
                                tickfont: {
                                    size: Math.max(10, Math.min(12, containerWidth / 60))
                                }
                            },
                            title: {
                                font: {
                                    size: Math.max(14, containerWidth / 40)
                                }
                            },
                            legend: {
                                font: {
                                    size: Math.max(10, Math.min(12, containerWidth / 60))
                                }
                            }
                        });
                    
                    default:
                        // Универсальные настройки для неизвестного типа
                        return Object.assign({}, baseSettings, {
                            margin: {
                                l: Math.max(40, containerWidth * 0.08),
                                r: Math.max(30, containerWidth * 0.08),
                                t: Math.max(40, containerHeight * 0.12),
                                b: Math.max(40, containerHeight * 0.12),
                                pad: 5
                            },
                            font: {
                                size: Math.max(10, Math.min(14, containerWidth / 50))
                            }
                        });
                }
            }
            
            // Обновленная функция уведомления родительского окна
            function notifyParentWhenPlotlyReady() {
                // Проверяем доступность Plotly
                if (typeof window.Plotly !== 'undefined' || document.querySelector('.plotly-graph-div')) {
                    const plotlyElements = document.querySelectorAll('.plotly-graph-div');
                    if (plotlyElements.length > 0) {
                        const plotlyDiv = plotlyElements[0].id;
                        const chartType = detectChartType();
                        
                        // Проверяем, является ли окно частью модального окна
                        const isModal = window.location.href.includes('modal=true') || 
                                      window.parent.document.getElementById('viz-container') !== null ||
                                      window.parent.document.getElementById('fullscreen-viz-container') !== null;
                        
                        window.parent.postMessage({
                            type: isModal ? 'plotly-modal-ready' : 'plotly-ready',
                            plotlyDiv: plotlyDiv,
                            chartType: chartType,
                            dimensions: {
                                width: plotlyElements[0].clientWidth,
                                height: plotlyElements[0].clientHeight
                            }
                        }, '*');
                        
                        console.log('[PlotlyResize] Уведомление о готовности отправлено (' + 
                            (isModal ? 'модальное' : 'стандартное') + ', тип диаграммы: ' + chartType + ')');
                        
                        // Серия повторных отправок с увеличивающимися интервалами
                        [300, 600, 1000, 1500].forEach(delay => {
                            setTimeout(() => {
                                window.parent.postMessage({
                                    type: isModal ? 'plotly-modal-ready' : 'plotly-ready',
                                    plotlyDiv: plotlyDiv,
                                    chartType: chartType,
                                    dimensions: {
                                        width: plotlyElements[0].clientWidth,
                                        height: plotlyElements[0].clientHeight
                                    }
                                }, '*');
                                console.log('[PlotlyResize] Повторное уведомление, задержка: ' + delay + 'мс');
                            }, delay);
                        });
                    } else {
                        console.log('[PlotlyResize] Plotly элементы не найдены, повторная попытка через 200мс');
                        setTimeout(notifyParentWhenPlotlyReady, 200);
                    }
                } else {
                    console.log('[PlotlyResize] Plotly не инициализирован, повторная попытка через 200мс');
                    setTimeout(notifyParentWhenPlotlyReady, 200);
                }
            }
            
            // Улучшенная обработка сообщений от родительского окна
            function handleParentMessages(event) {
                try {
                    const data = event.data;
                    
                    // Обработка запроса на изменение размера
                    if (data && data.type === 'resize-plotly') {
                        console.log('[PlotlyResize] Получен запрос на изменение размера: ' + 
                            data.width + 'x' + data.height);
                        
                        // Находим элемент графика
                        const plotlyDiv = data.plotlyDiv 
                            ? document.getElementById(data.plotlyDiv)
                            : document.querySelector('.plotly-graph-div');
                        
                        if (plotlyDiv && window.Plotly) {
                            console.log('[PlotlyResize] Применяем новые размеры к #' + plotlyDiv.id);
                            
                            // Определяем тип диаграммы для оптимальных настроек
                            const chartType = data.chartType || detectChartType();
                            
                            // Получаем оптимальные настройки для данного типа диаграммы и размера
                            const layoutSettings = getOptimalLayoutSettings(
                                chartType, 
                                data.width, 
                                data.height
                            );
                            
                            console.log('[PlotlyResize] Используем настройки для типа: ' + chartType, layoutSettings);
                            
                            // Применяем новые размеры с оптимизированными настройками
                            window.Plotly.relayout(plotlyDiv, layoutSettings)
                                .then(() => {
                                    console.log('[PlotlyResize] Размер успешно изменен');
                                    
                                    // Дополнительные оптимизации для круговых диаграмм
                                    if (chartType === 'pie') {
                                        // Задержка для полного перерасчета диаграммы
                                        setTimeout(() => {
                                            // Может потребоваться дополнительная корректировка для отступов легенды
                                            window.Plotly.relayout(plotlyDiv, {
                                                'legend.font.size': Math.max(10, Math.min(14, layoutSettings.width / 50)),
                                                'legend.itemwidth': Math.floor(layoutSettings.width * 0.15),
                                                'textposition': 'inside'
                                            });
                                        }, 50);
                                    }
                                    
                                    // Отправляем подтверждение
                                    window.parent.postMessage({
                                        type: 'plotly-resize-complete',
                                        plotlyDiv: plotlyDiv.id,
                                        success: true
                                    }, '*');
                                })
                                .catch(err => {
                                    console.error('[PlotlyResize] Ошибка при изменении размера:', err);
                                });
                        } else {
                            console.error('[PlotlyResize] Не найден элемент графика или Plotly не инициализирован');
                        }
                    }
                } catch (e) {
                    console.error('[PlotlyResize] Ошибка при обработке сообщения:', e);
                }
            }
            
            // Регистрируем обработчик сообщений
            window.addEventListener('message', handleParentMessages);
            
            // Запускаем проверку наличия Plotly
            notifyParentWhenPlotlyReady();
            
            // Добавляем обработчики событий
            window.addEventListener('resize', function() {
                console.log('[PlotlyResize] Событие resize в iframe');
                notifyParentWhenPlotlyReady();
            });
            
            window.addEventListener('load', function() {
                console.log('[PlotlyResize] Событие load в iframe');
                setTimeout(notifyParentWhenPlotlyReady, 200);
            });
            
            // MutationObserver для отслеживания изменений в DOM
            const observer = new MutationObserver(function(mutations) {
                for (const mutation of mutations) {
                    if (mutation.type === 'childList' && 
                        mutation.addedNodes.length > 0 && 
                        document.querySelector('.plotly-graph-div')) {
                        console.log('[PlotlyResize] Обнаружены изменения в DOM с элементами Plotly');
                        setTimeout(notifyParentWhenPlotlyReady, 100);
                        break;
                    }
                }
            });
            
            // Запускаем наблюдение за изменениями в DOM
            observer.observe(document.body, { childList: true, subtree: true });
        })();
        `;
        
        const scriptElement = document.createElement('script');
        scriptElement.id = 'enhanced-plotly-resizer';
        scriptElement.textContent = scriptText;
        document.head.appendChild(scriptElement);
    }

    // Экспортируем функцию в глобальную область видимости
    window.iframeScriptInjector = {
        injectEnhancedIframeScript: injectEnhancedIframeScript
    };
    
    utils.log('Модуль инжекции скриптов для iframe инициализирован');
})();