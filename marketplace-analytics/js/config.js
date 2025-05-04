/**
 * Global configuration settings for the application
 */
(function() {
    'use strict';
    
    window.appConfig = {
        // Base paths (configurable for different environments)
        paths: {
            // Use relative paths instead of absolute paths
            visualizations: '../analytics_output/visualizations/',
            thumbnails: '../analytics_output/thumbnails/'
        },
        
        // Debug settings
        debug: false,
        
        // Default visualizations for demo/fallback
        fallbackVisualizations: [
            {
                id: 'viz_demo',
                title: 'Demo Visualization',
                path: 'demo_visualization.html',
                type: 'bar',
                category: 'demo'
            }
        ]
    };
})();