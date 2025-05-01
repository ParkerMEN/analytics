/**
 * Генератор миниатюр для визуализаций Plotly
 * 
 * Создаёт упрощенные версии визуализаций для предпросмотра
 * в карточках на главной странице
 */
(function() {
    'use strict';

    // Конфигурация
    const config = {
        // Селекторы для поиска элементов
        selectors: {
            visualizationCard: '.visualization-card',
            visualizationContent: '.visualization-content',
            iframe: '.visualization-iframe',
            thumbnail: '.viz-thumbnail',
            thumbnailCanvas: '.viz-thumbnail-canvas'
        },
        // Размеры миниатюр
        thumbnail: {
            width: 320,
            height: 240
        },
        // Максимальное время ожидания загрузки исходного графика
        maxWaitTime: 5000
    };

    // Реестр графиков, для которых нужно создать миниатюры
    const pendingThumbnails = new Map();

    // Флаг, показывающий готовность DOM
    let isDOMReady = false;

    /**
     * Создаёт миниатюру для визуализации
     * @param {string} vizId - ID визуализации
     * @param {string} vizPath - путь к файлу визуализации
     * @param {HTMLElement} container - контейнер для миниатюры
     */
    function createThumbnail(vizId, vizPath, container) {
        // Регистрируем визуализацию для обработки
        pendingThumbnails.set(vizId, {
            path: vizPath,
            container: container,
            processed: false
        });

        // Создаем холст для миниатюры
        const canvas = document.createElement('canvas');
        canvas.className = config.selectors.thumbnailCanvas.substring(1);
        canvas.width = config.thumbnail.width;
        canvas.height = config.thumbnail.height;
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.objectFit = 'contain';
        canvas.dataset.vizId = vizId;

        // Добавляем холст в контейнер
        container.innerHTML = '';
        container.appendChild(canvas);

        // Запускаем процесс рендеринга миниатюры
        renderThumbnail(vizId, vizPath, canvas);
    }

    /**
     * Рендерит миниатюру графика
     * @param {string} vizId - ID визуализации
     * @param {string} vizPath - путь к файлу визуализации
     * @param {HTMLCanvasElement} canvas - холст для миниатюры
     */
    function renderThumbnail(vizId, vizPath, canvas) {
        // Создаем невидимый iframe для загрузки визуализации
        const tempIframe = document.createElement('iframe');
        tempIframe.style.position = 'absolute';
        tempIframe.style.left = '-9999px';
        tempIframe.style.width = config.thumbnail.width + 'px';
        tempIframe.style.height = config.thumbnail.height + 'px';
        tempIframe.style.opacity = '0';
        tempIframe.style.visibility = 'hidden';
        tempIframe.src = '../analytics_output/visualizations/' + vizPath;
        
        document.body.appendChild(tempIframe);
        
        // Устанавливаем таймер для предотвращения зависания
        const timeout = setTimeout(() => {
            cleanupThumbnailProcess(tempIframe, vizId);
            renderFallbackThumbnail(canvas, vizId);
        }, config.maxWaitTime);

        // Слушаем загрузку iframe
        tempIframe.onload = function() {
            try {
                // Пытаемся получить доступ к содержимому iframe
                const iframeDoc = tempIframe.contentDocument || tempIframe.contentWindow.document;
                const plotlyElement = iframeDoc.querySelector('.plotly-graph-div');
                
                if (plotlyElement) {
                    // Кастомное сообщение для извлечения данных графика
                    const extractDataScript = `
                        try {
                            const plotDiv = document.querySelector('.plotly-graph-div');
                            if (plotDiv && window.Plotly) {
                                // Упрощаем данные для миниатюры
                                const data = Plotly.getData(plotDiv);
                                const layout = Plotly.Plots.getSubplotIds(plotDiv, 'cartesian').length ? 
                                    Plotly.getLayout(plotDiv) : null;
                                
                                // Убираем сложные и ненужные для миниатюры элементы
                                const simplifiedData = data.map(trace => {
                                    // Сохраняем только базовые свойства
                                    const simplifiedTrace = {
                                        type: trace.type,
                                        x: trace.x?.slice(0, 10),
                                        y: trace.y?.slice(0, 10)
                                    };
                                    
                                    if (trace.marker) simplifiedTrace.marker = {color: trace.marker.color};
                                    if (trace.mode) simplifiedTrace.mode = trace.mode;
                                    
                                    return simplifiedTrace;
                                });
                                
                                // Упрощаем макет
                                const simplifiedLayout = layout ? {
                                    title: layout.title?.text || '',
                                    showlegend: false,
                                    margin: {t:30, r:10, l:10, b:10},
                                    xaxis: {showticklabels: false},
                                    yaxis: {showticklabels: false},
                                    width: ${config.thumbnail.width},
                                    height: ${config.thumbnail.height},
                                    font: {size: 8}
                                } : {};
                                
                                return {
                                    data: simplifiedData,
                                    layout: simplifiedLayout,
                                    success: true
                                };
                            }
                        } catch(e) {
                            console.error('Ошибка при извлечении данных графика:', e);
                        }
                        return {success: false};
                    `;

                    tempIframe.contentWindow.eval(`
                        const thumbnailData = (${extractDataScript})();
                        window.parent.postMessage({
                            type: 'thumbnail-data',
                            vizId: '${vizId}',
                            data: thumbnailData
                        }, '*');
                    `);
                } else {
                    renderFallbackThumbnail(canvas, vizId);
                }
            } catch (e) {
                console.error('Ошибка при обработке iframe для миниатюры:', e);
                renderFallbackThumbnail(canvas, vizId);
            } finally {
                clearTimeout(timeout);
                cleanupThumbnailProcess(tempIframe, vizId);
            }
        };
    }

    /**
     * Создаёт миниатюру из полученных данных
     * @param {string} vizId - ID визуализации
     * @param {Object} plotlyData - данные для построения графика
     * @param {HTMLCanvasElement} canvas - холст для миниатюры
     */
    function createPlotlyThumbnail(vizId, plotlyData, canvas) {
        // Проверяем, существует ли родительский элемент canvas
        if (!canvas.parentNode) return;
        
        // Создаем временный div для рендеринга Plotly
        const tempDiv = document.createElement('div');
        tempDiv.style.width = config.thumbnail.width + 'px';
        tempDiv.style.height = config.thumbnail.height + 'px';
        tempDiv.style.position = 'absolute';
        tempDiv.style.left = '-9999px';
        document.body.appendChild(tempDiv);
        
        try {
            // Рендерим упрощенный график
            window.Plotly.newPlot(tempDiv, plotlyData.data, plotlyData.layout, {
                staticPlot: true, // Делаем статический график
                displayModeBar: false // Скрываем панель инструментов
            }).then(() => {
                // Конвертируем в изображение
                window.Plotly.toImage(tempDiv, {
                    format: 'png',
                    width: config.thumbnail.width,
                    height: config.thumbnail.height
                }).then((imgData) => {
                    // Рисуем изображение на холсте
                    const img = new Image();
                    img.onload = function() {
                        const ctx = canvas.getContext('2d');
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        
                        // Добавляем индикатор интерактивности
                        ctx.fillStyle = 'rgba(65, 105, 225, 0.7)';
                        ctx.beginPath();
                        ctx.arc(canvas.width - 15, 15, 10, 0, 2 * Math.PI);
                        ctx.fill();
                        
                        ctx.fillStyle = 'white';
                        ctx.font = 'bold 12px Arial';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText('i', canvas.width - 15, 15);
                        
                        // Удаляем временные элементы
                        document.body.removeChild(tempDiv);
                    };
                    img.src = imgData;
                }).catch((err) => {
                    console.error('Ошибка при конвертации в изображение:', err);
                    document.body.removeChild(tempDiv);
                    renderFallbackThumbnail(canvas, vizId);
                });
            }).catch((err) => {
                console.error('Ошибка при рендеринге графика:', err);
                document.body.removeChild(tempDiv);
                renderFallbackThumbnail(canvas, vizId);
            });
        } catch (e) {
            console.error('Ошибка при создании миниатюры:', e);
            if (document.body.contains(tempDiv)) {
                document.body.removeChild(tempDiv);
            }
            renderFallbackThumbnail(canvas, vizId);
        }
    }

    /**
     * Очищает ресурсы после создания миниатюры
     * @param {HTMLIFrameElement} iframe - iframe для удаления
     * @param {string} vizId - ID визуализации
     */
    function cleanupThumbnailProcess(iframe, vizId) {
        if (iframe && iframe.parentNode) {
            iframe.parentNode.removeChild(iframe);
        }
        
        // Помечаем визуализацию как обработанную
        const vizInfo = pendingThumbnails.get(vizId);
        if (vizInfo) {
            vizInfo.processed = true;
        }
    }

    /**
     * Создаёт заглушку для миниатюры в случае ошибки
     * @param {HTMLCanvasElement} canvas - холст для миниатюры
     * @param {string} vizId - ID визуализации
     */
    function renderFallbackThumbnail(canvas, vizId) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Рисуем фон
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Рисуем иконку графика
        ctx.strokeStyle = '#adb5bd';
        ctx.lineWidth = 2;
        
        // Рисуем упрощенную диаграмму
        ctx.beginPath();
        ctx.moveTo(canvas.width/4, canvas.height*3/4);
        ctx.lineTo(canvas.width/3, canvas.height/2);
        ctx.lineTo(canvas.width/2, canvas.height*2/3);
        ctx.lineTo(canvas.width*2/3, canvas.height/3);
        ctx.lineTo(canvas.width*3/4, canvas.height/2);
        ctx.stroke();
        
        // Добавляем подпись
        ctx.fillStyle = '#6c757d';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Предпросмотр недоступен', canvas.width/2, canvas.height/4);
        
        // Добавляем ID визуализации
        ctx.font = '12px Arial';
        ctx.fillText('ID: ' + vizId, canvas.width/2, canvas.height*3/4);
    }

    /**
     * Обработчик сообщений от iframe
     * @param {MessageEvent} event - событие сообщения
     */
    function handleMessage(event) {
        if (event.data && event.data.type === 'thumbnail-data') {
            const { vizId, data } = event.data;
            
            // Находим информацию о визуализации
            const vizInfo = pendingThumbnails.get(vizId);
            if (vizInfo && !vizInfo.processed) {
                // Находим canvas для визуализации
                const canvas = vizInfo.container.querySelector(config.selectors.thumbnailCanvas);
                
                if (canvas && data && data.success) {
                    // Создаем миниатюру из данных
                    createPlotlyThumbnail(vizId, data, canvas);
                } else {
                    // Создаем заглушку
                    if (canvas) {
                        renderFallbackThumbnail(canvas, vizId);
                    }
                }
                
                // Помечаем визуализацию как обработанную
                vizInfo.processed = true;
            }
        }
    }

    /**
     * Инициализирует создание миниатюр для всех визуализаций
     */
    function initThumbnails() {
        // Получаем данные о визуализациях
        if (window.visualizationManager && window.visualizationManager.getVisualizations) {
            const visualizations = window.visualizationManager.getVisualizations();
            
            // Для каждой карточки визуализации
            document.querySelectorAll(config.selectors.visualizationCard).forEach(card => {
                const vizId = card.dataset.vizId;
                
                if (vizId) {
                    // Находим данные визуализации
                    const vizData = visualizations.find(v => v.id === vizId);
                    
                    if (vizData) {
                        // Создаем контейнер для миниатюры
                        const container = document.createElement('div');
                        container.className = config.selectors.thumbnail.substring(1);
                        container.style.width = '100%';
                        container.style.height = '100%';
                        container.style.display = 'block';
                        container.style.position = 'absolute';
                        container.style.top = '0';
                        container.style.left = '0';
                        container.style.zIndex = '1';
                        
                        // Добавляем контейнер в карточку
                        const contentContainer = card.querySelector(config.selectors.visualizationContent);
                        if (contentContainer) {
                            contentContainer.appendChild(container);
                            
                            // Создаем миниатюру
                            createThumbnail(vizId, vizData.path, container);
                            
                            // Добавляем индикатор загрузки
                            const loader = contentContainer.querySelector('.visualization-loader');
                            if (loader) {
                                loader.style.display = 'none';
                            }
                        }
                    }
                }
            });
        }
    }

    // Инициализация при загрузке DOM
    function init() {
        isDOMReady = true;
        
        // Добавляем обработчик сообщений
        window.addEventListener('message', handleMessage);
        
        // Инициализируем создание миниатюр
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(initThumbnails, 100);
        } else {
            window.addEventListener('load', () => {
                setTimeout(initThumbnails, 100);
            });
        }
    }

    // API для внешнего использования
    window.vizThumbnails = {
        createThumbnail,
        renderFallbackThumbnail
    };

    // Инициализация при загрузке DOM
    if (document.readyState !== 'loading') {
        init();
    } else {
        document.addEventListener('DOMContentLoaded', init);
    }
})();