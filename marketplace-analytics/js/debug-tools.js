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
            console.log('Checking visualization file paths...');
            
            // Get base path from configuration
            const basePath = window.appConfig ? window.appConfig.paths.visualizations : '../analytics_output/visualizations/';
            
            // Try different relative path combinations
            const paths = [
                basePath + 'viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
                './' + basePath + 'viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html',
                '/' + basePath + 'viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.html'
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
        },

        // Добавить новую функцию для проверки статуса системы
        checkSystemStatus: function() {
            console.group('Статус системы визуализации данных');
            
            // Проверка наличия и состояния ключевых объектов
            const components = [
                { name: 'visualizationManager', obj: window.visualizationManager },
                { name: 'thumbnailManager', obj: window.thumbnailManager },
                { name: 'unifiedChartManager', obj: window.unifiedChartManager },
                { name: 'iframeChartHandler', obj: window.iframeChartHandler },
                { name: 'plotlyFullscreenAdapter', obj: window.plotlyFullscreenAdapter },
                { name: 'modalHelpers', obj: window.modalHelpers },
                { name: 'debugVisualizations', obj: window.debugVisualizations }
            ];
            
            console.log('Компоненты системы:');
            components.forEach(comp => {
                const status = comp.obj ? 'доступен' : 'недоступен';
                const hasInit = comp.obj && typeof comp.obj.init === 'function' ? 'есть метод init' : 'нет метода init';
                console.log(`- ${comp.name}: ${status}, ${hasInit}`);
            });
            
            // Проверка DOM-элементов
            console.log('\nКлючевые DOM-элементы:');
            const elements = [
                { name: '#visualizations-grid', el: document.querySelector('#visualizations-grid') },
                { name: '.visualization-card', el: document.querySelectorAll('.visualization-card') },
                { name: '.viz-thumbnail', el: document.querySelectorAll('.viz-thumbnail') }
            ];
            
            elements.forEach(item => {
                if (item.name.startsWith('#')) {
                    console.log(`- ${item.name}: ${item.el ? 'найден' : 'не найден'}`);
                } else {
                    console.log(`- ${item.name}: найдено ${item.el ? item.el.length : 0} элементов`);
                }
            });
            
            // Проверка базового пути
            console.log('\nНастройки путей:');
            console.log(`- visualizationsBasePath: ${window.visualizationsBasePath || 'не установлен'}`);
            
            console.groupEnd();
            
            return {
                components: components.map(c => ({ name: c.name, available: !!c.obj })),
                domElements: elements.map(e => ({ 
                    name: e.name, 
                    found: e.name.startsWith('#') ? !!e.el : (e.el ? e.el.length > 0 : false)
                })),
                paths: {
                    base: window.visualizationsBasePath || 'не установлен'
                }
            };
        },

        // Добавить новую функцию для автоматического определения и исправления путей к файлам
        fixVisualizationPaths: function() {
            console.log('Запуск автоматической коррекции путей к файлам визуализаций...');
            
            // Варианты путей для проверки
            const pathOptions = [
                '../analytics_output/visualizations/',
                './analytics_output/visualizations/',
                '/analytics_output/visualizations/',
                'c:/projects/analytics_output/visualizations/',
                '../../analytics_output/visualizations/'
            ];
            
            let workingPath = null;
            
            // Проверяем каждый вариант пути
            for (const path of pathOptions) {
                try {
                    const testImage = new Image();
                    const testComplete = false;
                    const testPath = path + 'viz_Chastota_upominaniy_dostoinstv_i_ikh_svyaz_s_reytingom.png';
                    
                    testImage.onload = function() {
                        console.log(`Успешно загружено изображение по пути: ${path}`);
                        workingPath = path;
                        window.visualizationsBasePath = path;
                        console.log(`Установлен рабочий путь: ${path}`);
                        
                        // Обновляем миниатюры, если есть thumbnailManager
                        if (window.thumbnailManager) {
                            window.thumbnailManager.refreshAll();
                        }
                    };
                    
                    testImage.src = testPath;
                } catch (e) {
                    console.warn(`Ошибка при проверке пути ${path}:`, e);
                }
            }
            
            return {
                checkedPaths: pathOptions,
                workingPath: workingPath || 'Не найден'
            };
        }
    };
    
    // Вызываем эту проверку автоматически через 2 секунды после загрузки
    setTimeout(() => {
        console.log('Автоматическая проверка статуса системы...');
        window.debugVisualizations.checkSystemStatus();
    }, 2000);
    
    console.log('Инструменты отладки визуализаций загружены. Используйте window.debugVisualizations для диагностики.');
})();