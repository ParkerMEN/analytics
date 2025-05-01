import os
import re
import glob
import shutil
import logging
from datetime import datetime
from visualization_page_generator import VisualizationPageGenerator
from typing import List, Dict, Any

class VisualizationDataCollector:
    """Class for collecting visualization data from reports and files."""
    
    def __init__(self, output_dir="analytics_output"):
        self.visualizations_dir = os.path.join(output_dir, "visualizations")
        self.output_dir = output_dir
        self.visualization_images = []
        
        # Setup logging
        self.logger = logging.getLogger('VisualizationDataCollector')
        self.logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)
        
        # Create file handler
        os.makedirs(output_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(output_dir, "visualization_data_collector.log"), encoding="utf-8")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        self.logger.info("VisualizationDataCollector initialized")
    
    def collect_visualizations(self):
        """Collects information about all visualizations."""
        self.logger.info("Starting visualization data collection...")
        
        # Check for index file
        index_path = os.path.join(self.visualizations_dir, "index.md")
        if not os.path.exists(index_path):
            self.logger.error(f"Index file not found: {index_path}")
            return False
            
        # Get all visualization report files
        report_files = glob.glob(os.path.join(self.visualizations_dir, "reports", "*.md"))
        self.logger.info(f"Found {len(report_files)} visualization reports")
        
        # Get all visualization files with flexible naming patterns
        image_files = []
        html_files = []
        
        # Search in all possible locations with different naming patterns
        # 1. Exact matching based on report patterns
        for report_file in report_files:
            report_basename = os.path.basename(report_file)
            viz_number = re.search(r'report_(\d+)_', report_basename)
            if viz_number:
                viz_num = viz_number.group(1)
                # Name pattern variations
                patterns = [
                    f"viz_{viz_num}_*.png", 
                    f"viz_{viz_num}_*.html",
                    f"viz_Визуализация {viz_num}.png",
                    f"viz_Визуализация {viz_num}.html",
                    f"viz_*.png", 
                    f"viz_*.html"
                ]
                
                for pattern in patterns:
                    # Search in root visualizations directory
                    image_files.extend(glob.glob(os.path.join(self.visualizations_dir, pattern)))
                    # Search in output directory
                    output_dir = os.path.join(self.visualizations_dir, "output")
                    if os.path.exists(output_dir):
                        image_files.extend(glob.glob(os.path.join(output_dir, pattern)))
                    
                    # If HTML pattern, add to HTML files list
                    if ".html" in pattern:
                        html_files.extend(glob.glob(os.path.join(self.visualizations_dir, pattern)))
                        if os.path.exists(output_dir):
                            html_files.extend(glob.glob(os.path.join(output_dir, pattern)))
        
        # 2. General search for all possible visualization files
        for ext in ['png', 'jpg', 'jpeg', 'svg']:
            image_files.extend(glob.glob(os.path.join(self.visualizations_dir, f"*.{ext}")))
            
        html_files.extend(glob.glob(os.path.join(self.visualizations_dir, "*.html")))
        
        # Remove duplicates
        image_files = list(set(image_files))
        html_files = list(set(html_files))
        
        self.logger.info(f"Found {len(image_files)} image files and {len(html_files)} HTML files")
        
        # Normalize HTML files for CDN usage
        self._normalize_html_files(html_files)
        
        # Check if we need to run scripts to create visualizations
        if not image_files and not html_files:
            self.logger.info("No visualization files found. Running scripts to create them...")
            self._run_visualization_scripts()
            
            # Re-search after running scripts
            for ext in ['png', 'jpg', 'jpeg', 'svg']:
                new_images = glob.glob(os.path.join(self.visualizations_dir, f"*.{ext}"))
                if new_images:
                    image_files.extend(new_images)
            
            new_htmls = glob.glob(os.path.join(self.visualizations_dir, "*.html"))
            if new_htmls:
                html_files.extend(new_htmls)
                self._normalize_html_files(new_htmls)
            
            self.logger.info(f"After running scripts, found {len(image_files)} image files and {len(html_files)} HTML files")
        
        # Collect visualization information from reports with improved matching
        self.visualization_images = []
        processed_files = set()  # For tracking processed files
        
        for report_file in sorted(report_files):
            self.logger.debug(f"Processing report: {report_file}")
            viz_info = self._extract_visualization_info(report_file)
            
            if viz_info:
                # Extract visualization number and name from report filename
                report_basename = os.path.basename(report_file)
                
                # First try to find by visualization number
                viz_match = re.search(r'report_(\d+)_(.+)\.md', report_basename)
                if viz_match:
                    viz_num = viz_match.group(1)
                    viz_name_raw = viz_match.group(2)
                    viz_name = viz_name_raw.replace('_', ' ')
                    
                    # Create all possible filename variations
                    possible_names = [
                        f"viz_{viz_num}_",
                        f"viz_Визуализация {viz_num}",
                        f"viz_{viz_name}",
                        f"viz_{viz_name_raw}"
                    ]
                    
                    # Look for matching HTML file
                    html_match = None
                    for html_file in html_files:
                        html_basename = os.path.basename(html_file)
                        if any(possible_name in html_basename for possible_name in possible_names) or \
                           any(html_basename.lower().startswith(p.lower()) for p in possible_names):
                            html_match = html_file
                            break
                    
                    if html_match:
                        viz_info['html_path'] = html_match
                        viz_info['is_interactive'] = True
                        processed_files.add(html_match)
                        self.logger.info(f"Found HTML file for visualization {viz_info['title']}: {html_match}")
                    else:
                        self.logger.warning(f"HTML file for visualization {viz_info['title']} not found. "
                                           f"Searched for patterns: {', '.join(possible_names)}")
                    
                    # Look for matching image file
                    image_match = None
                    for image_file in image_files:
                        image_basename = os.path.basename(image_file)
                        if any(possible_name in image_basename for possible_name in possible_names) or \
                           any(image_basename.lower().startswith(p.lower()) for p in possible_names):
                            image_match = image_file
                            break
                    
                    if image_match:
                        viz_info['image_path'] = image_match
                        processed_files.add(image_match)
                        self.logger.info(f"Found image file for visualization {viz_info['title']}: {image_match}")
                    
                    # Add normalized title for fuzzy matching
                    viz_info['normalized_title'] = re.sub(r'[^a-zA-Zа-яА-Я0-9]', '', viz_info['title'].lower())
                    
                    # If we found at least one file, add the visualization
                    if viz_info.get('image_path') or viz_info.get('html_path'):
                        self.visualization_images.append(viz_info)
                    else:
                        self.logger.warning(f"No files found for visualization {viz_info['title']}")
                else:
                    self.logger.warning(f"Could not extract visualization number and name from file: {report_basename}")
        
        # Fix the HTML file matching logic for remaining files
        for html_file in html_files:
            if html_file in processed_files:
                continue
                
            html_basename = os.path.basename(html_file)
            # Create normalized version of HTML filename
            normalized_html = re.sub(r'[^a-zA-Zа-яА-Я0-9]', '', html_basename.lower())
            
            # Find the best match among visualization infos
            best_match = None
            best_match_score = 0
            
            for viz_info in self.visualization_images:
                if 'normalized_title' in viz_info and viz_info['normalized_title']:
                    # Calculate similarity score
                    from difflib import SequenceMatcher
                    similarity = SequenceMatcher(None, normalized_html, 
                                               viz_info['normalized_title']).ratio()
                    
                    if similarity > best_match_score and similarity > 0.6:  # 60% similarity threshold
                        best_match = viz_info
                        best_match_score = similarity
            
            if best_match and not best_match.get('html_path'):
                best_match['html_path'] = html_file
                best_match['is_interactive'] = True
                processed_files.add(html_file)
                self.logger.info(f"Matched HTML file {html_file} to visualization {best_match['title']} with score {best_match_score:.2f}")
        
        # Add any unused HTML files as additional visualizations
        for html_file in html_files:
            if html_file in processed_files:
                continue
                
            html_basename = os.path.basename(html_file)
            self.logger.info(f"Adding unused HTML: {html_basename}")
            
            # Create basic visualization for unparsed HTML
            viz_info = {
                'title': f"Visualization {html_basename}",
                'type': 'Interactive Visualization',
                'description': f"Automatically added visualization",
                'insights': 'No information available',
                'html_path': html_file,
                'is_interactive': True
            }
            
            self.visualization_images.append(viz_info)
        
        if len(self.visualization_images) > 0:
            self.logger.info(f"Successfully collected information about {len(self.visualization_images)} visualizations")
            return self.visualization_images
        else:
            self.logger.warning("Failed to collect visualization information")
            return False
    
    def _normalize_html_files(self, html_files):
        """Normalizes HTML files with visualizations to use Plotly CDN."""
        self.logger.info(f"Normalizing {len(html_files)} HTML files to use Plotly CDN")
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # If the file contains Plotly but doesn't use CDN
                if 'Plotly' in content and 'cdn.plot.ly' not in content:
                    self.logger.info(f"Modifying HTML file to use CDN: {html_file}")
                    
                    # Replace embedded JavaScript with CDN
                    if '<script type="text/javascript">window.PlotlyConfig' in content:
                        modified_content = content.replace(
                            '<script type="text/javascript">window.PlotlyConfig',
                            '<script charset="utf-8" src="https://cdn.plot.ly/plotly-latest.min.js"></script>\n<script type="text/javascript">window.PlotlyConfig'
                        )
                        
                        # Save modified version
                        with open(html_file, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                        
                        self.logger.info(f"HTML file successfully modified: {html_file}")
                
                # Ensure HTML file has proper body and html tags
                modified = False
                modified_content = content
                
                if '</body>' not in content:
                    if modified:
                        modified_content += '\n</body>'
                    else:
                        modified_content = content + '\n</body>'
                        modified = True
                        
                if '</html>' not in content:
                    if modified:
                        modified_content += '\n</html>'
                    else:
                        modified_content = content + '\n</html>'
                        modified = True
                
                # Save modified version
                if modified:
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    self.logger.info(f"HTML file {os.path.basename(html_file)} successfully normalized")
                    
            except Exception as e:
                self.logger.error(f"Error processing HTML file {html_file}: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
    
    def _extract_visualization_info(self, report_file):
        """Extracts visualization information from a report."""
        try:
            self.logger.debug(f"Extracting information from report: {report_file}")
            
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            info = {
                'title': '',
                'type': '',
                'description': '',
                'insights': '',
                'image_path': '',
                'html_path': '',
                'is_interactive': False
            }
            
            # Extract title
            title_match = re.search(r'# (.*?)$', content, re.MULTILINE)
            if title_match:
                info['title'] = title_match.group(1).strip()
                self.logger.debug(f"Extracted title: {info['title']}")
            else:
                # If no title, use filename
                base_name = os.path.basename(report_file).replace('report_', '').replace('.md', '')
                viz_match = re.search(r'(\d+)_(.+)', base_name)
                if viz_match:
                    viz_num = viz_match.group(1)
                    viz_name = viz_match.group(2).replace('_', ' ')
                    info['title'] = f"Visualization {viz_num}: {viz_name}"
                else:
                    info['title'] = f"Visualization {base_name}"
                self.logger.debug(f"Created title from filename: {info['title']}")
            
            # Extract visualization type
            type_match = re.search(r'## Тип визуализации\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
            if type_match:
                info['type'] = type_match.group(1).strip()
                self.logger.debug(f"Extracted type: {info['type']}")
            
            # Extract description
            desc_match = re.search(r'## Описание\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
            if desc_match:
                info['description'] = desc_match.group(1).strip()
                self.logger.debug(f"Extracted description, length: {len(info['description'])}")
            
            # Extract insights (with various header variations)
            insights_match = re.search(r'## (?:Ожидаемые )?[Ии]нсайты\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
            if insights_match:
                info['insights'] = insights_match.group(1).strip()
                self.logger.debug(f"Extracted insights, length: {len(info['insights'])}")
            
            return info
                
        except Exception as e:
            self.logger.error(f"Error processing file {report_file}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _run_visualization_scripts(self):
        """Runs scripts to create visualizations."""
        script_dir = os.path.join(self.visualizations_dir, "code")
        if not os.path.exists(script_dir):
            self.logger.warning(f"Script directory not found: {script_dir}")
            return
        
        script_files = glob.glob(os.path.join(script_dir, "*.py"))
        self.logger.info(f"Found {len(script_files)} visualization scripts")
        
        if not script_files:
            self.logger.warning("No visualization scripts found")
            return
        
        import subprocess
        import sys
        
        for script in script_files:
            try:
                self.logger.info(f"Running script: {script}")
                result = subprocess.run([sys.executable, script], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE,
                                       encoding='utf-8')
                
                if result.returncode == 0:
                    self.logger.info(f"Script {os.path.basename(script)} executed successfully")
                else:
                    self.logger.error(f"Script {os.path.basename(script)} failed with return code {result.returncode}")
                    self.logger.error(f"Error output: {result.stderr}")
            except Exception as e:
                self.logger.error(f"Error running script {script}: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())

    def _analyze_topic_correlations(self, data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Анализирует корреляции между темами на основе их совместного появления в отзывах
        """
        topic_counts = {}
        co_occurrences = {}
        
        # Подсчитываем, сколько раз каждая тема встречается и сколько раз темы встречаются вместе
        for review in data:
            topics = review.get("topics", [])
            for topic in topics:
                if topic not in topic_counts:
                    topic_counts[topic] = 0
                    co_occurrences[topic] = {}
                topic_counts[topic] += 1
                
                # Подсчитываем совместные появления тем
                for other_topic in topics:
                    if topic != other_topic:
                        if other_topic not in co_occurrences[topic]:
                            co_occurrences[topic][other_topic] = 0
                        co_occurrences[topic][other_topic] += 1
        
        # Рассчитываем корреляции
        correlations = {}
        for topic, co_topics in co_occurrences.items():
            correlations[topic] = {}
            for co_topic, co_count in co_topics.items():
                # Формула коэффициента Жаккара: |A ∩ B| / |A ∪ B| 
                # |A ∩ B| = совместное появление
                # |A ∪ B| = появление A + появление B - совместное появление
                union = topic_counts[topic] + topic_counts[co_topic] - co_count
                if union > 0:
                    correlations[topic][co_topic] = co_count / union
                else:
                    correlations[topic][co_topic] = 0
                    
        return correlations

# Function to generate a report from visualizations
def generate_report():
    # Initialize data collector
    data_collector = VisualizationDataCollector()
    
    # Collect visualization data
    visualization_data = data_collector.collect_visualizations()
    
    if visualization_data:
        # Initialize page generator
        page_generator = VisualizationPageGenerator()
        
        # Generate HTML report
        report_path = page_generator.generate_html_report(visualization_data)
        
        if report_path:
            data_collector.logger.info(f"Report generated successfully: {report_path}")
            return report_path
        else:
            data_collector.logger.error("Failed to generate report")
            return None
    else:
        data_collector.logger.error("Failed to collect visualization data")
        return None

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("visualization_report.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("visualization_report_main")
    
    logger.info("Starting visualization report generation process...")
    
    # Generate report
    report_path = generate_report()
    
    if report_path:
        logger.info("Report created successfully.")
        logger.info(f"Report path: {report_path}")
    else:
        logger.error("Failed to create report.")

if __name__ == "__main__":
    main()