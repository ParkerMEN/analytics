/**
 * Thumbnail Manager
 * 
 * Централизованный менеджер для работы с миниатюрами визуализаций.
 * Управляет созданием миниатюр, обработкой событий и модальными окнами.
 * 
 * @version 1.0.0
 */

(function() {
    'use strict';
    
    // ========================
    // Конфигурация
    // ========================
    const config = {
        // Селекторы элементов
        selectors: {
            visualizationCard: '.visualization-card',
            visualizationContent: '.visualization-content',
            thumbnail: '.viz-thumbnail',
            thumbnailContainer: '.viz-thumbnail-container',
            loader: '.visualization-loader',
            fullscreenBtn: '.viz-fullscreen-btn',
            standardModal: '#vizModal',
            fullscreenModal: '#vizFullscreenModal',
            vizContainer: '#viz-container',
            fullscreenContainer: '#fullscreen-viz-container',
            modalTitle: '.modal-title',
            closeBtn: '.btn-close, [data-bs-dismiss="modal"], [data-dismiss="modal"]'
        },
        
        // Пути к ресурсам
        paths: {
            thumbnails: '../analytics_output/visualizations/',
            visualizations: '../analytics_output/visualizations/'
        },
        
        // Классы для динамического создания элементов
        classes: {
            thumbnail: 'viz-thumbnail',
            fullscreenBtn: 'viz-fullscreen-btn',
            loader: 'visualization-loader',
            spinner: 'visualization-spinner'
        },
        
        // Таймауты и задержки
        timeouts: {
            modalTransition: 300,
            cleanupDelay: 100
        },
        
        // Включение/отключение логирования для отладки
        debug: true
    };
    
    // ========================
    // Состояние менеджера
    // ========================
    const state = {
        // Кэш сгенерированных миниатюр
        thumbnailCache: new Map(),
        
        // Открытые модальные окна
        openModals: new Set(),
        
        // Регистрация обработчиков событий для очистки
        eventHandlers: new Map(),
        
        // Флаги состояния
        isInitialized: false,
        isProcessingModal: false
    };
    
    // ========================
    // Вспомогательные функции
    // ========================
    const utils = {
        // Логирование с префиксом
        log: function(message, level = 'info') {
            if (!config.debug) return;
            
            const prefix = '[ThumbnailManager]';
            
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
        
        // Безопасное получение DOM элемента
        getElement: function(selector, parent = document) {
            try {
                return parent.querySelector(selector);
            } catch (e) {
                utils.log(`Ошибка при получении элемента ${selector}: ${e.message}`, 'error');
                return null;
            }
        },
        
        // Безопасное получение всех DOM элементов
        getAllElements: function(selector, parent = document) {
            try {
                return parent.querySelectorAll(selector);
            } catch (e) {
                utils.log(`Ошибка при получении элементов ${selector}: ${e.message}`, 'error');
                return [];
            }
        },
        
        // Регистрация обработчика события с возможностью очистки
        registerEventHandler: function(element, eventType, handler, options = {}) {
            if (!element) return false;
            
            try {
                const wrappedHandler = function(event) {
                    return handler.call(this, event);
                };
                
                element.addEventListener(eventType, wrappedHandler, options);
                
                // Запоминаем обработчик для возможности удаления
                const key = `${element.id || 'elem'}_${eventType}_${Date.now()}`;
                state.eventHandlers.set(key, {
                    element: element,
                    type: eventType,
                    handler: wrappedHandler,
                    options: options
                });
                
                return key;
            } catch (e) {
                utils.log(`Ошибка при регистрации обработчика события ${eventType}: ${e.message}`, 'error');
                return false;
            }
        },
        
        // Удаление зарегистрированного обработчика события
        removeEventHandler: function(handlerId) {
            if (!handlerId) return false;
            
            const handlerInfo = state.eventHandlers.get(handlerId);
            if (handlerInfo) {
                try {
                    handlerInfo.element.removeEventListener(
                        handlerInfo.type,
                        handlerInfo.handler,
                        handlerInfo.options
                    );
                    
                    state.eventHandlers.delete(handlerId);
                    return true;
                } catch (e) {
                    utils.log(`Ошибка при удалении обработчика события: ${e.message}`, 'error');
                    return false;
                }
            }
            
            return false;
        },
        
        // Проверка наличия Bootstrap
        hasBootstrap: function() {
            return typeof bootstrap !== 'undefined' && bootstrap.Modal;
        },
        
        // Проверка наличия необходимых компонентов
        checkDependencies: function() {
            const missing = [];
            
            if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
                missing.push('Bootstrap Modal');
            }
            
            if (typeof window.visualizationManager === 'undefined') {
                missing.push('visualizationManager');
            }
            
            return {
                ready: missing.length === 0,
                missing: missing
            };
        }
    };
    
    // ========================
    // Управление миниатюрами
    // ========================
    const thumbnailManager = {
        // Инициализация менеджера миниатюр
        init: function() {
            if (state.isInitialized) {
                utils.log('Менеджер миниатюр уже инициализирован');
                return;
            }
            
            utils.log('Инициализация менеджера миниатюр');
            
            // Проверка и обеспечение visualizationManager
            if (!window.visualizationManager) {
                utils.log('Отсутствует необходимая зависимость: visualizationManager', 'error');
                
                // Создаем базовую версию
                window.visualizationManager = {
                    getVisualizations: function() {
                        return [{
                            id: 'viz_chastota',
                            title: 'Частота упоминаний достоинств и их связь с рейтингом',
                            path: 'viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
                            type: 'bar',
                            category: 'analysis'
                        }];
                    },
                    getVisualizationById: function(id) {
                        const visualizations = this.getVisualizations();
                        return visualizations.find(v => v.id === id);
                    }
                };
                
                utils.log('Создана резервная версия visualizationManager');
            }
            
            // Инициализация обработчиков модальных окон
            this.setupModalHandlers();
            
            // Создание миниатюр для всех карточек
            this.generateAllThumbnails();
            
            // Настройка мутационного обсервера для динамически добавляемых карточек
            this.setupMutationObserver();
            
            // Установка глобальных обработчиков Escape и cleanup
            this.setupGlobalHandlers();
            
            state.isInitialized = true;
            utils.log('Менеджер миниатюр инициализирован успешно');
        },
        
        // Генерация миниатюр для всех карточек
        generateAllThumbnails: function() {
            utils.log('Генерация миниатюр для всех карточек');
            
            const cards = utils.getAllElements(config.selectors.visualizationCard);
            if (cards.length === 0) {
                utils.log('Не найдено карточек визуализаций', 'warn');
                return;
            }
            
            utils.log(`Найдено ${cards.length} карточек визуализаций`);
            
            cards.forEach(card => {
                // Получаем ID визуализации из атрибута
                const vizId = card.dataset.vizId;
                if (!vizId) {
                    utils.log('Карточка без ID визуализации', 'warn');
                    return;
                }
                
                // Получаем данные визуализации
                const vizData = window.visualizationManager.getVisualizationById(vizId);
                if (!vizData) {
                    utils.log(`Не найдены данные для визуализации с ID: ${vizId}`, 'warn');
                    return;
                }
                
                // Создаем миниатюру
                this.generateThumbnail(card, vizData);
            });
        },
        
        // Генерация отдельной миниатюры
        generateThumbnail: function(card, vizData) {
            utils.log(`Генерация миниатюры для визуализации: ${vizData.id}`);
            
            // Находим контейнер контента
            const content = utils.getElement(config.selectors.visualizationContent, card);
            if (!content) {
                utils.log('Не найден контейнер для контента', 'warn');
                return;
            }
            
            // Скрываем загрузчик, если есть
            const loader = utils.getElement(config.selectors.loader, content);
            if (loader) {
                loader.style.display = 'none';
            }
            
            // Удаляем существующую миниатюру, если есть
            const existingThumbnail = utils.getElement(config.selectors.thumbnail, content);
            if (existingThumbnail) {
                existingThumbnail.remove();
            }
            
            // Создаем контейнер для миниатюры
            const thumbnail = document.createElement('div');
            thumbnail.className = config.classes.thumbnail;
            thumbnail.dataset.vizId = vizData.id;
            thumbnail.style.width = '100%';
            thumbnail.style.height = '100%';
            thumbnail.style.position = 'absolute';
            thumbnail.style.top = '0';
            thumbnail.style.left = '0';
            thumbnail.style.zIndex = '1';
            thumbnail.style.backgroundColor = '#f8f9fa';
            thumbnail.style.display = 'flex';
            thumbnail.style.alignItems = 'center';
            thumbnail.style.justifyContent = 'center';
            thumbnail.style.cursor = 'pointer';
            
            // Создаем IMG элемент для миниатюры
            const img = document.createElement('img');
            img.className = 'viz-thumbnail-canvas';
            img.alt = vizData.title || `Визуализация ${vizData.id}`;
            img.style.maxWidth = '100%';
            img.style.maxHeight = '100%';
            img.style.objectFit = 'contain';
            
            // Формируем путь к PNG файлу
            const pngPath = getThumbnailPath(vizData);
            img.src = pngPath;
            
            // Обработчик ошибки загрузки изображения
            img.onerror = () => {
                utils.log(`Ошибка загрузки миниатюры: ${pngPath}`, 'error');
                img.style.display = 'none';
                
                // Создаем заглушку
                const errorContainer = document.createElement('div');
                errorContainer.style.padding = '10px';
                errorContainer.style.textAlign = 'center';
                
                const errorIcon = document.createElement('div');
                errorIcon.innerHTML = '⚠️';
                errorIcon.style.fontSize = '24px';
                errorContainer.appendChild(errorIcon);
                
                const errorText = document.createElement('div');
                errorText.textContent = 'Не удалось загрузить визуализацию';
                errorText.style.color = '#dc3545';
                errorText.style.fontSize = '12px';
                errorText.style.marginTop = '5px';
                errorContainer.appendChild(errorText);
                
                // Кнопка повторной попытки
                const retryButton = document.createElement('button');
                retryButton.className = 'btn btn-sm btn-outline-primary mt-2 retry-btn';
                retryButton.textContent = 'Повторить';
                errorContainer.appendChild(retryButton);
                
                // Регистрируем обработчик для кнопки повтора
                utils.registerEventHandler(retryButton, 'click', (e) => {
                    e.stopPropagation();
                    this.generateThumbnail(card, vizData);
                });
                
                thumbnail.appendChild(errorContainer);
            };
            
            // Добавляем изображение в контейнер
            thumbnail.appendChild(img);
            content.appendChild(thumbnail);
            
            // Добавляем обработчик клика на миниатюру
            const thumbnailHandler = (e) => {
                // Проверяем, был ли клик по кнопке или другому интерактивному элементу
                if (e.target.closest('.retry-btn') || e.target.closest(config.selectors.fullscreenBtn)) {
                    return;
                }
                
                this.openVisualizationModal(vizData);
            };
            
            // Регистрируем обработчик
            utils.registerEventHandler(thumbnail, 'click', thumbnailHandler);
            
            // Создаем кнопку полноэкранного режима, если её нет
            let fullscreenBtn = utils.getElement(config.selectors.fullscreenBtn, content);
            if (!fullscreenBtn) {
                fullscreenBtn = document.createElement('button');
                fullscreenBtn.className = config.classes.fullscreenBtn;
                fullscreenBtn.innerHTML = '<i class="bi bi-arrows-fullscreen"></i>';
                fullscreenBtn.title = 'Открыть визуализацию в полноэкранном режиме';
                content.appendChild(fullscreenBtn);
                
                // ВАЖНО: Регистрируем обработчик для кнопки полноэкранного режима
                utils.registerEventHandler(fullscreenBtn, 'click', (e) => {
                    // Останавливаем всплытие события, чтобы не сработал обработчик миниатюры
                    e.stopPropagation();
                    e.preventDefault();
                    
                    // Открываем полноэкранный режим
                    this.openFullscreenModal(vizData);
                });
            }
            
            // Кэшируем созданную миниатюру
            state.thumbnailCache.set(vizData.id, {
                element: thumbnail,
                vizData: vizData
            });
            
            utils.log(`Миниатюра для визуализации ${vizData.id} создана успешно`);
        },
        
        // ========================
        // Управление модальными окнами
        // ========================
        
        // Настройка обработчиков модальных окон
        setupModalHandlers: function() {
            utils.log('Настройка обработчиков модальных окон');
            
            const standardModal = utils.getElement(config.selectors.standardModal);
            const fullscreenModal = utils.getElement(config.selectors.fullscreenModal);
            
            if (standardModal) {
                this.enhanceModal(standardModal);
                
                // Обработчик события скрытия модального окна
                standardModal.addEventListener('hidden.bs.modal', () => {
                    this.onModalHidden(standardModal);
                });
            }
            
            if (fullscreenModal) {
                this.enhanceModal(fullscreenModal);
                
                // Обработчик события скрытия полноэкранного модального окна
                fullscreenModal.addEventListener('hidden.bs.modal', () => {
                    this.onModalHidden(fullscreenModal);
                });
            }
            
            // Настройка кнопки перехода в полноэкранный режим из модального окна
            const fullscreenBtn = document.getElementById('fullscreen-btn');
            if (fullscreenBtn) {
                utils.registerEventHandler(fullscreenBtn, 'click', () => {
                    if (standardModal && state.openModals.has(standardModal)) {
                        // Получаем текущую визуализацию
                        const vizContainer = utils.getElement(config.selectors.vizContainer);
                        const fullscreenContainer = utils.getElement(config.selectors.fullscreenContainer);
                        const modalTitle = utils.getElement(config.selectors.modalTitle, standardModal);
                        
                        // Запоминаем заголовок для переноса в полноэкранный режим
                        const title = modalTitle ? modalTitle.textContent : 'Визуализация';
                        
                        if (vizContainer && fullscreenContainer) {
                            // Копируем содержимое
                            fullscreenContainer.innerHTML = vizContainer.innerHTML;
                            
                            // Устанавливаем заголовок в полноэкранном режиме
                            const fullscreenTitle = utils.getElement(config.selectors.modalTitle, fullscreenModal);
                            if (fullscreenTitle) {
                                fullscreenTitle.textContent = title;
                            }
                            
                            // Закрываем стандартное модальное окно и открываем полноэкранное
                            this.closeModal(standardModal);
                            this.openModal(fullscreenModal);
                        }
                    }
                });
            }
        },
        
        // Улучшение стандартного модального окна
        enhanceModal: function(modal) {
            if (!modal) return;
            
            // Находим кнопки закрытия внутри модального окна
            const closeButtons = utils.getAllElements(config.selectors.closeBtn, modal);
            
            closeButtons.forEach(btn => {
                // Проверяем, был ли уже добавлен обработчик
                if (btn.hasAttribute('data-enhanced')) {
                    return;
                }
                
                // Добавляем обработчик для кнопки закрытия
                utils.registerEventHandler(btn, 'click', () => {
                    this.closeModal(modal);
                });
                
                // Помечаем кнопку, чтобы избежать дублирования
                btn.setAttribute('data-enhanced', 'true');
            });
        },
        
        // Открытие стандартного модального окна с визуализацией
        openVisualizationModal: function(vizData) {
            utils.log(`Открытие модального окна для визуализации: ${vizData.id}`);
            
            const modal = utils.getElement(config.selectors.standardModal);
            if (!modal) {
                utils.log('Модальное окно не найдено', 'error');
                return;
            }
            
            // Устанавливаем заголовок
            const modalTitle = utils.getElement(config.selectors.modalTitle, modal);
            if (modalTitle) {
                modalTitle.textContent = vizData.title || `Визуализация ${vizData.id}`;
            }
            
            // Получаем контейнер для контента
            const container = utils.getElement(config.selectors.vizContainer);
            if (!container) {
                utils.log('Контейнер для визуализации не найден', 'error');
                return;
            }
            
            // Очищаем контейнер
            container.innerHTML = '';
            
            // Создаем загрузчик
            const loader = document.createElement('div');
            loader.className = config.classes.loader;
            loader.innerHTML = `<div class="${config.classes.spinner}"></div>`;
            container.appendChild(loader);
            
            // Создаем iframe для загрузки визуализации
            const iframe = document.createElement('iframe');
            iframe.className = 'viz-modal-iframe';
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.style.opacity = '0';
            iframe.style.transition = 'opacity 0.3s';
            iframe.src = config.paths.visualizations + vizData.path;
            container.appendChild(iframe);
            
            // Обработчик загрузки iframe
            iframe.onload = function() {
                loader.style.display = 'none';
                iframe.style.opacity = '1';
            };
            
            // Открываем модальное окно
            this.openModal(modal);
        },
        
        // Открытие полноэкранного модального окна
        openFullscreenModal: function(vizData) {
            utils.log(`Открытие полноэкранного модального окна для визуализации: ${vizData.id}`);
            
            const modal = utils.getElement(config.selectors.fullscreenModal);
            if (!modal) {
                utils.log('Полноэкранное модальное окно не найдено', 'error');
                return;
            }
            
            // Устанавливаем заголовок
            const modalTitle = utils.getElement(config.selectors.modalTitle, modal);
            if (modalTitle) {
                modalTitle.textContent = vizData.title || `Визуализация ${vizData.id}`;
            }
            
            // Получаем контейнер для контента
            const container = utils.getElement(config.selectors.fullscreenContainer);
            if (!container) {
                utils.log('Контейнер для полноэкранной визуализации не найден', 'error');
                return;
            }
            
            // Очищаем контейнер
            container.innerHTML = '';
            
            // Создаем загрузчик
            const loader = document.createElement('div');
            loader.className = config.classes.loader;
            loader.innerHTML = `<div class="${config.classes.spinner}"></div>`;
            container.appendChild(loader);
            
            // Создаем iframe для загрузки визуализации
            const iframe = document.createElement('iframe');
            iframe.className = 'viz-modal-iframe';
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.style.opacity = '0';
            iframe.style.transition = 'opacity 0.3s';
            iframe.src = config.paths.visualizations + vizData.path;
            container.appendChild(iframe);
            
            // Обработчик загрузки iframe
            iframe.onload = function() {
                loader.style.display = 'none';
                iframe.style.opacity = '1';
            };
            
            // Открываем полноэкранное модальное окно
            this.openModal(modal);
        },
        
        // Общая функция открытия модального окна
        openModal: function(modal) {
            if (!modal) return;
            
            try {
                // Предотвращаем множественные операции с модальными окнами
                if (state.isProcessingModal) {
                    utils.log('Уже идет обработка модального окна, операция отложена', 'warn');
                    setTimeout(() => this.openModal(modal), config.timeouts.modalTransition);
                    return;
                }
                
                state.isProcessingModal = true;
                
                // Добавляем слушатель события завершения открытия модального окна
                const modalId = modal.id;
                const self = this;
                
                // Удаляем слушатель, если уже был добавлен
                if (modal._resizeListener) {
                    modal.removeEventListener('shown.bs.modal', modal._resizeListener);
                }
                
                // Создаем новый слушатель
                modal._resizeListener = function() {
                    utils.log(`Модальное окно ${modalId} полностью открыто, вызываем изменение размеров диаграмм`);
                    setTimeout(() => {
                        self.resizeModalCharts(modal);
                    }, 100); // Небольшая задержка для дополнительной гарантии
                };
                
                // Добавляем слушатель
                modal.addEventListener('shown.bs.modal', modal._resizeListener);
                
                // Открываем через Bootstrap API, если доступно
                if (utils.hasBootstrap()) {
                    const bsModal = new bootstrap.Modal(modal);
                    bsModal.show();
                    
                    // Добавляем в список открытых модальных окон
                    state.openModals.add(modal);
                } else {
                    // Ручное открытие, если Bootstrap недоступен
                    modal.style.display = 'block';
                    modal.classList.add('show');
                    document.body.classList.add('modal-open');
                    
                    // Создаем backdrop вручную
                    const backdrop = document.createElement('div');
                    backdrop.className = 'modal-backdrop fade show';
                    document.body.appendChild(backdrop);
                    
                    // Добавляем в список открытых модальных окон
                    state.openModals.add(modal);
                }
                
                utils.log(`Модальное окно ${modalId} открыто успешно`);
            } catch (e) {
                utils.log(`Ошибка при открытии модального окна: ${e.message}`, 'error');
            } finally {
                setTimeout(() => {
                    state.isProcessingModal = false;
                }, config.timeouts.modalTransition);
            }
        },
        
        // Добавляем новый метод для изменения размеров графиков в модальном окне
        resizeModalCharts: function(modal) {
            // Найти все iframe с графиками в модальном окне
            const iframes = utils.getAllElements('iframe.viz-modal-iframe', modal);
            
            iframes.forEach(iframe => {
                // Получаем ID iframe
                const iframeId = iframe.id || `iframe-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
                if (!iframe.id) iframe.id = iframeId;
                
                // Вызываем изменение размера через chart-adapter
                if (window.iframeChartHandler && typeof window.iframeChartHandler.resizeIframeChart === 'function') {
                    utils.log(`Вызываем изменение размера для iframe: ${iframeId}`);
                    window.iframeChartHandler.resizeIframeChart(iframeId);
                    
                    // Повторяем через небольшой промежуток для гарантии
                    setTimeout(() => {
                        window.iframeChartHandler.resizeIframeChart(iframeId);
                    }, 200);
                }
            });
        },
        
        // Закрытие модального окна
        closeModal: function(modal) {
            if (!modal) return;
            
            try {
                // Предотвращаем множественные операции с модальными окнами
                if (state.isProcessingModal) {
                    utils.log('Уже идет обработка модального окна, операция отложена', 'warn');
                    setTimeout(() => this.closeModal(modal), config.timeouts.modalTransition);
                    return;
                }
                
                state.isProcessingModal = true;
                
                // Закрываем через Bootstrap API, если доступно
                if (utils.hasBootstrap()) {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) {
                        bsModal.hide();
                    } else {
                        // Если экземпляр не получен, закрываем вручную
                        this.forceCloseModal(modal);
                    }
                } else {
                    // Ручное закрытие, если Bootstrap недоступен
                    this.forceCloseModal(modal);
                }
                
                // Удаляем из списка открытых модальных окон
                state.openModals.delete(modal);
                
                utils.log(`Модальное окно ${modal.id} закрыто успешно`);
            } catch (e) {
                utils.log(`Ошибка при закрытии модального окна: ${e.message}`, 'error');
            } finally {
                setTimeout(() => {
                    state.isProcessingModal = false;
                }, config.timeouts.modalTransition);
            }
        },
        
        // Принудительное закрытие модального окна
        forceCloseModal: function(modal) {
            if (!modal) return;
            
            // Скрываем модальное окно
            modal.style.display = 'none';
            modal.classList.remove('show');
            modal.setAttribute('aria-hidden', 'true');
            modal.removeAttribute('aria-modal');
            modal.removeAttribute('role');
            
            // Удаляем все backdrop элементы
            document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
                backdrop.remove();
            });
            
            // Проверяем, есть ли еще открытые модальные окна
            const hasOpenModals = state.openModals.size > 0;
            
            if (!hasOpenModals) {
                // Восстанавливаем состояние body
                this.restoreBodyState();
            }
            
            // Сбрасываем фокус
            if (document.activeElement && document.activeElement.blur) {
                document.activeElement.blur();
            }
        },
        
        // Восстановление состояния body после закрытия всех модальных окон
        restoreBodyState: function() {
            // Восстанавливаем стандартные стили и атрибуты body
            const body = document.body;
            
            body.classList.remove('modal-open');
            body.style.overflow = '';
            body.style.paddingRight = '';
            body.removeAttribute('data-bs-overflow');
            body.removeAttribute('data-bs-padding-right');
            body.removeAttribute('aria-hidden');
            
            // Сбрасываем inline-стили, которые могут блокировать интерфейс
            body.style.position = '';
            body.style.top = '';
            body.style.height = '';
        },
        
        // Обработчик события завершения скрытия модального окна
        onModalHidden: function(modal) {
            utils.log(`Событие hidden.bs.modal для ${modal.id}`);
            
            // Удаляем из списка открытых модальных окон
            state.openModals.delete(modal);
            
            // Проверяем наличие оставшихся backdrop элементов
            setTimeout(() => {
                const backdrops = document.querySelectorAll('.modal-backdrop');
                if (backdrops.length > 0) {
                    utils.log(`Обнаружены оставшиеся backdrop элементы (${backdrops.length}), удаляем...`);
                    backdrops.forEach(backdrop => backdrop.remove());
                }
                
                // Если нет открытых модальных окон, восстанавливаем состояние body
                if (state.openModals.size === 0) {
                    this.restoreBodyState();
                }
            }, config.timeouts.cleanupDelay);
        },
        
        // ========================
        // Наблюдатели и глобальные обработчики
        // ========================
        
        // Настройка MutationObserver для отслеживания динамически добавляемых элементов
        setupMutationObserver: function() {
            utils.log('Настройка MutationObserver');
            
            const observer = new MutationObserver(mutations => {
                let needsUpdate = false;
                
                mutations.forEach(mutation => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // Проверяем, добавлена ли карточка визуализации
                                if (node.matches(config.selectors.visualizationCard) || node.querySelector(config.selectors.visualizationCard)) {
                                    needsUpdate = true;
                                }
                            }
                        });
                    }
                });
                
                if (needsUpdate) {
                    utils.log('Обнаружены новые элементы визуализации, обновляем миниатюры');
                    this.generateAllThumbnails();
                }
            });
            
            // Начинаем наблюдение за контейнером визуализаций
            const container = document.querySelector('#visualizations-grid') || document.body;
            observer.observe(container, {
                childList: true,
                subtree: true
            });
            
            return observer;
        },
        
        // Настройка глобальных обработчиков
        setupGlobalHandlers: function() {
            utils.log('Настройка глобальных обработчиков');
            
            // Обработчик клавиши Escape
            utils.registerEventHandler(document, 'keydown', (e) => {
                if (e.key === 'Escape') {
                    // Найдем последнее открытое модальное окно
                    const modals = Array.from(state.openModals);
                    if (modals.length > 0) {
                        const lastModal = modals[modals.length - 1];
                        this.closeModal(lastModal);
                    }
                }
            });
            
            // Обработчик кликов по backdrop
            utils.registerEventHandler(document, 'click', (e) => {
                if (e.target.classList.contains('modal') && e.target.classList.contains('show')) {
                    const backdropCloseable = e.target.getAttribute('data-bs-backdrop') !== 'static';
                    if (backdropCloseable) {
                        this.closeModal(e.target);
                    }
                }
            });
            
            // Обработчик события resize окна
            utils.registerEventHandler(window, 'resize', () => {
                // Здесь можно добавить логику для адаптации модальных окон при изменении размера окна
            });
        }
    };
    
    // ========================
    // Вспомогательная функция для получения пути к миниатюре
    // ========================
    function getThumbnailPath(vizData) {
        if (!vizData || !vizData.path) {
            console.error('Недостаточно данных для получения пути к миниатюре');
            return 'img/placeholder.png'; // путь к запасному изображению
        }
        
        // Используем window.visualizationsBasePath, если он определен, или конфигурационный путь
        const basePath = window.visualizationsBasePath || config.paths.thumbnails;
        
        // Удаляем начальные слеши, если они есть
        const normalizedPath = vizData.path.replace(/^\/+/, '');
        
        // Строим полный путь к PNG файлу
        const pngPath = `${basePath}${normalizedPath.replace(/\.html$/, '.png')}`;
        
        console.log(`Путь к миниатюре: ${pngPath}`);
        return pngPath;
    }
    
    // ========================
    // Экспорт публичного API
    // ========================
    window.thumbnailManager = {
        // Инициализация менеджера
        init: function() {
            thumbnailManager.init();
        },
        
        // Создание миниатюр для всех карточек
        refreshAll: function() {
            thumbnailManager.generateAllThumbnails();
        },
        
        // Создание миниатюры для конкретной визуализации
        createThumbnail: function(vizId) {
            const vizData = window.visualizationManager.getVisualizationById(vizId);
            if (vizData) {
                const card = document.querySelector(`.visualization-card[data-viz-id="${vizId}"]`);
                if (card) {
                    thumbnailManager.generateThumbnail(card, vizData);
                }
            }
        },
        
        // Открытие визуализации в модальном окне
        openVisualization: function(vizId) {
            const vizData = window.visualizationManager.getVisualizationById(vizId);
            if (vizData) {
                thumbnailManager.openVisualizationModal(vizData);
            }
        },
        
        // Открытие визуализации в полноэкранном режиме
        openFullscreen: function(vizId) {
            const vizData = window.visualizationManager.getVisualizationById(vizId);
            if (vizData) {
                thumbnailManager.openFullscreenModal(vizData);
            }
        },
        
        // Закрытие всех модальных окон
        closeAll: function() {
            const modals = Array.from(state.openModals);
            modals.forEach(modal => {
                thumbnailManager.closeModal(modal);
            });
        }
    };
    
    // Автоинициализация при загрузке документа
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            thumbnailManager.init();
        });
    } else {
        thumbnailManager.init();
    }
})();