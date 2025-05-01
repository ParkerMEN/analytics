/**
 * Visualizations Manager
 * 
 * Отвечает за загрузку, отображение и управление визуализациями из внешних HTML-файлов.
 * Включает функционал ленивой загрузки, обработки ошибок, фильтрации и поиска.
 * 
 * @author MarketAnalytics Team
 * @version 1.1.0
 */

(function() {
    'use strict';
    
    // ========================
    // Конфигурация
    // ========================
    const config = {
        // Путь к директории с визуализациями
        visualizationsPath: '../analytics_output/visualizations/',
        
        // Количество визуализаций на странице при пагинации
        itemsPerPage: 15, // Увеличиваем количество элементов на странице
        
        // Задержка перед показом визуализации (мс)
        loadDelay: 200, // Уменьшаем задержку для более быстрой загрузки
        
        // Таймаут загрузки iframe (мс)
        iframeTimeout: 8000,
        
        // CSS селекторы
        selectors: {
            grid: '#visualizations-grid',
            pagination: '#viz-pagination',
            noResults: '#no-visualizations',
            search: '#viz-search',
            categorySelect: '#viz-category',
            typeSelect: '#viz-type',
            filterToggle: '#viz-filter-toggle',
            filtersPanel: '#viz-filters',
            resetFilters: '#reset-filters',
            fullscreenModal: '#vizFullscreenModal',
            fullscreenContainer: '#fullscreen-viz-container'
        },
        
        // Классы для динамического создания элементов
        classes: {
            card: 'card visualization-card shadow-sm mb-2',
            header: 'card-header bg-white py-2',
            title: 'card-title fs-6 mb-0',
            content: 'visualization-content',
            iframe: 'visualization-iframe',
            fallback: 'visualization-fallback',
            loader: 'visualization-loader',
            spinner: 'visualization-spinner',
            footer: 'card-footer bg-white py-2 text-muted small',
            fullscreenBtn: 'viz-fullscreen-btn'
        }
    };
    
    // ========================
    // Массив визуализаций
    // ========================
    // Пути к файлам визуализаций
    const visualizations = [
        {
            id: 'raspredelenie-reytingov',
            title: 'Распределение рейтингов отзывов',
            path: 'viz_Raspredelenie_reytingov_otzyvov__ves_korpus_.html',
            category: 'ratings',
            type: 'bar',
            description: 'Распределение рейтингов по всему корпусу отзывов'
        },
        {
            id: 'chastota-upominaniy-dostoinstv',
            title: 'Частота упоминаний достоинств',
            path: 'viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
            category: 'mentions',
            type: 'bar',
            description: 'Частота упоминаний достоинств и их связь с рейтингом'
        },
        {
            id: 'chastota-upominaniy-problem',
            title: 'Частота упоминаний проблем с аккумулятором',
            path: 'viz_Chastota_upominaniy_problem_s_akkumulyatorom_i_ikh_vliyanie_na_reyting.html',
            category: 'problems',
            type: 'bar',
            description: 'Анализ частоты упоминаний проблем с аккумулятором'
        },
        {
            id: 'protsent-raspredeleniya',
            title: 'Распределение типов отзывов',
            path: 'viz_Protsentnoe_raspredelenie_polozhitelnykh__neytralnykh_i_otritsatelnykh_otzyvov.html',
            category: 'distribution',
            type: 'pie',
            description: 'Процентное распределение положительных, нейтральных и отрицательных отзывов'
        },
        {
            id: 'trend-upominaniy',
            title: 'Тренд упоминаний доставки',
            path: 'viz_Trend_upominaniy_bystroy_dostavki_i_ikh_svyaz_s_reytingom.html',
            category: 'trends',
            type: 'line',
            description: 'Тренд упоминаний быстрой доставки и их связь с рейтингом'
        },
        {
            id: 'vliyanie-konkretnykh-problem',
            title: 'Влияние конкретных проблем',
            path: 'viz_Vliyanie_konkretnykh_problem_na_sredniy_reyting.html',
            category: 'problems',
            type: 'bar',
            description: 'Влияние конкретных проблем на средний рейтинг отзывов'
        },
        {
            id: 'vzaimosvyaz-legkosti-sborki',
            title: 'Взаимосвязь легкости сборки и рейтинга',
            path: 'viz_Vzaimosvyaz_legkosti_sborki_i_reytinga.html',
            category: 'correlations',
            type: 'scatter',
            description: 'Анализ связи между легкостью сборки и рейтингом продукта'
        },
        {
            id: 'vzaimosvyaz-rekomendatsiy',
            title: 'Взаимосвязь рекомендаций и рейтинга',
            path: 'viz_Vzaimosvyaz_rekomendatsiy_polzovateley_i_reytinga.html',
            category: 'correlations',
            type: 'scatter',
            description: 'Влияние рекомендаций пользователей на рейтинг'
        },
        {
            id: 'vzaimosvyaz-komplektatsii',
            title: 'Взаимосвязь комплектации и рейтинга',
            path: 'viz_Vzaimosvyaz_upominaniya_komplektatsii_i_reytinga.html',
            category: 'correlations',
            type: 'scatter',
            description: 'Анализ влияния комплектации на рейтинг отзывов'
        },
        {
            id: 'chastota-upominaniy-vesa',
            title: 'Частота упоминаний веса',
            path: 'viz_Chastota_upominaniy_i_vliyanie_legkosti_vesa_na_reyting.html',
            category: 'mentions',
            type: 'bar',
            description: 'Частота упоминаний и влияние легкости веса на рейтинг'
        }
        // Можно добавить другие визуализации, следуя тому же формату
    ];
    
    // ========================
    // Состояние приложения
    // ========================
    const state = {
        currentPage: 1,
        totalPages: 1,
        filter: {
            search: '',
            category: 'all',
            type: 'all'
        },
        filteredVisualizations: [],
        categories: new Set(),
        types: new Set(),
        bootstrap: null // Для хранения объекта bootstrap
    };
    
    // ========================
    // Инициализация
    // ========================
    function init() {
        // Получение DOM-элементов
        const elements = {};
        Object.entries(config.selectors).forEach(([key, selector]) => {
            elements[key] = document.querySelector(selector);
        });
        
        // Если элементы не найдены, выходим
        if (!elements.grid) {
            console.error('Не удалось найти контейнер для визуализаций');
            return;
        }
        
        // Инициализируем Bootstrap для модальных окон
        if (typeof bootstrap !== 'undefined') {
            state.bootstrap = bootstrap;
        }
        
        // Сбор уникальных категорий и типов для фильтров
        visualizations.forEach(viz => {
            if (viz.category) state.categories.add(viz.category);
            if (viz.type) state.types.add(viz.type);
        });
        
        // Заполнение селектов категорий и типов
        populateFilterOptions(elements.categorySelect, Array.from(state.categories));
        populateFilterOptions(elements.typeSelect, Array.from(state.types));
        
        // Настройка обработчиков событий для фильтров и поиска
        setupEventListeners(elements);
        
        // Первоначальное отображение визуализаций
        filterAndDisplayVisualizations(elements);
    }
    
    // ========================
    // Заполнение опций фильтров
    // ========================
    function populateFilterOptions(selectElement, options) {
        if (!selectElement) return;
        
        // Форматирование названия для удобочитаемого текста
        const formatName = (name) => {
            return name
                .split('-')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
        };
        
        options.sort().forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = formatName(option);
            selectElement.appendChild(optionElement);
        });
    }
    
    // ========================
    // Настройка обработчиков событий
    // ========================
    function setupEventListeners(elements) {
        // Поиск
        if (elements.search) {
            elements.search.addEventListener('input', debounce(() => {
                state.filter.search = elements.search.value.toLowerCase().trim();
                state.currentPage = 1;
                filterAndDisplayVisualizations(elements);
            }, 300));
        }
        
        // Фильтр по категории
        if (elements.categorySelect) {
            elements.categorySelect.addEventListener('change', () => {
                state.filter.category = elements.categorySelect.value;
                state.currentPage = 1;
                filterAndDisplayVisualizations(elements);
            });
        }
        
        // Фильтр по типу
        if (elements.typeSelect) {
            elements.typeSelect.addEventListener('change', () => {
                state.filter.type = elements.typeSelect.value;
                state.currentPage = 1;
                filterAndDisplayVisualizations(elements);
            });
        }
        
        // Переключение видимости панели фильтров
        if (elements.filterToggle && elements.filtersPanel) {
            elements.filterToggle.addEventListener('click', () => {
                const isVisible = elements.filtersPanel.style.display !== 'none';
                elements.filtersPanel.style.display = isVisible ? 'none' : 'block';
                elements.filterToggle.innerHTML = isVisible ? 
                    '<i class="bi bi-funnel"></i> Фильтры' : 
                    '<i class="bi bi-funnel-fill"></i> Скрыть фильтры';
            });
        }
        
        // Сброс фильтров
        if (elements.resetFilters) {
            elements.resetFilters.addEventListener('click', () => {
                if (elements.search) elements.search.value = '';
                if (elements.categorySelect) elements.categorySelect.value = 'all';
                if (elements.typeSelect) elements.typeSelect.value = 'all';
                
                state.filter = { search: '', category: 'all', type: 'all' };
                state.currentPage = 1;
                filterAndDisplayVisualizations(elements);
            });
        }
    }
    
    // ========================
    // Фильтрация и отображение визуализаций
    // ========================
    function filterAndDisplayVisualizations(elements) {
        // Фильтрация визуализаций
        state.filteredVisualizations = visualizations.filter(viz => {
            // Поиск по текстовому запросу
            const matchesSearch = state.filter.search === '' || 
                viz.title.toLowerCase().includes(state.filter.search) || 
                (viz.description && viz.description.toLowerCase().includes(state.filter.search));
            
            // Фильтр по категории
            const matchesCategory = state.filter.category === 'all' || 
                viz.category === state.filter.category;
            
            // Фильтр по типу
            const matchesType = state.filter.type === 'all' || 
                viz.type === state.filter.type;
            
            return matchesSearch && matchesCategory && matchesType;
        });
        
        // Расчет пагинации
        state.totalPages = Math.ceil(state.filteredVisualizations.length / config.itemsPerPage);
        if (state.currentPage > state.totalPages) state.currentPage = 1;
        
        // Отображение визуализаций текущей страницы
        displayVisualizations(elements);
        
        // Создание пагинации
        if (state.totalPages > 1) {
            createPagination(elements);
        } else if (elements.pagination) {
            elements.pagination.innerHTML = '';
        }
        
        // Отображение сообщения, если визуализации не найдены
        if (elements.noResults) {
            elements.noResults.style.display = 
                state.filteredVisualizations.length === 0 ? 'block' : 'none';
        }
    }
    
    // ========================
    // Отображение визуализаций
    // ========================
    function displayVisualizations(elements) {
        // Очистка контейнера
        elements.grid.innerHTML = '';
        
        // Вычисление границ для текущей страницы
        const start = (state.currentPage - 1) * config.itemsPerPage;
        const end = Math.min(start + config.itemsPerPage, state.filteredVisualizations.length);
        
        // Отображение визуализаций для текущей страницы
        const pageVisualizations = state.filteredVisualizations.slice(start, end);
        
        pageVisualizations.forEach((viz, index) => {
            // Создание карточки для визуализации
            const vizCard = createVisualizationCard(viz, index);
            elements.grid.appendChild(vizCard);
            
            // Отложенная загрузка iframe для улучшения производительности
            setTimeout(() => {
                loadVisualization(vizCard, viz, elements);
            }, config.loadDelay * (index + 1));
        });
    }
    
    // ========================
    // Создание карточки визуализации
    // ========================
    function createVisualizationCard(viz, index) {
        const { classes } = config;
        
        // Создание карточки
        const card = document.createElement('div');
        card.className = classes.card;
        card.id = `viz-card-${viz.id}`;
        card.dataset.vizId = viz.id;
        card.style.transitionDelay = `${index * 0.1}s`;
        
        // Заголовок
        const header = document.createElement('div');
        header.className = classes.header;
        
        const title = document.createElement('h5');
        title.className = classes.title;
        title.textContent = viz.title;
        header.appendChild(title);
        
        // Контейнер для контента
        const content = document.createElement('div');
        content.className = classes.content;
        
        // Индикатор загрузки
        const loader = document.createElement('div');
        loader.className = classes.loader;
        loader.innerHTML = `<div class="${classes.spinner}"></div>`;
        content.appendChild(loader);
        
        // Fallback на случай ошибки загрузки
        const fallback = document.createElement('div');
        fallback.className = classes.fallback;
        fallback.style.display = 'none';
        fallback.innerHTML = `
            <div>
                <i class="bi bi-exclamation-triangle fs-2 text-warning mb-2"></i>
                <p>Не удалось загрузить визуализацию</p>
                <button class="btn btn-sm btn-outline-primary retry-btn">Повторить</button>
            </div>
        `;
        content.appendChild(fallback);
        
        // Нижний колонтитул с дополнительной информацией
        const footer = document.createElement('div');
        footer.className = classes.footer;
        footer.innerHTML = viz.description || 'Описание будет добавлено позже';
        
        // Сборка карточки
        card.appendChild(header);
        card.appendChild(content);
        card.appendChild(footer);
        
        return card;
    }
    
    // ========================
    // Загрузка визуализации
    // ========================
    function loadVisualization(card, viz, elements) {
        const content = card.querySelector(`.${config.classes.content}`);
        const loader = content.querySelector(`.${config.classes.loader}`);
        const fallback = content.querySelector(`.${config.classes.fallback}`);
        
        if (!content || !loader || !fallback) return;
        
        // Создание миниатюры для предпросмотра
        const thumbnailContainer = document.createElement('div');
        thumbnailContainer.className = 'viz-thumbnail-container';
        thumbnailContainer.style.width = '100%';
        thumbnailContainer.style.height = '100%';
        thumbnailContainer.style.position = 'relative';
        content.appendChild(thumbnailContainer);
        
        // Если доступна функция создания миниатюры, используем её
        if (window.vizThumbnails && window.vizThumbnails.createThumbnail) {
            window.vizThumbnails.createThumbnail(viz.id, viz.path, thumbnailContainer);
            loader.style.display = 'none';
        }
        
        // Добавляем кнопку полноэкранного режима
        const fullscreenBtn = document.createElement('button');
        fullscreenBtn.className = config.classes.fullscreenBtn;
        fullscreenBtn.innerHTML = '<i class="bi bi-arrows-fullscreen"></i>';
        fullscreenBtn.title = 'Открыть визуализацию';
        content.appendChild(fullscreenBtn);
        
        // Делаем всю карточку кликабельной для открытия визуализации
        card.style.cursor = 'pointer';
        card.addEventListener('click', function(event) {
            // Предотвращаем открытие при клике на кнопки и другие интерактивные элементы
            if (event.target.closest('.retry-btn')) return;
            
            // Открываем модальное окно с визуализацией
            openVisualizationModal(viz);
        });
        
        // Функция открытия модального окна с визуализацией
        function openVisualizationModal(viz) {
            const modal = document.getElementById('vizModal') || createVizModal();
            if (!modal) return;
            
            // Устанавливаем заголовок модального окна
            const modalTitle = modal.querySelector('.modal-title');
            if (modalTitle) modalTitle.textContent = viz.title;
            
            // Очищаем и заполняем контейнер визуализации
            const modalContainer = document.getElementById('viz-container');
            if (modalContainer) {
                modalContainer.innerHTML = '';
                
                // Добавляем лоадер
                const modalLoader = document.createElement('div');
                modalLoader.className = config.classes.loader;
                modalLoader.innerHTML = `<div class="${config.classes.spinner}"></div>`;
                modalContainer.appendChild(modalLoader);
                
                // Создаем iframe для загрузки визуализации
                const modalIframe = document.createElement('iframe');
                modalIframe.className = 'viz-modal-iframe';
                modalIframe.style.width = '100%';
                modalIframe.style.height = '100%';
                modalIframe.style.border = 'none';
                modalIframe.style.opacity = '0';
                modalIframe.style.transition = 'opacity 0.3s';
                modalIframe.src = config.visualizationsPath + viz.path;
                modalContainer.appendChild(modalIframe);
                
                // Обработчик загрузки iframe
                modalIframe.onload = function() {
                    modalLoader.style.display = 'none';
                    modalIframe.style.opacity = '1';
                    
                    // Отправляем сообщение для адаптации размеров
                    try {
                        const message = {
                            type: 'resize-plotly',
                            width: modalContainer.clientWidth,
                            height: modalContainer.clientHeight
                        };
                        modalIframe.contentWindow.postMessage(message, '*');
                    } catch (e) {
                        console.error('Ошибка при отправке сообщения в iframe:', e);
                    }
                };
            }
            
            // Показываем модальное окно
            if (window.bootstrap && window.bootstrap.Modal) {
                const bsModal = new window.bootstrap.Modal(modal);
                bsModal.show();
            } else {
                modal.style.display = 'block';
            }
        }
        
        // Функция создания модального окна для визуализации
        function createVizModal() {
            // Проверяем, существует ли модальное окно
            let modal = document.getElementById('vizModal');
            if (modal) return modal;
            
            // Создаем новое модальное окно
            modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'vizModal';
            modal.setAttribute('tabindex', '-1');
            modal.setAttribute('aria-hidden', 'true');
            
            // Создаем структуру модального окна
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Визуализация</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-0">
                            <div id="viz-container" style="height: 500px; position: relative;"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Закрыть</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Добавляем модальное окно в документ
            document.body.appendChild(modal);
            
            return modal;
        }
    }
    
    // ========================
    // Создание пагинации
    // ========================
    function createPagination(elements) {
        if (!elements.pagination) return;
        
        elements.pagination.innerHTML = '';
        
        // Создание навигации пагинации
        const nav = document.createElement('nav');
        nav.setAttribute('aria-label', 'Навигация по визуализациям');
        
        const ul = document.createElement('ul');
        ul.className = 'pagination';
        
        // Кнопка "Предыдущая"
        const prevDisabled = state.currentPage === 1;
        ul.appendChild(createPaginationItem('Назад', prevDisabled, () => {
            state.currentPage--;
            filterAndDisplayVisualizations(elements);
        }));
        
        // Страницы
        const startPage = Math.max(1, state.currentPage - 2);
        const endPage = Math.min(state.totalPages, state.currentPage + 2);
        
        // Первая страница
        if (startPage > 1) {
            ul.appendChild(createPaginationItem('1', false, () => {
                state.currentPage = 1;
                filterAndDisplayVisualizations(elements);
            }));
            
            if (startPage > 2) {
                const ellipsis = createPaginationItem('...', true);
                ellipsis.className = 'page-item disabled';
                ul.appendChild(ellipsis);
            }
        }
        
        // Номера страниц
        for (let i = startPage; i <= endPage; i++) {
            const active = i === state.currentPage;
            ul.appendChild(createPaginationItem(i.toString(), false, () => {
                state.currentPage = i;
                filterAndDisplayVisualizations(elements);
            }, active));
        }
        
        // Последняя страница
        if (endPage < state.totalPages) {
            if (endPage < state.totalPages - 1) {
                const ellipsis = createPaginationItem('...', true);
                ellipsis.className = 'page-item disabled';
                ul.appendChild(ellipsis);
            }
            
            ul.appendChild(createPaginationItem(state.totalPages.toString(), false, () => {
                state.currentPage = state.totalPages;
                filterAndDisplayVisualizations(elements);
            }));
        }
        
        // Кнопка "Следующая"
        const nextDisabled = state.currentPage === state.totalPages;
        ul.appendChild(createPaginationItem('Вперед', nextDisabled, () => {
            state.currentPage++;
            filterAndDisplayVisualizations(elements);
        }));
        
        nav.appendChild(ul);
        elements.pagination.appendChild(nav);
    }
    
    // ========================
    // Создание элемента пагинации
    // ========================
    function createPaginationItem(text, disabled, onClick, active = false) {
        const li = document.createElement('li');
        li.className = `page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}`;
        
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#visualizations';
        a.innerText = text;
        
        if (!disabled && onClick) {
            a.addEventListener('click', function(e) {
                e.preventDefault();
                onClick();
                
                // Плавная прокрутка к началу раздела визуализаций
                document.getElementById('visualizations').scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            });
        }
        
        li.appendChild(a);
        return li;
    }
    
    // ========================
    // Утилиты
    // ========================
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Добавить в visualizations.js
    window.addEventListener('resize', debounce(() => {
        document.querySelectorAll('.visualization-iframe').forEach(iframe => {
            // Повторно запустить масштабирование для всех iframe при ресайзе
            adjustIframeScale(iframe);
        });
    }, 250));

    // Инициализация при загрузке DOM
    document.addEventListener('DOMContentLoaded', init);

    // ========================
    // Внешний API для работы с визуализациями
    // ========================
    window.visualizationManager = {
        // Получение списка всех визуализаций
        getVisualizations: function() {
            return visualizations;
        },
        
        // Получение визуализации по ID
        getVisualizationById: function(id) {
            return visualizations.find(v => v.id === id);
        },
        
        // Открытие визуализации в модальном окне
        openVisualization: function(vizId) {
            const viz = this.getVisualizationById(vizId);
            if (viz) {
                const card = document.querySelector(`.visualization-card[data-viz-id="${vizId}"]`);
                const elements = {};
                Object.entries(config.selectors).forEach(([key, selector]) => {
                    elements[key] = document.querySelector(selector);
                });
                
                loadVisualization(card, viz, elements);
                
                // Искусственно вызываем клик для открытия модального окна
                card.click();
            }
        },
        
        // Фильтрация визуализаций
        filterVisualizations: function(criteria) {
            if (typeof criteria === 'object') {
                if (criteria.search) state.filter.search = criteria.search.toLowerCase();
                if (criteria.category) state.filter.category = criteria.category;
                if (criteria.type) state.filter.type = criteria.type;
                
                const elements = {};
                Object.entries(config.selectors).forEach(([key, selector]) => {
                    elements[key] = document.querySelector(selector);
                });
                
                filterAndDisplayVisualizations(elements);
            }
        }
    };
})();