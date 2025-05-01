// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Navbar Scroll Effect
    initNavbarScroll();
    
    // Initialize Scroll Animation
    initScrollAnimation();
    
    // Initialize Back to Top Button
    initBackToTop();
    
    // Initialize Charts
    initCharts();
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