/**
 * Visualizations Manager
 * 
 * Отвечает за загрузку, отображение и управление визуализациями из внешних HTML-файлов.
 * Включает функционал ленивой загрузки, обработки ошибок, фильтрации и поиска.
 * 
 * @author 
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
    // Будет заполнен динамически
    const visualizations = [];

    // Функция для получения списка визуализаций
    async function loadVisualizations() {
        // Определение, работаем через file:// или http(s)
        const isLocalFile = window.location.protocol === 'file:';
        
        try {
            if (isLocalFile) {
                console.log('Обнаружен протокол file:// - используем статические данные');
                // В режиме file:// используем предопределенные визуализации
                
                // Заполняем массив визуализаций
                visualizations.length = 0;
                staticVizFiles.forEach((file, index) => {
                    const id = `viz_${index + 1}`;
                    const nameParts = file.replace('viz_', '').replace('.html', '').split('_');
                    const title = nameParts.map(part => part.charAt(0).toUpperCase() + part.slice(1)).join(' ');
                    
                    visualizations.push({
                        id: id,
                        title: title,
                        path: file,
                        type: index % 2 === 0 ? 'bar' : (index % 3 === 0 ? 'pie' : 'scatter'),
                        category: 'analysis'
                    });
                });
                
                console.log(`Загружено ${visualizations.length} статических визуализаций`);
                return visualizations;
            } else {
                // Для HTTP/HTTPS - запрос к директории
                const response = await fetch(window.visualizationsBasePath || '../analytics_output/visualizations/');
                if (!response.ok) {
                    throw new Error(`Ошибка загрузки списка визуализаций: ${response.status}`);
                }
                
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // Получаем все ссылки в директории
                const links = Array.from(doc.querySelectorAll('a'));
                
                // Фильтруем только файлы формата viz_*.html
                const vizRegex = /^viz_.*\.html$/;
                const vizFiles = links
                    .map(link => {
                        const href = link.getAttribute('href');
                        if (!href) return null;
                        
                        // Извлекаем только имя файла из пути для надежности
                        const fileName = href.split('/').pop();
                        return fileName && vizRegex.test(fileName) ? fileName : null;
                    })
                    .filter(Boolean); // Убираем null значения
                
                console.log(`Найдено ${vizFiles.length} файлов визуализаций`);
                
                // Очищаем текущий массив
                visualizations.length = 0;
                
                // Создаем объекты визуализаций на основе найденных файлов
                vizFiles.forEach((file, index) => {
                    const id = `viz_${index + 1}`;
                    const nameParts = file.replace('viz_', '').replace('.html', '').split('_');
                    const title = nameParts.map(part => part.charAt(0).toUpperCase() + part.slice(1)).join(' ');
                    
                    visualizations.push({
                        id: id,
                        title: title,
                        path: file,
                        type: detectChartTypeFromFileName(file),
                        category: 'analysis'
                    });
                });
                
                return visualizations;
            }
        } catch (error) {
            console.error('Ошибка при загрузке визуализаций:', error);
            console.log('Используем резервные статические визуализации');
            
            // Используем резервные статические данные в случае ошибки
            visualizations.length = 0;
            visualizations.push(...fallbackVisualizations);
            
            // Если fallbackVisualizations пуст, создадим минимальный набор
            if (visualizations.length === 0) {
                visualizations.push({
                    id: 'viz_demo',
                    title: 'Демонстрационная визуализация',
                    path: 'viz_demo.html',
                    type: 'bar',
                    category: 'analysis',
                    description: 'Пример визуализации для проверки функциональности'
                });
            }
            
            return visualizations;
        }
    }

    // Вспомогательная функция для определения типа диаграммы по имени файла
    function detectChartTypeFromFileName(fileName) {
        const lowerName = fileName.toLowerCase();
        if (lowerName.includes('raspredelenie') || lowerName.includes('chastota')) {
            return 'bar';
        } else if (lowerName.includes('vzaimosvyaz') || lowerName.includes('svyaz')) {
            return 'scatter';
        } else if (lowerName.includes('protsentnoe') || lowerName.includes('dolya')) {
            return 'pie';
        } else {
            return 'bar'; // По умолчанию
        }
    }

    // Резервные статические визуализации
    const fallbackVisualizations = [
        // Оставляем как запасной вариант
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
    async function init() {
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
        
        // Показываем индикатор загрузки
        if (elements.grid) {
            elements.grid.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Загружаем визуализации...</p></div>';
        }
        
        try {
            // Загружаем список визуализаций
            await loadVisualizations();
            
            // Сбор уникальных категорий и типов для фильтров
            state.categories.clear();
            state.types.clear();
            
            visualizations.forEach(viz => {
                if (viz.category) state.categories.add(viz.category);
                if (viz.type) state.types.add(viz.type);
            });
            
            // Заполнение селектов категорий и типов
            if (elements.categorySelect) {
                elements.categorySelect.innerHTML = '<option value="all">Все категории</option>';
                populateFilterOptions(elements.categorySelect, Array.from(state.categories));
            }
            
            if (elements.typeSelect) {
                elements.typeSelect.innerHTML = '<option value="all">Все типы</option>';
                populateFilterOptions(elements.typeSelect, Array.from(state.types));
            }
            
            // Настройка обработчиков событий для фильтров и поиска
            setupEventListeners(elements);
            
            // Первоначальное отображение визуализаций
            filterAndDisplayVisualizations(elements);
        } catch (error) {
            console.error('Ошибка при инициализации визуализаций:', error);
            
            if (elements.grid) {
                elements.grid.innerHTML = `
                    <div class="alert alert-danger text-center" role="alert">
                        <i class="bi bi-exclamation-triangle fs-4 mb-3"></i>
                        <p>Произошла ошибка при загрузке визуализаций.</p>
                        <button class="btn btn-outline-danger mt-2" onclick="init()">Повторить загрузку</button>
                    </div>
                `;
            }
        }
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
                
                // Даем время для обновления DOM, затем инициализируем миниатюры
                setTimeout(() => {
                    // Сначала скрываем все лоадеры для корректного отображения
                    document.querySelectorAll('.visualization-loader').forEach(loader => {
                        loader.style.display = 'none';
                    });
                    
                    // Последовательно пробуем разные способы инициализации миниатюр
                    if (typeof window.initStaticThumbnails === 'function') {
                        console.log('Переинициализация статических миниатюр после сброса фильтров');
                        window.initStaticThumbnails();
                    } else if (window.vizThumbnails && window.vizThumbnails.initThumbnails) {
                        console.log('Переинициализация миниатюр через vizThumbnails после сброса фильтров');
                        window.vizThumbnails.initThumbnails();
                    }
                }, 500); // Таймаут для гарантии завершения обновления DOM
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
        
        // Создаем контейнер для миниатюры
        const thumbnailContainer = document.createElement('div');
        thumbnailContainer.className = 'viz-thumbnail-container';
        thumbnailContainer.style.width = '100%';
        thumbnailContainer.style.height = '100%';
        thumbnailContainer.style.position = 'relative';
        content.appendChild(thumbnailContainer);
        
        // Загрузка изображения миниатюры
        const img = document.createElement('img');
        img.className = 'viz-thumbnail';
        img.alt = viz.title;
        img.style.width = '100%';
        img.style.height = 'auto';
        
        // Путь к PNG миниатюре
        const pngPath = `${config.visualizationsPath}${viz.path.replace(/\.html$/, '.png')}`;
        img.src = pngPath;
        
        // Исправленный обработчик ошибки загрузки изображения
        img.onerror = function() {
            console.error(`Не удалось загрузить миниатюру: ${pngPath}`);
            img.style.display = 'none';
            
            // Создаем заглушку с информативным сообщением
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
            
            // Кнопка повторной загрузки
            const retryBtn = document.createElement('button');
            retryBtn.textContent = 'Повторить';
            retryBtn.className = 'btn btn-sm btn-outline-primary mt-2';
            retryBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Повторная попытка загрузки
                errorContainer.style.display = 'none';
                loader.style.display = 'block';
                img.style.display = '';
                img.src = pngPath + '?retry=' + new Date().getTime(); // Добавляем параметр для обхода кэширования
            });
            errorContainer.appendChild(retryBtn);
            
            thumbnailContainer.appendChild(errorContainer);
        };
        
        // Добавляем изображение в контейнер
        thumbnailContainer.appendChild(img);
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
    function createPaginationItem(label, disabled, onClick, active = false) {
        const li = document.createElement('li');
        li.className = `page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}`;
        
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = label;
        if (!disabled) {
            a.addEventListener('click', (e) => {
                e.preventDefault();
                onClick();
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

    // Добавьте этот вспомогательный метод в объект utils или в начало функции createVisualizationCard
    function safeClassNameReplace(element, search, replacement) {
        if (!element) return;
        
        // Безопасная работа с className
        if (typeof element.className === 'string') {
            element.className = element.className.split(search).join(replacement);
        } else if (element.className && typeof element.className.baseVal === 'string') {
            // Для SVG элементов
            element.className.baseVal = element.className.baseVal.split(search).join(replacement);
        }
    }

    window.addEventListener('resize', debounce(() => {
        document.querySelectorAll('.visualization-iframe').forEach(iframe => {
            // Повторно запустить масштабирование для всех iframe при ресайзе
            if (window.iframeChartHandler && window.iframeChartHandler.resizeIframeChart) {
                window.iframeChartHandler.resizeIframeChart(iframe.id);
            }
        });
    }, 250));

    // Инициализация при загрузке DOM
    document.addEventListener('DOMContentLoaded', () => {
        init().catch(error => {
            console.error('Ошибка при инициализации:', error);
        });
    });

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

    console.log('visualizations.js загружен');
    console.log('Состояние visualizationManager:', window.visualizationManager);

    // Явно проверить создание объекта
    if (!window.visualizationManager) {
        console.error('visualizationManager не инициализирован!');
        
        // Экстренное создание минимальной версии
        window.visualizationManager = {
            getVisualizations: function() {
                console.warn('Используется аварийная версия visualizationManager');
                return [];
            }
        };
    }
})();