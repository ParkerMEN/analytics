/**
 * Хелперы для работы с модальными окнами
 */
(function() {
    'use strict';
    
    // Проверяем наличие нового менеджера миниатюр
    const hasThumbnailManager = typeof window.thumbnailManager !== 'undefined';
    
    // Инициализация улучшенных обработчиков закрытия
    function enhanceModalClose() {
        // Если используется новый менеджер, делегируем ему обработку модалок
        if (hasThumbnailManager) {
            console.log('[ModalHelpers] Используется централизованный менеджер миниатюр');
            return;
        }
        
        // Иначе используем старую логику
        console.log('[ModalHelpers] Используется старая логика обработки модальных окон');
        
        // Избегаем дублирования обработчиков с помощью специального атрибута
        const closeButtons = document.querySelectorAll('.modal .btn-close, .modal button[data-dismiss="modal"], button.закрыть, [data-bs-dismiss="modal"], [data-dismiss="modal"], .close');
        
        closeButtons.forEach(button => {
            // Проверяем, был ли уже добавлен обработчик
            if (button.hasAttribute('data-enhanced-close')) {
                return;
            }
            
            // Помечаем кнопку обработчиком
            button.setAttribute('data-enhanced-close', 'true');
            
            // Добавляем безопасный обработчик события, не удаляя существующие
            button.addEventListener('click', function(e) {
                // Не отменяем стандартное поведение Bootstrap, но добавляем свою логику
                
                // Находим ближайший модальный контейнер
                const modal = this.closest('.modal');
                
                if (modal) {
                    // Запускаем усиленное закрытие после стандартного
                    setTimeout(() => {
                        closeModalCompletely(modal);
                    }, 150);
                }
            });
        });
        
        // Обработчик глобальных событий Escape
        if (!window._escapeHandlerAttached) {
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    // Найти все видимые модальные окна
                    const visibleModals = document.querySelectorAll('.modal.show, .modal[style*="display: block"]');
                    
                    // Закрыть последнее (верхнее) модальное окно
                    if (visibleModals.length > 0) {
                        const topModal = visibleModals[visibleModals.length - 1];
                        closeModalCompletely(topModal);
                    }
                }
            });
            
            window._escapeHandlerAttached = true;
        }
        
        // Добавляем обработчик для backdrop
        document.addEventListener('click', function(e) {
            // Если клик был по backdrop
            if (e.target.classList.contains('modal') && e.target.classList.contains('show')) {
                const backdropCloseable = e.target.getAttribute('data-bs-backdrop') !== 'static';
                if (backdropCloseable) {
                    setTimeout(() => {
                        closeModalCompletely(e.target);
                    }, 150);
                }
            }
        });
    }
    
    // Полное закрытие модального окна
    function closeModalCompletely(modal) {
        // Если используется новый менеджер, делегируем ему закрытие модалок
        if (hasThumbnailManager && window.thumbnailManager.closeAll) {
            window.thumbnailManager.closeAll();
            return;
        }
        
        if (!modal) return;
        
        // Сохраняем ссылку на документ
        const doc = modal.ownerDocument;
        
        // Проверяем, открыто ли модальное окно
        const isModalVisible = modal.classList.contains('show') || 
                              modal.style.display === 'block';
        
        if (!isModalVisible) {
            console.log('Модальное окно уже закрыто');
            return;
        }
        
        // Закрываем через Bootstrap API
        if (window.bootstrap && bootstrap.Modal) {
            try {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                    console.log('Модальное окно закрыто через Bootstrap API');
                }
            } catch (e) {
                console.error('Ошибка при закрытии через Bootstrap API:', e);
            }
        }
        
        // Принудительно очищаем состояние модального окна
        setTimeout(() => {
            // 1. Скрываем модальное окно
            modal.style.display = 'none';
            modal.classList.remove('show');
            modal.setAttribute('aria-hidden', 'true');
            modal.removeAttribute('aria-modal');
            modal.removeAttribute('role');
            
            // 2. Тщательно удаляем все backdrop элементы
            const backdrops = doc.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                backdrop.remove();
            });
            
            // 3. Проверяем, есть ли еще открытые модальные окна
            const otherModals = doc.querySelectorAll('.modal.show');
            const hasOpenModals = otherModals.length > 0;
            
            if (!hasOpenModals) {
                // 4. Полностью восстанавливаем состояние body
                const body = doc.body;
                body.classList.remove('modal-open');
                body.style.overflow = '';
                body.style.paddingRight = '';
                body.removeAttribute('data-bs-overflow');
                body.removeAttribute('data-bs-padding-right');
                body.removeAttribute('aria-hidden');
                
                // 5. Удаляем inline-стили, которые могут блокировать интерфейс
                body.style.position = '';
                body.style.top = '';
                body.style.height = '';
            }
            
            // 6. Очищаем фокус, чтобы предотвратить непредсказуемое поведение
            if (document.activeElement && document.activeElement.blur) {
                document.activeElement.blur();
            }
            
            console.log('Принудительная очистка модального окна завершена');
        }, 50); // Небольшая задержка для корректной работы с Bootstrap
    }
    
    // Добавляем функцию для полноэкранного режима (новая функция)
    function setupFullscreenButton() {
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', function() {
                const vizModal = document.getElementById('vizModal');
                const vizFullscreenModal = document.getElementById('vizFullscreenModal');
                
                // Копирование содержимого между модальными окнами
                const sourceContainer = document.getElementById('viz-container');
                const targetContainer = document.getElementById('fullscreen-viz-container');
                
                if (sourceContainer && targetContainer) {
                    // Запоминаем оригинальный iframe для извлечения URL и других данных
                    const originalIframe = sourceContainer.querySelector('iframe');
                    if (!originalIframe) {
                        console.error('[ModalHelpers] Не найден исходный iframe');
                        return;
                    }
                    
                    const iframeSrc = originalIframe.src;
                    
                    // Собираем данные о диаграмме из исходного iframe, если возможно
                    let chartType = 'unknown';
                    try {
                        if (originalIframe.contentWindow._lastChartType) {
                            chartType = originalIframe.contentWindow._lastChartType;
                        } else if (window._lastPlotlySizes && window._lastPlotlySizes[originalIframe.id]) {
                            chartType = window._lastPlotlySizes[originalIframe.id].chartType;
                        }
                    } catch (e) {
                        console.warn('[ModalHelpers] Не удалось получить тип диаграммы из iframe:', e);
                    }
                    
                    console.log(`[ModalHelpers] Тип диаграммы для полноэкранного режима: ${chartType}`);
                    
                    // Очищаем целевой контейнер
                    targetContainer.innerHTML = '';
                    
                    // Создаем новый iframe вместо копирования существующего
                    if (iframeSrc) {
                        // Создаем загрузчик
                        const loader = document.createElement('div');
                        loader.className = 'visualization-loader';
                        loader.innerHTML = '<div class="visualization-spinner"></div>';
                        targetContainer.appendChild(loader);
                        
                        // Создаем новый iframe с тем же источником
                        const newIframe = document.createElement('iframe');
                        newIframe.className = 'viz-modal-iframe';
                        newIframe.id = 'fullscreen-viz-iframe-' + Date.now();
                        newIframe.style.width = '100%';
                        newIframe.style.height = '100%';
                        newIframe.style.border = 'none';
                        
                        // Добавляем параметр chart_type в URL для передачи информации о типе диаграммы
                        const separator = iframeSrc.includes('?') ? '&' : '?';
                        newIframe.src = `${iframeSrc}${separator}chart_type=${chartType}&fullscreen=true`;
                        
                        // Сохраняем информацию о типе диаграммы для дальнейшего использования
                        window._lastFullscreenChartType = chartType;
                        
                        // Обработчик завершения загрузки iframe
                        newIframe.onload = function() {
                            if (loader) loader.style.display = 'none';
                            
                            // Пытаемся передать тип диаграммы непосредственно в контент iframe
                            try {
                                setTimeout(() => {
                                    newIframe.contentWindow.postMessage({
                                        type: 'set-chart-type',
                                        chartType: chartType
                                    }, '*');
                                }, 100);
                            } catch (e) {
                                console.warn('[ModalHelpers] Не удалось передать тип диаграммы в iframe', e);
                            }
                        };
                        
                        targetContainer.appendChild(newIframe);
                    } else {
                        console.error('[ModalHelpers] Не удалось получить URL исходного iframe');
                        return;
                    }
                    
                    // Закрываем обычное модальное окно
                    if (window.bootstrap && vizModal) {
                        const modalInstance = bootstrap.Modal.getInstance(vizModal);
                        if (modalInstance) modalInstance.hide();
                    }
                    
                    // Открываем полноэкранное модальное окно
                    if (window.bootstrap && vizFullscreenModal) {
                        const fullscreenModalInstance = new bootstrap.Modal(vizFullscreenModal);
                        fullscreenModalInstance.show();
                        
                        // Добавляем обработчик для оптимизации через новый адаптер
                        vizFullscreenModal.addEventListener('shown.bs.modal', function() {
                            console.log('[ModalHelpers] Модальное окно открыто, запускаем оптимизацию диаграммы');
                            
                            setTimeout(() => {
                                const iframe = targetContainer.querySelector('iframe');
                                if (!iframe) return;
                                
                                // Используем новый адаптер, если доступен
                                if (window.plotlyFullscreenAdapter) {
                                    console.log('[ModalHelpers] Оптимизация через plotlyFullscreenAdapter');
                                    window.plotlyFullscreenAdapter.optimizeChart(iframe)
                                        .catch(err => {
                                            console.error('[ModalHelpers] Ошибка оптимизации через адаптер:', err);
                                            
                                            // Теперь вызываем через window.modalHelpers
                                            window.modalHelpers.fallbackResizing(iframe, chartType, targetContainer);
                                        });
                                } else {
                                    // Теперь вызываем через window.modalHelpers
                                    window.modalHelpers.fallbackResizing(iframe, chartType, targetContainer);
                                }
                            }, 200);
                        }, { once: true });
                    }
                }
            });
        }
    }
    
    // Вспомогательная функция для запасного варианта ресайзинга
    function fallbackResizing(iframe, chartType, targetContainer) {
        console.log('[ModalHelpers] Используется запасной вариант ресайзинга');
        
        // Серия попыток с интервалом 300-350мс
        for (let i = 1; i <= 6; i++) {
            setTimeout(() => {
                if (!iframe) return;
                
                console.log(`[PlotlyResize] Попытка ресайза #${i} через ${i * 350}ms`);
                
                // 1. Прямой ресайз через iframe
                try {
                    const iframeWindow = iframe.contentWindow;
                    const iframeDocument = iframe.contentDocument || iframeWindow.document;
                    const plotlyElements = iframeDocument.querySelectorAll('.plotly-graph-div');
                    
                    if (plotlyElements.length > 0 && iframeWindow.Plotly) {
                        // Исправлено: убираем переназначение переменной container
                        const plotlyDiv = plotlyElements[0].id;
                        
                        // Точный расчет размеров с учетом padding
                        const style = window.getComputedStyle(targetContainer);
                        const paddingX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
                        const paddingY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
                        
                        const width = targetContainer.clientWidth - paddingX;
                        const height = targetContainer.clientHeight - paddingY;
                        
                        console.log(`[PlotlyResize] Применяем размеры ${width}x${height} к графику типа ${chartType}`);
                        
                        // Отправляем сообщение в iframe для изменения размеров
                        iframeWindow.postMessage({
                            type: 'resize-plotly',
                            width: width,
                            height: height,
                            plotlyDiv: plotlyDiv,
                            chartType: chartType || window._lastFullscreenChartType || 'unknown'
                        }, '*');
                    }
                } catch (e) {
                    console.error('[PlotlyResize] Ошибка при прямом ресайзе:', e);
                }
                
                // 2. Используем стандартные методы
                if (iframe.id && window.iframeChartHandler) {
                    window.iframeChartHandler.resizeIframeChart(iframe.id, chartType);
                }
                
                // 3. Используем глобальную функцию для ресайза
                if (window.resizeModalChart) {
                    window.resizeModalChart('vizFullscreenModal', chartType);
                }
            }, i * 350); // Использование возрастающих задержек
        }
    }
    
    // Экспортируем функции для использования в других модулях
    window.modalHelpers = {
        enhanceModalClose: enhanceModalClose,
        closeModalCompletely: closeModalCompletely,
        setupFullscreenButton: setupFullscreenButton,
        fallbackResizing: fallbackResizing // Добавляем функцию в экспорт
    };
    
    // Автоинициализация
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            enhanceModalClose();
            setupFullscreenButton();
        });
    } else {
        enhanceModalClose();
        setupFullscreenButton();
    }
    
    // Периодически проверяем новые кнопки закрытия (для динамически добавленных модалок)
    setInterval(enhanceModalClose, 2000);
})();