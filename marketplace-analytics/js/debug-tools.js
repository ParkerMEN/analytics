(function() {
    'use strict';
    
    window.debugVisualizations = {
        // Проверяет доступность файлов визуализаций
        checkFiles: function() {
            console.log('Проверка доступности файлов визуализаций...');
            
            if (window.visualizationManager && window.visualizationManager.getVisualizations) {
                const visualizations = window.visualizationManager.getVisualizations();
                const results = [];
                
                visualizations.forEach(viz => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('HEAD', '../analytics_output/visualizations/' + viz.path, false);
                    try {
                        xhr.send();
                        const status = xhr.status;
                        results.push({
                            id: viz.id,
                            path: viz.path,
                            status: status,
                            ok: status >= 200 && status < 300
                        });
                    } catch (e) {
                        results.push({
                            id: viz.id,
                            path: viz.path,
                            error: e.message,
                            ok: false
                        });
                    }
                });
                
                console.table(results);
                return results;
            } else {
                console.error('visualizationManager не доступен');
                return null;
            }
        },
        
        // Анализирует содержимое HTML файлов визуализаций
        analyzeHTML: function(vizPath) {
            console.log(`Анализ содержимого файла ${vizPath}...`);
            
            const xhr = new XMLHttpRequest();
            xhr.open('GET', '../analytics_output/visualizations/' + vizPath, false);
            try {
                xhr.send();
                if (xhr.status >= 200 && xhr.status < 300) {
                    const content = xhr.responseText;
                    
                    // Проверяем наличие ключевых элементов Plotly
                    const hasPlotlyDiv = content.includes('plotly-graph-div');
                    const hasPlotlyData = content.includes('Plotly.newPlot');
                    const hasPlotlyScript = content.includes('plotly-');
                    
                    console.log({
                        file: vizPath,
                        length: content.length,
                        hasPlotlyDiv: hasPlotlyDiv,
                        hasPlotlyData: hasPlotlyData,
                        hasPlotlyScript: hasPlotlyScript
                    });
                    
                    // Выводим начало и конец файла
                    console.log('Начало файла (первые 200 символов):');
                    console.log(content.substring(0, 200));
                    
                    console.log('Конец файла (последние 200 символов):');
                    console.log(content.substring(content.length - 200));
                    
                    return {
                        content: content,
                        stats: {
                            length: content.length,
                            hasPlotlyDiv: hasPlotlyDiv,
                            hasPlotlyData: hasPlotlyData,
                            hasPlotlyScript: hasPlotlyScript
                        }
                    };
                } else {
                    console.error(`Ошибка при загрузке файла: ${xhr.status}`);
                    return null;
                }
            } catch (e) {
                console.error(`Исключение при загрузке файла: ${e.message}`);
                return null;
            }
        },
        
        // Проверяет логи в sessionStorage
        checkLogs: function() {
            const logs = JSON.parse(sessionStorage.getItem('vizThumbnailLogs') || '[]');
            console.log('=== Логи генерации миниатюр ===');
            
            if (logs.length === 0) {
                console.log('Логи отсутствуют. Возможно, скрипт viz-thumbnails.js не запустился или не записал логи.');
                return [];
            }
            
            logs.forEach(log => {
                console.log(`[${log.time}] [${log.level}] ${log.message}`);
            });
            
            console.log('==============================');
            
            // Анализируем логи на наличие ошибок
            const errors = logs.filter(log => log.level === 'error');
            if (errors.length > 0) {
                console.log(`Найдено ${errors.length} ошибок:`);
                errors.forEach(error => {
                    console.log(`- ${error.message}`);
                });
            }
            
            return logs;
        },
        
        // Проверяет путь к файлам визуализаций
        checkPaths: function() {
            console.log('Проверка путей к файлам визуализаций...');
            
            // Текущий путь страницы
            console.log('Текущий путь: ' + window.location.pathname);
            
            // Базовый URL для относительных путей
            const base = document.querySelector('base');
            console.log('Базовый URL: ' + (base ? base.href : 'не задан'));
            
            // Попытка загрузить файл с разными путями для проверки
            const paths = [
                '/analytics_output/visualizations/viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
                '../analytics_output/visualizations/viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
                'analytics_output/visualizations/viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
                'c:/projects/analytics_output/visualizations/viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
                'file:///c:/projects/analytics_output/visualizations/viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html'
            ];
            
            const results = [];
            
            paths.forEach(path => {
                const img = new Image();
                img.onload = function() {
                    console.log(`Путь доступен: ${path}`);
                    results.push({
                        path: path,
                        status: 'доступен'
                    });
                };
                img.onerror = function() {
                    console.log(`Ошибка при загрузке: ${path}`);
                    results.push({
                        path: path,
                        status: 'недоступен'
                    });
                };
                img.src = path;
            });
            
            return results;
        }
    };
    
    console.log('Инструменты отладки визуализаций загружены. Используйте window.debugVisualizations для диагностики.');
})();