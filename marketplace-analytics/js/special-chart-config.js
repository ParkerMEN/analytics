/**
 * Special Chart Configuration
 * 
 * Содержит специальные конфигурации для отдельных диаграмм, требующих 
 * индивидуального подхода к отображению и форматированию
 * 
 * @version 1.0.0
 */

(function() {
    'use strict';
    
    // Общие настройки форматирования
    const formatConfig = {
        fontFamily: 'Inter, sans-serif',
        colors: {
            primary: '#4361ee',
            secondary: '#3f37c9',
            accent: '#4cc9f0',
            grid: 'rgba(0,0,0,0.07)',
            zeroLine: 'rgba(0,0,0,0.2)'
        }
    };
    
    // Специальные настройки для конкретных диаграмм
    const specialCharts = {
        // Специальная конфигурация для диаграммы "Взаимосвязь рекомендаций и рейтинга"
        'vzaimosvyaz-rekomendatsiy': {
            type: 'scatter-correlation',
            getLayout: function(width, height) {
                // Рассчитываем оптимальные размеры шрифтов
                const titleSize = Math.max(16, Math.min(22, width / 35));
                const axisLabelSize = Math.max(13, Math.min(16, width / 60));
                const tickLabelSize = Math.max(11, Math.min(14, width / 70));
                const legendSize = Math.max(11, Math.min(14, width / 70));
                
                // Определяем оптимальное расположение легенды
                const isWide = width > height * 1.2;
                
                // Рассчитываем оптимальные отступы
                const margins = {
                    l: Math.max(60, width * 0.08),  // Увеличиваем отступ для оси Y
                    r: isWide ? Math.max(100, width * 0.15) : Math.max(40, width * 0.08),
                    t: Math.max(70, height * 0.12),
                    b: Math.max(60, height * 0.1),
                    pad: 10
                };
                
                return {
                    width: width,
                    height: height,
                    autosize: true,
                    
                    // Усовершенствованные настройки полей
                    margin: margins,
                    
                    // Улучшенные настройки для осей
                    xaxis: {
                        title: {
                            text: 'Рекомендации пользователей',
                            font: {
                                family: formatConfig.fontFamily,
                                size: axisLabelSize,
                                color: '#333'
                            },
                            standoff: 15
                        },
                        showgrid: true,
                        gridcolor: formatConfig.colors.grid,
                        gridwidth: 1,
                        zeroline: true,
                        zerolinecolor: formatConfig.colors.zeroLine,
                        zerolinewidth: 1.5,
                        tickfont: {
                            family: formatConfig.fontFamily,
                            size: tickLabelSize
                        },
                        showline: true,
                        linecolor: '#ccc',
                        linewidth: 1
                    },
                    
                    yaxis: {
                        title: {
                            text: 'Рейтинг',
                            font: {
                                family: formatConfig.fontFamily,
                                size: axisLabelSize,
                                color: '#333'
                            },
                            standoff: 15
                        },
                        showgrid: true,
                        gridcolor: formatConfig.colors.grid,
                        gridwidth: 1,
                        zeroline: true,
                        zerolinecolor: formatConfig.colors.zeroLine,
                        zerolinewidth: 1.5,
                        tickfont: {
                            family: formatConfig.fontFamily,
                            size: tickLabelSize
                        },
                        showline: true,
                        linecolor: '#ccc',
                        linewidth: 1
                    },
                    
                    // Оптимизированные настройки легенды
                    legend: {
                        x: isWide ? 1.02 : 0.5,
                        y: isWide ? 0.5 : -0.15,
                        xanchor: isWide ? 'left' : 'center',
                        yanchor: isWide ? 'middle' : 'top',
                        orientation: isWide ? 'v' : 'h',
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: 'rgba(0,0,0,0.1)',
                        borderwidth: 1,
                        font: {
                            family: formatConfig.fontFamily,
                            size: legendSize
                        }
                    },
                    
                    // Улучшенный заголовок
                    title: {
                        text: 'Взаимосвязь рекомендаций пользователей и рейтинга',
                        font: {
                            family: formatConfig.fontFamily,
                            size: titleSize,
                            color: '#333'
                        },
                        x: 0.5,
                        xanchor: 'center',
                        yanchor: 'top',
                        pad: {b: 20}
                    },
                    
                    // Улучшенное отображение подсказок
                    hovermode: 'closest',
                    hoverlabel: {
                        bgcolor: 'rgba(255,255,255,0.95)',
                        bordercolor: '#333',
                        font: {
                            family: formatConfig.fontFamily,
                            size: 12
                        },
                        namelength: -1
                    }
                };
            },
            
            // Специальные настройки для обновления трейсов (точек на диаграмме)
            updateTraces: function(plotlyDiv, width, height) {
                if (!plotlyDiv || !plotlyDiv._fullData) return null;
                
                // Рассчитываем оптимальный размер маркеров в зависимости от размеров экрана
                const baseMarkerSize = Math.max(8, Math.min(16, width / 80));
                
                // Настройки для каждого трейса
                const tracesUpdates = [];
                
                plotlyDiv._fullData.forEach((trace, i) => {
                    if (trace.type === 'scatter') {
                        // Базовые настройки для всех трейсов
                        const update = {
                            marker: {
                                size: baseMarkerSize,
                                opacity: 0.7,
                                line: {
                                    width: 1,
                                    color: 'rgba(255,255,255,0.8)'
                                }
                            }
                        };
                        
                        // Для первого трейса (обычно "Да" - рекомендованные)
                        if (i === 0) {
                            update.marker.color = formatConfig.colors.primary;
                            update.marker.size = baseMarkerSize + 1;
                        } 
                        // Для второго трейса (обычно "Нет" - не рекомендованные)
                        else if (i === 1) {
                            update.marker.color = '#f72585';
                            update.marker.opacity = 0.6;
                        }
                        
                        tracesUpdates.push(update);
                    }
                });
                
                return tracesUpdates;
            }
        },
        
        // Здесь можно добавить другие специальные настройки для других диаграмм
        'vzaimosvyaz-komplektatsii': {
            type: 'scatter-correlation',
            // Аналогичные настройки для другой корреляционной диаграммы
            getLayout: function(width, height) {
                // По аналогии с предыдущей диаграммой
                // ...
                return {/* ... */};
            },
            updateTraces: function(plotlyDiv, width, height) {
                // По аналогии с предыдущей диаграммой
                // ...
                return [];
            }
        },
        
        'vzaimosvyaz-legkosti-sborki': {
            type: 'scatter-correlation',
            // Аналогичные настройки для третьей корреляционной диаграммы
            getLayout: function(width, height) {
                // ...
                return {/* ... */};
            },
            updateTraces: function(plotlyDiv, width, height) {
                // ...
                return [];
            }
        }
    };
    
    // Экспорт API
    window.specialChartConfig = {
        // Проверка существования специальной конфигурации
        hasSpecialConfig: function(vizId) {
            return !!specialCharts[vizId];
        },
        
        // Получение специальной конфигурации
        getSpecialConfig: function(vizId) {
            return specialCharts[vizId] || null;
        },
        
        // Получение типа диаграммы из специальной конфигурации
        getSpecialChartType: function(vizId) {
            return specialCharts[vizId] ? specialCharts[vizId].type : null;
        },
        
        // Получение оптимального layout для диаграммы
        getOptimalLayout: function(vizId, width, height) {
            if (specialCharts[vizId] && typeof specialCharts[vizId].getLayout === 'function') {
                return specialCharts[vizId].getLayout(width, height);
            }
            return null;
        },
        
        // Получение обновлений для трейсов
        getTracesUpdates: function(vizId, plotlyDiv, width, height) {
            if (specialCharts[vizId] && typeof specialCharts[vizId].updateTraces === 'function') {
                return specialCharts[vizId].updateTraces(plotlyDiv, width, height);
            }
            return null;
        }
    };
    
    console.log('Специальные конфигурации для диаграмм загружены');
})();