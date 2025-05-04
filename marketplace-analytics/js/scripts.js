// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Создаем глобальную переменную для базового пути визуализаций
    window.visualizationsBasePath = window.appConfig ? window.appConfig.paths.visualizations : '../analytics_output/visualizations/';

    // Initialize Navbar Scroll Effect
    initNavbarScroll();
    
    // Initialize Scroll Animation
    initScrollAnimation();
    
    // Initialize Back to Top Button
    initBackToTop();
    
    // Initialize Charts
    initCharts();
    
    // Проверка и сброс возможных проблем с модальными окнами
    function resetModalState() {
        // Проверка на наличие "застрявших" backdrop элементов
        const backdrops = document.querySelectorAll('.modal-backdrop');
        if (backdrops.length > 0) {
            console.warn('Обнаружены оставшиеся backdrop элементы:', backdrops.length);
            backdrops.forEach(backdrop => backdrop.remove());
        }
        
        // Сброс стилей body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        document.body.removeAttribute('data-bs-overflow');
        document.body.removeAttribute('data-bs-padding-right');
        document.body.removeAttribute('aria-hidden');
    }

    // Вызываем сброс состояния при загрузке страницы
    resetModalState();

    // Создаем запасной visualizationManager для обеспечения минимальной работоспособности
    function ensureVisualizationManager() {
        if (!window.visualizationManager) {
            console.log('visualizationManager не найден, создаем базовую версию...');
            window.visualizationManager = {
                _visualizations: [{
                    id: 'viz_chastota',
                    title: 'Частота упоминаний достоинств и их связь с рейтингом',
                    path: 'viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
                    type: 'bar',
                    category: 'analysis'
                }],
                getVisualizations: function() {
                    return this._visualizations;
                },
                getVisualizationById: function(id) {
                    return this._visualizations.find(v => v.id === id);
                },
                openVisualization: function(vizId) {
                    console.log('Открытие визуализации:', vizId);
                    const viz = this.getVisualizationById(vizId);
                    if (viz && window.thumbnailManager) {
                        window.thumbnailManager.openVisualization(vizId);
                    }
                }
            };
        }
        
        return window.visualizationManager;
    }

    // Вызываем функцию ensureVisualizationManager сразу после resetModalState()
    ensureVisualizationManager();
});

// Navbar becomes different on scroll
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled', 'bg-white');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
}

// Add scroll animations to elements
function initScrollAnimation() {
    const elements = document.querySelectorAll('.fade-in');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, {
        threshold: 0.1
    });
    
    elements.forEach(element => {
        observer.observe(element);
    });
}

// Initialize Back to Top button
function initBackToTop() {
    const backToTopButton = document.getElementById('back-to-top');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });
    
    backToTopButton.addEventListener('click', function(e) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Initialize Charts with Plotly.js
function initCharts() {
    // Chart 1: Line Chart - Sales Dynamics
    const lineChart = document.getElementById('chart-1');
    if (lineChart) {
        const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь'];
        const sales = [120, 170, 160, 190, 230, 280];
        
        const trace1 = {
            x: months,
            y: sales,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Продажи',
            line: {
                color: '#4361ee',
                width: 3
            },
            marker: {
                size: 8,
                color: '#4361ee'
            }
        };
        
        const layout1 = {
            title: {
                text: 'Динамика продаж по месяцам',
                font: {
                    size: 18,
                    family: 'Inter, sans-serif'
                }
            },
            autosize: true,
            margin: {
                l: 40,
                r: 40,
                b: 60,
                t: 80
            },
            xaxis: {
                title: 'Месяц'
            },
            yaxis: {
                title: 'Объем продаж (тыс. руб.)'
            },
            hovermode: 'closest',
            responsive: true
        };
        
        Plotly.newPlot(lineChart, [trace1], layout1, {responsive: true});
    }
    
    // Chart 2: Pie Chart - Category Distribution
    const pieChart = document.getElementById('chart-2');
    if (pieChart) {
        const categories = ['Электроника', 'Одежда', 'Дом и сад', 'Красота', 'Другое'];
        const values = [30, 25, 20, 15, 10];
        
        const trace2 = {
            labels: categories,
            values: values,
            type: 'pie',
            marker: {
                colors: ['#4361ee', '#3a0ca3', '#4cc9f0', '#7209b7', '#f72585']
            },
            textinfo: 'percent',
            insidetextorientation: 'radial'
        };
        
        const layout2 = {
            title: {
                text: 'Распределение категорий',
                font: {
                    size: 18,
                    family: 'Inter, sans-serif'
                }
            },
            height: 350,
            margin: {
                l: 40,
                r: 40,
                b: 40,
                t: 80
            },
            showlegend: true,
            responsive: true
        };
        
        Plotly.newPlot(pieChart, [trace2], layout2, {responsive: true});
    }
    
    // Chart 3: Bar Chart - Marketplace Comparison
    const barChart = document.getElementById('chart-3');
    if (barChart) {
        const marketplaces = ['Wildberries', 'Ozon', 'Яндекс Маркет', 'СберМегаМаркет', 'AliExpress'];
        const revenue = [350, 270, 190, 160, 120];
        const orders = [420, 310, 240, 180, 150];
        
        const trace3a = {
            x: marketplaces,
            y: revenue,
            name: 'Выручка (тыс. руб.)',
            type: 'bar',
            marker: {
                color: '#4361ee'
            }
        };
        
        const trace3b = {
            x: marketplaces,
            y: orders,
            name: 'Количество заказов',
            type: 'bar',
            marker: {
                color: '#4cc9f0'
            }
        };
        
        const layout3 = {
            title: {
                text: 'Сравнение показателей по маркетплейсам',
                font: {
                    size: 18,
                    family: 'Inter, sans-serif'
                }
            },
            barmode: 'group',
            xaxis: {
                title: 'Маркетплейс'
            },
            yaxis: {
                title: 'Значение'
            },
            margin: {
                l: 50,
                r: 50,
                b: 60,
                t: 80
            },
            legend: {
                x: 1,
                xanchor: 'right',
                y: 1
            },
            responsive: true
        };
        
        Plotly.newPlot(barChart, [trace3a, trace3b], layout3, {responsive: true});
    }
}

// Модифицируем часть инициализации визуализаций
function initVisualizationSystem() {
    console.log('Запуск инициализации системы визуализаций...');
    
    // Проверка наличия необходимых элементов DOM
    const vizGrid = document.getElementById('visualizations-grid');
    if (!vizGrid) {
        console.error('Элемент #visualizations-grid не найден в DOM');
        return;
    }
    
    // Базовый путь к визуализациям - проверяем и устанавливаем явно
    if (!window.visualizationsBasePath) {
        window.visualizationsBasePath = '../analytics_output/visualizations/';
        console.log(`Установлен базовый путь к визуализациям: ${window.visualizationsBasePath}`);
    }
    
    // Создаем объект visualizationManager, если он не существует
    if (!window.visualizationManager) {
        console.log('Создание объекта visualizationManager...');
        
        window.visualizationManager = {
            // Базовая реализация необходимых методов
            init: function() {
                console.log('Инициализация visualizationManager...');
                this.loadVisualizations();
            },
            getVisualizations: function() {
                return this._visualizations || [];
            },
            _visualizations: [],
            loadVisualizations: function() {
                // Проверим доступность директории с визуализациями
                this._testVisDirectoryAccess()
                    .then(() => this._loadVisualizationList())
                    .catch(error => {
                        console.error('Ошибка при загрузке визуализаций:', error);
                        
                        // Загрузить тестовые данные, если основной способ не работает
                        console.log('Загрузка тестовых данных визуализаций...');
                        
                        // Упрощенная версия для демонстрации
                        this._visualizations = [
                            {
                                id: 'viz_chastota',
                                title: 'Частота упоминаний достоинств и их связь с рейтингом',
                                path: 'viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
                                type: 'bar',
                                category: 'analysis'
                            },
                            {
                                id: 'viz_raspredelenie',
                                title: 'Распределение рейтингов отзывов',
                                path: 'viz_Raspredelenie_reytingov_otzyvov.html',
                                type: 'pie',
                                category: 'analysis'
                            },
                            {
                                id: 'viz_vzaimosvyaz',
                                title: 'Взаимосвязь комплектации и рейтинга',
                                path: 'viz_Vzaimosvyaz_komplektatsii.html',
                                type: 'scatter',
                                category: 'analysis'
                            }
                        ];
                        
                        console.log(`Загружено ${this._visualizations.length} визуализаций`);
                        
                        // Заполнить фильтры и отобразить визуализации
                        this._setupFiltersAndDisplay();
                    });
            },
            
            // Проверка доступности директории с визуализациями
            _testVisDirectoryAccess: function() {
                return new Promise((resolve, reject) => {
                    // Список возможных путей для проверки
                    const paths = [
                        '../analytics_output/visualizations/',
                        './analytics_output/visualizations/',
                        '/analytics_output/visualizations/',
                        '../../analytics_output/visualizations/'
                    ];
                    
                    const tryPath = (index) => {
                        if (index >= paths.length) {
                            reject(new Error('Не удалось получить доступ к директории визуализаций'));
                            return;
                        }
                        
                        fetch(paths[index])
                            .then(response => {
                                if (response.ok) {
                                    window.visualizationsBasePath = paths[index];
                                    console.log(`Найден работающий путь: ${paths[index]}`);
                                    resolve(response);
                                } else {
                                    tryPath(index + 1);
                                }
                            })
                            .catch(() => tryPath(index + 1));
                    };
                    
                    tryPath(0);
                });
            },
            
            // Загрузка списка визуализаций
            _loadVisualizationList: function() {
                return new Promise((resolve, reject) => {
                    // Используем улучшенную функцию из visualizations.js
                    loadVisualizations()
                        .then(visualizations => {
                            this._visualizations = visualizations;
                            this._setupFiltersAndDisplay();
                            resolve(visualizations);
                        })
                        .catch(reject);
                });
            },
            
            // Настройка фильтров и отображение визуализаций
            _setupFiltersAndDisplay: function() {
                // Получаем элементы интерфейса
                const elements = {};
                Object.entries(config.selectors).forEach(([key, selector]) => {
                    elements[key] = document.querySelector(selector);
                });
                
                // Собираем уникальные категории и типы
                this._visualizations.forEach(viz => {
                    if (viz.category) state.categories.add(viz.category);
                    if (viz.type) state.types.add(viz.type);
                });
                
                // Заполняем опции фильтров, если они есть
                if (elements.categorySelect) {
                    populateFilterOptions(elements.categorySelect, Array.from(state.categories));
                }
                if (elements.typeSelect) {
                    populateFilterOptions(elements.typeSelect, Array.from(state.types));
                }
                
                // Настройка обработчиков событий
                setupEventListeners(elements);
                
                // Фильтрация и отображение визуализаций
                filterAndDisplayVisualizations(elements);
                
                // Инициализация миниатюр
                if (window.thumbnailManager) {
                    window.thumbnailManager.init();
                }
            },
            
            // Получение визуализации по ID
            getVisualizationById: function(id) {
                return this._visualizations.find(v => v.id === id);
            },
            
            // Открытие визуализации
            openVisualization: function(vizId) {
                console.log(`Открытие визуализации: ${vizId}`);
                
                const viz = this.getVisualizationById(vizId);
                if (!viz) {
                    console.error(`Визуализация с ID ${vizId} не найдена`);
                    return;
                }
                
                // Если используем thumbnailManager, делегируем ему открытие
                if (window.thumbnailManager && window.thumbnailManager.openVisualization) {
                    window.thumbnailManager.openVisualization(vizId);
                } else {
                    // Запасной вариант
                    const elements = {};
                    Object.entries(config.selectors).forEach(([key, selector]) => {
                        elements[key] = document.querySelector(selector);
                    });
                    
                    loadVisualization(document.querySelector(`[data-viz-id="${vizId}"]`), viz, elements);
                }
            }
        };
    }
    
    // Вызываем инициализацию после создания объекта
    if (window.visualizationManager && typeof window.visualizationManager.init === 'function') {
        window.visualizationManager.init();
    }
}

// Запускаем инициализацию с небольшой задержкой
setTimeout(initVisualizationSystem, 300);