import os
import re
import logging
import markdown
from bs4 import BeautifulSoup
from datetime import datetime

class VisualizationPageGenerator:
    """Class for generating HTML pages with visualizations."""
    
    def __init__(self, output_dir="analytics_output"):
        self.output_dir = output_dir
        self.template_file = "analytics_report.html"
        self.output_file = os.path.join(output_dir, "visualization_report.html")
        
        # Setup logging
        self.logger = logging.getLogger('VisualizationPageGenerator')
        self.logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)
        
        # Create file handler
        os.makedirs(output_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(output_dir, "visualization_page_generator.log"), encoding="utf-8")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        self.logger.info("VisualizationPageGenerator initialized")

    def generate_html_report(self, visualization_data):
        """Generates an HTML report based on template and collected visualizations."""
        self.logger.info("Generating HTML report...")
        
        # Load template
        template_html = self._find_or_create_template()
        if not template_html:
            return False
        
        try:
            # Parse the HTML template
            soup = BeautifulSoup(template_html, 'html.parser')
            
            # Add styles for dashboard if not present
            self._ensure_dashboard_styles(soup)
            
            # Get or create content container
            container = self._get_or_create_visualization_container(soup)
            
            # Generate visualizations
            for viz_idx, viz in enumerate(visualization_data):
                self._add_visualization_to_container(soup, container, viz, viz_idx)
            
            # Add filter scripts
            self._add_filter_scripts(soup)
            
            # Save final report
            output_path = self.output_file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(str(soup))
            self.logger.info(f"HTML report saved: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _find_or_create_template(self):
        """Finds or creates an HTML template for the report."""
        possible_locations = [
            self.template_file,
            os.path.join(os.getcwd(), "analytics_report.html"),
            os.path.join(os.path.dirname(os.getcwd()), "analytics_report.html"),
            os.path.join(os.path.dirname(self.output_file), "analytics_report.html")
        ]
        
        for location in possible_locations:
            if os.path.exists(location):
                self.logger.info(f"Found template: {location}")
                with open(location, "r", encoding="utf-8") as f:
                    return f.read()
        
        self.logger.warning("Template not found. Creating default template.")
        return self._create_default_template()
    
    def _create_default_template(self):
        """Creates a default HTML template when none is found."""
        self.logger.info("Creating default HTML template")
        
        template = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Аналитический отчет с визуализациями</title>
    <style>
        :root {
            --primary-color: #3498db;
            --secondary-color: #2c3e50;
            --accent-color: #e74c3c;
            --light-bg: #f8f9fa;
            --dark-bg: #343a40;
            --text-light: #7f8c8d;
            --border-color: #eaeaea;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background-color: var(--dark-bg);
            color: white;
            padding: 20px 0;
            margin-bottom: 30px;
        }
        
        header .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .dashboard-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(600px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .visualization-card {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
            background-color: white;
            margin-bottom: 20px;
        }
        
        .visualization-card:hover {
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            transform: translateY(-5px);
        }
        
        .visualization-header {
            padding: 15px;
            border-bottom: 1px solid var(--border-color);
            background-color: var(--light-bg);
        }
        
        .visualization-header h3 {
            margin: 0;
            color: var(--secondary-color);
            font-size: 18px;
        }
        
        .visualization-type {
            font-size: 14px;
            color: var(--text-light);
            margin-top: 5px;
        }
        
        .visualization-content {
            padding: 15px;
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .visualization-content iframe {
            width: 100%;
            height: 500px;
            border: none;
        }
        
        .visualization-content .plotly-graph {
            width: 100%;
            height: 500px;
        }
        
        .visualization-content img {
            max-width: 100%;
            max-height: 400px;
            display: block;
            margin: 0 auto;
        }
        
        .visualization-insights {
            padding: 15px;
            border-top: 1px solid var(--border-color);
            background-color: var(--light-bg);
        }
        
        .visualization-insights h4 {
            margin-top: 0;
            color: var(--secondary-color);
            font-size: 16px;
        }
        
        .filter-container {
            margin-bottom: 30px;
            padding: 15px;
            background-color: var(--light-bg);
            border-radius: 8px;
            border-left: 5px solid var(--primary-color);
        }
        
        .filter-group {
            margin-bottom: 15px;
            display: inline-block;
            margin-right: 20px;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        
        .filter-group select {
            padding: 8px;
            width: 200px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        
        .filter-button {
            padding: 8px 16px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        
        .filter-button:hover {
            background-color: #2980b9;
        }
        
        .tab-container {
            margin-bottom: 20px;
        }
        
        .tab {
            overflow: hidden;
            border: 1px solid var(--border-color);
            background-color: var(--light-bg);
            border-radius: 8px 8px 0 0;
        }
        
        .tab button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 12px 16px;
            transition: 0.3s;
            font-size: 16px;
            font-weight: bold;
            color: var(--secondary-color);
        }
        
        .tab button:hover {
            background-color: #ddd;
        }
        
        .tab button.active {
            background-color: white;
            border-bottom: 3px solid var(--primary-color);
        }
        
        .tabcontent {
            display: none;
            padding: 20px;
            border: 1px solid var(--border-color);
            border-top: none;
            border-radius: 0 0 8px 8px;
            animation: fadeEffect 1s;
            background-color: white;
        }
        
        @keyframes fadeEffect {
            from {opacity: 0;}
            to {opacity: 1;}
        }
        
        footer {
            margin-top: 50px;
            padding: 20px 0;
            background-color: var(--dark-bg);
            color: white;
            text-align: center;
        }
        
        .report-info {
            margin-top: 30px;
            padding: 15px;
            background-color: var(--light-bg);
            border-radius: 8px;
            font-size: 14px;
            color: var(--text-light);
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Аналитический отчет с визуализациями</h1>
            <div>Дата создания: <time datetime="{{date_iso}}">{{date_human}}</time></div>
        </div>
    </header>
    <div class="container">
        <div class="filter-container">
            <div class="filter-group">
                <label for="filter-rating">Фильтр по рейтингу:</label>
                <select id="filter-rating">
                    <option value="all">Все рейтинги</option>
                    <option value="1">1 звезда</option>
                    <option value="2">2 звезды</option>
                    <option value="3">3 звезды</option>
                    <option value="4">4 звезды</option>
                    <option value="5">5 звезд</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="filter-topic">Фильтр по теме:</label>
                <select id="filter-topic">
                    <option value="all">Все темы</option>
                </select>
            </div>
            <button class="filter-button" onclick="applyFilters()">Применить фильтры</button>
            <button class="filter-button" onclick="resetFilters()">Сбросить</button>
        </div>
        
        <div class="tab-container">
            <div class="tab">
                <button class="tablinks active" onclick="openTab(event, 'AllTab')">Все визуализации</button>
                <button class="tablinks" onclick="openTab(event, 'RatingTab')">По рейтингу</button>
                <button class="tablinks" onclick="openTab(event, 'TopicTab')">По темам</button>
                <button class="tablinks" onclick="openTab(event, 'InteractiveTab')">Интерактивные</button>
            </div>
            
            <div id="AllTab" class="tabcontent" style="display: block;">
                <div class="dashboard-container" id="all-visualizations">
                    <!-- Здесь будут размещаться визуализации -->
                </div>
            </div>
            
            <div id="RatingTab" class="tabcontent">
                <div class="dashboard-container" id="rating-visualizations">
                    <!-- Визуализации по рейтингу -->
                </div>
            </div>
            
            <div id="TopicTab" class="tabcontent">
                <div class="dashboard-container" id="topic-visualizations">
                    <!-- Визуализации по темам -->
                </div>
            </div>
            
            <div id="InteractiveTab" class="tabcontent">
                <div class="dashboard-container" id="interactive-visualizations">
                    <!-- Интерактивные визуализации -->
                </div>
            </div>
        </div>
        
        <div class="report-info">
            <p>Отчет сгенерирован автоматически на основе данных анализа отзывов.</p>
        </div>
    </div>
    
    <footer>
        <div class="container">
            <p>&copy; {{current_year}} Аналитический отчет</p>
        </div>
    </footer>

    <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
        
        function applyFilters() {
            const ratingFilter = document.getElementById('filter-rating').value;
            const topicFilter = document.getElementById('filter-topic').value;
            
            const cards = document.querySelectorAll('.visualization-card');
            
            cards.forEach(card => {
                let showByRating = ratingFilter === 'all' || card.dataset.rating === ratingFilter;
                let showByTopic = topicFilter === 'all' || card.dataset.topics.includes(topicFilter);
                
                if (showByRating && showByTopic) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        
        function resetFilters() {
            document.getElementById('filter-rating').value = 'all';
            document.getElementById('filter-topic').value = 'all';
            
            const cards = document.querySelectorAll('.visualization-card');
            cards.forEach(card => {
                card.style.display = 'block';
            });
        }
        
        // Find unique topics and populate the topic filter
        function populateTopicFilter() {
            const cards = document.querySelectorAll('.visualization-card');
            const topics = new Set();
            
            cards.forEach(card => {
                if (card.dataset.topics) {
                    const cardTopics = card.dataset.topics.split(' ');
                    cardTopics.forEach(topic => {
                        if (topic && topic !== 'undefined') {
                            topics.add(topic);
                        }
                    });
                }
            });
            
            const topicFilter = document.getElementById('filter-topic');
            topics.forEach(topic => {
                const option = document.createElement('option');
                option.value = topic;
                option.textContent = topic.charAt(0).toUpperCase() + topic.slice(1);
                topicFilter.appendChild(option);
            });
        }
        
        // Initialize tabs and filters
        document.addEventListener('DOMContentLoaded', function() {
            populateTopicFilter();
            
            // Organize visualizations into tabs
            const cards = document.querySelectorAll('.visualization-card');
            cards.forEach(card => {
                let clone;
                
                // Add to rating tab if it has a rating
                if (card.dataset.rating && card.dataset.rating !== 'undefined') {
                    clone = card.cloneNode(true);
                    document.getElementById('rating-visualizations').appendChild(clone);
                }
                
                // Add to topic tab if it has topics
                if (card.dataset.topics && card.dataset.topics !== 'undefined') {
                    clone = card.cloneNode(true);
                    document.getElementById('topic-visualizations').appendChild(clone);
                }
                
                // Add to interactive tab if it has an iframe
                if (card.querySelector('iframe')) {
                    clone = card.cloneNode(true);
                    document.getElementById('interactive-visualizations').appendChild(clone);
                }
            });
        });
    </script>
</body>
</html>
"""
        # Replace placeholders with dynamic values
        now = datetime.now()
        template = template.replace('{{date_iso}}', now.isoformat())
        template = template.replace('{{date_human}}', now.strftime('%d.%m.%Y %H:%M'))
        template = template.replace('{{current_year}}', str(now.year))
        
        # Save template for future use
        with open("analytics_report.html", "w", encoding="utf-8") as f:
            f.write(template)
            
        return template
    
    def _ensure_dashboard_styles(self, soup):
        """Ensures dashboard styles are present in the HTML."""
        if not soup.find('style', string=lambda x: x and 'dashboard-container' in x):
            style_tag = soup.new_tag("style")
            style_tag.string = """
            .dashboard-container {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(600px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            
            .visualization-card {
                border: 1px solid #eaeaea;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 8px rgba(0,0,0,0.05);
                transition: all 0.3s ease;
                background-color: white;
                margin-bottom: 20px;
            }
            
            .visualization-card:hover {
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
                transform: translateY(-5px);
            }
            
            .visualization-header {
                padding: 15px;
                border-bottom: 1px solid #eaeaea;
                background-color: #f8f9fa;
            }
            
            .visualization-header h3 {
                margin: 0;
                color: #2c3e50;
                font-size: 18px;
            }
            
            .visualization-type {
                font-size: 14px;
                color: #7f8c8d;
                margin-top: 5px;
            }
            
            .visualization-content {
                padding: 15px;
                min-height: 400px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .visualization-content iframe {
                width: 100%;
                height: 500px;
                border: none;
            }
            
            .visualization-content img {
                max-width: 100%;
                max-height: 400px;
                display: block;
                margin: 0 auto;
            }
            
            .visualization-insights {
                padding: 15px;
                border-top: 1px solid #eaeaea;
                background-color: #f8f9fa;
            }
            
            .visualization-insights h4 {
                margin-top: 0;
                color: #2c3e50;
                font-size: 16px;
            }
            """
            soup.head.append(style_tag)
    
    def _get_or_create_visualization_container(self, soup):
        """Gets or creates the container for visualizations."""
        # Try to find the container designated for visualizations
        container = soup.find("div", id="all-visualizations")
        if not container:
            # Find any element with "visualization" in its class or id
            container = soup.find(lambda tag: tag.name == "div" and 
                                  ("visualization" in tag.get("class", []) or 
                                   "visualization" in tag.get("id", "")))
        
        # If still not found, create a new one
        if not container:
            # Find the main container
            main_container = soup.find("div", class_="container")
            if not main_container:
                main_container = soup.body
            
            # Create a new dashboard container
            container = soup.new_tag("div", **{"class": "dashboard-container", "id": "all-visualizations"})
            main_container.append(container)
        
        return container
    
    def _add_visualization_to_container(self, soup, container, viz, viz_idx):
        """Adds a visualization to the container."""
        self.logger.debug(f"Adding visualization {viz_idx}: {viz['title']}")
        
        # Create card for visualization
        viz_card = soup.new_tag("div", **{
            "class": "visualization-card", 
            "data-title": viz['title'],
            "data-rating": self._extract_rating_from_title(viz['title']),
            "data-topics": self._extract_topics_from_description(viz.get('description', ''))
        })
        
        # Create card header
        viz_header = soup.new_tag("div", **{"class": "visualization-header"})
        
        # Visualization title
        viz_title = soup.new_tag("h3")
        viz_title.string = viz['title']
        viz_header.append(viz_title)
        
        # Visualization type
        if viz.get('type'):
            viz_type = soup.new_tag("div", **{"class": "visualization-type"})
            viz_type.string = f"Тип: {viz['type']}"
            viz_header.append(viz_type)
        
        viz_card.append(viz_header)
        
        # Visualization content
        viz_content = soup.new_tag("div", **{"class": "visualization-content"})
        
        # Handle different visualization types
        if viz.get('is_interactive') and viz.get('html_path'):
            # Create iframe for interactive visualizations
            iframe = soup.new_tag("iframe", 
                                 src=viz['html_path'].replace('\\', '/'),
                                 **{"frameborder": "0", "scrolling": "no"})
            viz_content.append(iframe)
        elif viz.get('image_path'):
            # Create img tag for static visualizations
            img = soup.new_tag("img", 
                              src=viz['image_path'].replace('\\', '/'),
                              alt=viz['title'])
            viz_content.append(img)
        else:
            # Placeholder for visualizations without content
            placeholder = soup.new_tag("div", **{"class": "visualization-placeholder"})
            placeholder.string = "Содержимое визуализации не найдено"
            viz_content.append(placeholder)
        
        viz_card.append(viz_content)
        
        # Visualization insights
        if viz.get('insights'):
            viz_insights = soup.new_tag("div", **{"class": "visualization-insights"})
            insights_title = soup.new_tag("h4")
            insights_title.string = "Инсайты"
            viz_insights.append(insights_title)
            
            # Convert markdown to HTML
            insights_html = markdown.markdown(viz['insights'])
            insights_soup = BeautifulSoup(insights_html, 'html.parser')
            
            viz_insights.append(insights_soup)
            viz_card.append(viz_insights)
        
        container.append(viz_card)

    def _add_filter_scripts(self, soup):
        """Ensures filter scripts are present in the HTML."""
        # Check if filter script already exists
        if not soup.find('script', string=lambda x: x and 'function applyFilters()' in x):
            script_tag = soup.new_tag("script")
            script_tag.string = """
            function applyFilters() {
                const ratingFilter = document.getElementById('filter-rating').value;
                const topicFilter = document.getElementById('filter-topic').value;
                
                const cards = document.querySelectorAll('.visualization-card');
                
                cards.forEach(card => {
                    let showByRating = ratingFilter === 'all' || card.dataset.rating === ratingFilter;
                    let showByTopic = topicFilter === 'all' || card.dataset.topics.includes(topicFilter);
                    
                    if (showByRating && showByTopic) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
            
            function resetFilters() {
                document.getElementById('filter-rating').value = 'all';
                document.getElementById('filter-topic').value = 'all';
                
                const cards = document.querySelectorAll('.visualization-card');
                cards.forEach(card => {
                    card.style.display = 'block';
                });
            }
            
            // Find unique topics and populate the topic filter
            function populateTopicFilter() {
                const cards = document.querySelectorAll('.visualization-card');
                const topics = new Set();
                
                cards.forEach(card => {
                    if (card.dataset.topics) {
                        const cardTopics = card.dataset.topics.split(' ');
                        cardTopics.forEach(topic => {
                            if (topic && topic !== 'undefined') {
                                topics.add(topic);
                            }
                        });
                    }
                });
                
                const topicFilter = document.getElementById('filter-topic');
                topics.forEach(topic => {
                    const option = document.createElement('option');
                    option.value = topic;
                    option.textContent = topic.charAt(0).toUpperCase() + topic.slice(1);
                    topicFilter.appendChild(option);
                });
            }
            
            // Initialize tabs and filters when DOM is loaded
            document.addEventListener('DOMContentLoaded', function() {
                populateTopicFilter();
                
                // Organize visualizations into tabs
                const cards = document.querySelectorAll('.visualization-card');
                cards.forEach(card => {
                    let clone;
                    
                    // Add to rating tab if it has a rating
                    if (card.dataset.rating && card.dataset.rating !== 'undefined') {
                        clone = card.cloneNode(true);
                        document.getElementById('rating-visualizations').appendChild(clone);
                    }
                    
                    // Add to topic tab if it has topics
                    if (card.dataset.topics && card.dataset.topics !== 'undefined') {
                        clone = card.cloneNode(true);
                        document.getElementById('topic-visualizations').appendChild(clone);
                    }
                    
                    // Add to interactive tab if it has an iframe
                    if (card.querySelector('iframe')) {
                        clone = card.cloneNode(true);
                        document.getElementById('interactive-visualizations').appendChild(clone);
                    }
                });
            });
            """
            soup.body.append(script_tag)
    
    def _extract_rating_from_title(self, title):
        """Extracts rating information from visualization title."""
        # Look for patterns like "X звезд" or "X⭐"
        rating_match = re.search(r'(\d+)[\s-]?(?:звезд|⭐)', title.lower())
        if rating_match:
            return rating_match.group(1)
        return ""
    
    def _extract_topics_from_description(self, description):
        """Extracts topic information from visualization description."""
        topics = []
        
        # Look for key topics in the description
        keywords = {
            'аккумулятор': 'аккумулятор',
            'культиватор': 'культиватор',
            'упаковк': 'упаковка',
            'доставк': 'доставка',
            'колес': 'колеса',
            'запуск': 'запуск',
            'мощност': 'мощность',
            'легк': 'легкость'
        }
        
        description_lower = description.lower()
        
        for keyword, topic in keywords.items():
            if keyword in description_lower:
                topics.append(topic)
        
        return ' '.join(topics)