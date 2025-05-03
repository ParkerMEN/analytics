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
        console.log('[ModalHelpers] Настройка кнопки полноэкранного режима');
        
        const fullscreenBtns = document.querySelectorAll('.viz-fullscreen-btn');
        if (fullscreenBtns.length > 0) {
            fullscreenBtns.forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const vizCard = this.closest('.visualization-card');
                    if (!vizCard) return;
                    
                    const vizId = vizCard.dataset.vizId;
                    if (!vizId) return;
                    
                    console.log(`[ModalHelpers] Открытие визуализации ${vizId} в полноэкранном режиме`);
                    
                    // Если доступен thumbnailManager, используем его метод
                    if (window.thumbnailManager && typeof window.thumbnailManager.openFullscreen === 'function') {
                        window.thumbnailManager.openFullscreen(vizId);
                    } else {
                        // Запасной вариант
                        openFullscreenVisualization(vizId);
                    }
                });
            });
        } else {
            console.log('[ModalHelpers] Не найдены кнопки полноэкранного режима');
        }
    }
    
    // Функция для открытия визуализации в полноэкранном режиме (запасной вариант)
    function openFullscreenVisualization(vizId) {
        if (!window.visualizationManager) {
            console.error('[ModalHelpers] visualizationManager не доступен');
            return;
        }
        
        const vizData = window.visualizationManager.getVisualizationById(vizId);
        if (!vizData) {
            console.error(`[ModalHelpers] Визуализация с ID ${vizId} не найдена`);
            return;
        }
        
        const vizFullscreenModal = document.getElementById('vizFullscreenModal');
        if (!vizFullscreenModal) {
            console.error('[ModalHelpers] Модальное окно #vizFullscreenModal не найдено');
            return;
        }
        
        // Получаем контейнер для контента
        const targetContainer = document.getElementById('fullscreen-viz-container');
        if (!targetContainer) {
            console.error('[ModalHelpers] Контейнер #fullscreen-viz-container не найден');
            return;
        }
        
        // Устанавливаем заголовок
        const titleElement = vizFullscreenModal.querySelector('.modal-title');
        if (titleElement) {
            titleElement.textContent = vizData.title;
        }
        
        // Очищаем целевой контейнер
        targetContainer.innerHTML = '';
        
        // Создаем iframe для визуализации
        const iframe = document.createElement('iframe');
        iframe.className = 'viz-modal-iframe';
        iframe.src = `${window.visualizationsBasePath || '../analytics_output/visualizations/'}${vizData.path}`;
        iframe.id = `fullscreen-iframe-${vizId}`;
        iframe.setAttribute('allowfullscreen', 'true');
        iframe.onload = function() {
            console.log(`[ModalHelpers] Загружен iframe для визуализации ${vizId}`);
            
            // Изменяем размеры iframe после загрузки
            setTimeout(() => {
                if (window.plotlyFullscreenAdapter && window.plotlyFullscreenAdapter.optimizeChart) {
                    window.plotlyFullscreenAdapter.optimizeChart(iframe);
                }
            }, 300);
        };
        
        targetContainer.appendChild(iframe);
        
        // Открываем модальное окно через Bootstrap
        if (window.bootstrap && bootstrap.Modal) {
            const bsModal = new bootstrap.Modal(vizFullscreenModal);
            bsModal.show();
        } else {
            // Запасной вариант открытия
            vizFullscreenModal.style.display = 'block';
            vizFullscreenModal.classList.add('show');
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