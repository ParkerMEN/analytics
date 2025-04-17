"""
Модуль для сбора отзывов с маркетплейса Wildberries.
Отвечает за получение отзывов по артикулу товара через API Wildberries,
обработку ответов и сохранение собранных отзывов в JSON-файл
для дальнейшего анализа.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import requests
import json
import re
import logging
import os
import argparse
from datetime import datetime
import random

# Глобальные настройки
SAVE_DEBUG_RESPONSES = False  # По умолчанию отключаем сохранение отладочных файлов

# Настройка логирования
def setup_logging():
    """
    Настраивает систему логирования с сохранением в файл
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"parser_log_{timestamp}.txt")
    
    # Настраиваем корневой логгер
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Вывод в консоль
        ]
    )
    
    logging.info(f"Логирование настроено. Лог-файл: {log_file}")
    return log_file

def get_mobile_user_agent():
    """Возвращает случайный User-Agent мобильного устройства"""
    mobile_user_agents = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/85.0.4183.109 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Mobile Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Mozilla/5.0 (Linux; Android 9; SAMSUNG SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/10.2 Chrome/71.0.3578.99 Mobile Safari/537.36"
    ]
    return random.choice(mobile_user_agents)

def get_product_url(article):
    """
    Формирует URL товара на WildBerries по его артикулу
    """
    return f"https://www.wildberries.ru/catalog/{article}/detail.aspx"

def extract_imt_id_from_page(driver):
    """
    Расширенный поиск imtId в различных элементах страницы
    """
    logging.info("Ищем imtId различными методами...")
    
    # Метод 1: Поиск в URL кнопки отзывов (как в текущей реализации)
    try:
        review_buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="feedbacks"], a[href*="reviews"]'))
        )
        
        for button in review_buttons:
            href = button.get_attribute('href')
            if href:
                imtId_match = re.search(r'imtId=(\d+)', href)
                if imtId_match:
                    imt_id = imtId_match.group(1)
                    logging.info(f"imtId найден в URL кнопки отзывов: {imt_id}")
                    return imt_id
    except Exception as e:
        logging.warning(f"Не удалось найти imtId в URL кнопки отзывов: {e}")
    
    # Метод 2: Поиск в data-атрибутах
    try:
        elements_with_data = driver.find_elements(By.CSS_SELECTOR, '[data-imt-id], [data-nm-id], [data-product-id]')
        for element in elements_with_data:
            for attr in ['data-imt-id', 'data-nm-id', 'data-product-id']:
                value = element.get_attribute(attr)
                if value and value.isdigit():
                    logging.info(f"imtId найден в атрибуте {attr}: {value}")
                    return value
    except Exception as e:
        logging.warning(f"Не удалось найти imtId в data-атрибутах: {e}")
    
    # Метод 3: Поиск в JSON-скриптах на странице
    try:
        script_elements = driver.find_elements(By.TAG_NAME, 'script')
        for script in script_elements:
            try:
                content = script.get_attribute('innerHTML')
                if content and ('productId' in content or 'imtId' in content):
                    # Ищем структуры JSON
                    json_matches = re.findall(r'\{[^{}]*"(imtId|productId)":\s*"?(\d+)"?[^{}]*\}', content)
                    for match in json_matches:
                        imt_id = match[1]
                        logging.info(f"imtId найден в скрипте: {imt_id}")
                        return imt_id
            except:
                continue
    except Exception as e:
        logging.warning(f"Не удалось найти imtId в скриптах: {e}")
    
    # Метод 4: Поиск в URL страницы товара
    try:
        current_url = driver.current_url
        article_match = re.search(r'/catalog/(\d+)/', current_url)
        if article_match:
            article = article_match.group(1)
            # В некоторых случаях Wildberries использует артикул как imtId
            logging.info(f"Возможный imtId найден в URL страницы: {article}")
            return article
    except Exception as e:
        logging.warning(f"Не удалось найти imtId в URL страницы: {e}")
    
    return None

def get_imt_id(product_url):
    """
    Получает imt_id товара с помощью Selenium
    """
    logging.info(f"Открываем страницу товара: {product_url}")
    
    # Настройка Selenium WebDriver с пользовательским агентом для ПК
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1366,768")  # Фиксированное разрешение для ПК
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")  # User-Agent для ПК
    
    # Опционально: запуск в безголовом режиме
    # chrome_options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(product_url)

    # Максимальное время ожидания загрузки страницы (5 минут)
    start_time = time.time()
    max_wait_time = 300  # 5 минут в секундах
    page_loaded = False
    
    logging.info("Ожидаем загрузки страницы товара (максимум 5 минут)...")
    
    try:
        # Ожидание загрузки основных элементов страницы
        while time.time() - start_time < max_wait_time:
            # Проверяем, загрузились ли основные элементы страницы
            try:
                # Проверяем наличие основного контейнера товара
                product_container = driver.find_element(By.CLASS_NAME, "product-page")
                # Проверяем наличие названия товара
                title = driver.find_element(By.CSS_SELECTOR, "h1.product-page__title")
                
                # Проверка на наличие контента (исключение пустых элементов)
                if title.text.strip():
                    logging.info(f"Страница товара загружена. Название товара: {title.text.strip()}")
                    page_loaded = True
                    break
                    
            except Exception as e:
                # Если элементы не найдены, ждем и продолжаем цикл
                pass
                
            # Делаем небольшую паузу перед следующей проверкой
            time.sleep(2)
            elapsed_time = time.time() - start_time
            if int(elapsed_time) % 15 == 0:  # Каждые 15 секунд показываем прогресс
                logging.info(f"Ожидаем загрузку... Прошло {int(elapsed_time)} секунд")
                
        if not page_loaded:
            logging.error(f"Страница не загрузилась в течение {max_wait_time} секунд. Завершение работы.")
            driver.quit()
            return None
            
        # Пробуем извлечь imtId с помощью расширенного метода
        imt_id = extract_imt_id_from_page(driver)
        if imt_id:
            driver.quit()
            return imt_id
            
        logging.error("Не удалось найти imtId товара")
        driver.quit()
        return None
            
    except Exception as e:
        logging.error(f"Ошибка при поиске imtId: {e}")
        # Делаем скриншот для диагностики
        try:
            driver.save_screenshot(f"error_{int(time.time())}.png")
        except:
            pass
        driver.quit()
        return None

def get_imt_id_via_product_api(article):
    """
    Получает imtId через API карточки товара как резервный метод
    """
    product_api_urls = [
        f"https://card.wb.ru/cards/detail?nm={article}",
        f"https://wbx-content-v2.wbstatic.net/ru/{article}.json",
        f"https://wbxcatalog-ru.wildberries.ru/nm-2-card/catalog/{article}/detail.json",
        f"https://card.wildberries.ru/cards/detail?nm={article}&locale=ru"
    ]
    
    for url in product_api_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Проверяем различные пути в JSON для нахождения imtId
                imt_id = None
                
                # Путь 1
                if "data" in data and "products" in data["data"] and len(data["data"]["products"]) > 0:
                    product = data["data"]["products"][0]
                    imt_id = product.get("root") or product.get("imtId") or product.get("imt_id")
                
                # Путь 2
                if not imt_id and "imt_id" in data:
                    imt_id = data["imt_id"]
                
                # Путь 3
                if not imt_id and "data" in data and "product" in data["data"]:
                    imt_id = data["data"]["product"].get("root") or data["data"]["product"].get("imtId")
                
                if imt_id:
                    logging.info(f"imtId получен через API карточки товара: {imt_id}")
                    return str(imt_id)
                
        except Exception as e:
            logging.warning(f"Ошибка при запросе к {url}: {e}")
    
    return None

def get_reviews(imt_id):
    """
    Получает отзывы о товаре по imt_id, перебирая разные хосты и версии API
    """
    # Список хостов API для проверки
    hosts = ["feedbacks.wb.ru", "feedbacks1.wb.ru", "feedbacks2.wb.ru", "feedbacks3.wb.ru", "feedbacks4.wb.ru"]
    # Список версий API для проверки
    versions = ["v1", "v2", "v3"]
    
    logging.info(f"Попытка получить отзывы для imt_id: {imt_id}")
    
    for host in hosts:
        for version in versions:
            url = f"https://{host}/feedbacks/{version}/{imt_id}"
            logging.info(f"Пробуем URL: {url}")
            
            # Добавляем заголовки для имитации обычного браузера
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://www.wildberries.ru/"
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                logging.info(f"Ответ от {url} - статус код: {response.status_code}")
                
                if response.status_code == 200:
                    # Сохраняем ответ в файл для отладки только если включена соответствующая настройка
                    if SAVE_DEBUG_RESPONSES:
                        debug_file = f"debug_response_{host}_{version}_{int(time.time())}.json"
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        logging.info(f"Ответ API сохранен в файл {debug_file} для отладки")
                    else:
                        logging.debug("Получен ответ от API (сохранение отладочных файлов отключено)")
                    
                    # Пробуем парсить как JSON
                    try:
                        data = response.json()
                        
                        # Проверяем, есть ли в ответе непустые отзывы
                        feedbacks = data.get("feedbacks")
                        feedback_count = data.get("feedbackCount", 0)
                        
                        if feedbacks and isinstance(feedbacks, list) and len(feedbacks) > 0:
                            logging.info(f"Найдены отзывы! URL: {url}")
                            logging.info(f"Количество отзывов: {len(feedbacks)}")
                            return data
                        elif feedback_count > 0:
                            logging.warning(f"API указывает, что есть {feedback_count} отзывов, но не возвращает их. URL: {url}")
                        else:
                            logging.info(f"Отзывы не найдены на {url}")
                    except ValueError as e:
                        logging.error(f"Ошибка при разборе JSON от {url}: {e}")
                        # Дополнительная обработка HTML-ответа, если необходимо
            except Exception as e:
                logging.error(f"Ошибка при обращении к {url}: {e}")
    
    logging.error("Отзывы не найдены ни на одном из API-эндпоинтов Wildberries")
    return None

def normalize_review_data(reviews_data):
    """
    Нормализует данные отзывов для единообразного формата
    """
    # В базовой версии возвращаем данные как есть
    # Вы можете расширить эту функцию в будущем для обработки разных форматов
    return reviews_data

def format_reviews_for_ai(reviews_data, article):
    """
    Форматирует отзывы в удобный для анализа AI текстовый формат
    и сохраняет в файл
    """
    logging.info("Форматирование отзывов для анализа AI")
    
    try:
        feedbacks = reviews_data.get('feedbacks', [])
        if not feedbacks:
            logging.error("Нет отзывов для форматирования")
            return None
            
        output_filename = f"reviews_{article}_prepared_for_ai.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as file:
            for i, feedback in enumerate(feedbacks, 1):
                # Получаем данные отзыва
                rating = feedback.get('productValuation', 0)
                date = feedback.get('createdDate', '').split('T')[0] if 'T' in feedback.get('createdDate', '') else feedback.get('createdDate', '')
                text = feedback.get('text', '').strip()
                
                # Проверяем поля "достоинства" и "недостатки"
                # В API Wildberries используются разные названия этих полей
                advantages = ''
                if 'advantages' in feedback:
                    advantages = feedback['advantages'].strip()
                elif 'pros' in feedback:
                    advantages = feedback['pros'].strip()
                
                disadvantages = ''
                if 'disadvantages' in feedback:
                    disadvantages = feedback['disadvantages'].strip()
                elif 'cons' in feedback:
                    disadvantages = feedback['cons'].strip()
                
                has_photo = False
                if 'photos' in feedback and len(feedback['photos']) > 0:
                    has_photo = True
                elif 'photo' in feedback and len(feedback['photo']) > 0:
                    has_photo = True
                
                # Форматируем отзыв
                file.write(f"Отзыв #{i}\n")
                file.write(f"Рейтинг: {rating}/5\n")
                file.write(f"Дата: {date}\n")
                if has_photo:
                    file.write("Есть фото\n")
                
                file.write("Текст отзыва: ")
                if advantages:
                    file.write(f"Достоинства: {advantages}\n")
                if disadvantages:
                    file.write(f"Недостатки: {disadvantages}\n")
                if text:
                    file.write(text)
                file.write("\n")
                file.write("-" * 30 + "\n")
        
        logging.info(f"Отзывы отформатированы и сохранены в файл {output_filename}")
        return output_filename
        
    except Exception as e:
        logging.error(f"Ошибка при форматировании отзывов: {e}")
        return None

def monitor_all_network_activity(driver, duration=10):
    """
    Мониторит все сетевые запросы для обнаружения новых источников данных
    """
    # Активируем перехват сетевых запросов
    driver.execute_cdp_cmd("Network.enable", {})
    
    # Начинаем запись логов сети
    driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
    
    # Задаем начальное время
    start_time = time.time()
    api_urls = []
    
    try:
        # Выполняем действия, которые могут вызвать загрузку отзывов
        actions = [
            # Прокрутка до блока отзывов
            lambda: driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);"),
            # Клик по вкладке отзывов (если есть)
            lambda: driver.find_element(By.CSS_SELECTOR, "[data-auto='reviews-link'], .comments, .feedback-tab").click(),
            # Прокрутка блока отзывов (если есть)
            lambda: driver.execute_script("""
                var reviewsBlock = document.querySelector(".comments-list, .feedbacks, .reviews");
                if (reviewsBlock) reviewsBlock.scrollBy(0, 300);
            """)
        ]
        
        # Выполняем действия и ожидаем запросы
        for action in actions:
            try:
                action()
                time.sleep(1)
            except:
                pass
            
            # Получаем логи запросов
            logs = driver.execute_cdp_cmd("Network.getResponseReceivedExtraInfo", {})
            requests_data = driver.get_log('performance')
            
            # Обрабатываем логи запросов
            for request_data in requests_data:
                try:
                    request = json.loads(request_data['message'])
                    if 'message' in request and request['message']['method'] == 'Network.responseReceived':
                        response = request['message']['params']
                        url = response['response']['url']
                        
                        # Фильтруем URL, связанные с отзывами, рейтингами и т.д.
                        keywords = ['feedback', 'review', 'rating', 'comment']
                        if any(keyword in url.lower() for keyword in keywords):
                            # Проверяем, является ли запрос к API (по формату ответа)
                            content_type = response['response'].get('headers', {}).get('content-type', '')
                            if 'application/json' in content_type:
                                api_urls.append(url)
                                logging.info(f"Обнаружен потенциальный API отзывов: {url}")
                except:
                    continue
        
        # Продолжаем мониторинг до истечения времени
        while time.time() - start_time < duration:
            # Периодически получаем новые логи
            logs = driver.get_log('performance')
            for log in logs:
                try:
                    request = json.loads(log['message'])
                    if 'message' in request and request['message']['method'] == 'Network.responseReceived':
                        response = request['message']['params']
                        url = response['response']['url']
                        
                        # Те же проверки, что и выше
                        keywords = ['feedback', 'review', 'rating', 'comment']
                        if any(keyword in url.lower() for keyword in keywords):
                            content_type = response['response'].get('headers', {}).get('content-type', '')
                            if 'application/json' in content_type:
                                api_urls.append(url)
                                logging.info(f"Обнаружен потенциальный API отзывов: {url}")
                except:
                    continue
            
            time.sleep(0.5)
    
    finally:
        # Отключаем перехват сети
        driver.execute_cdp_cmd("Network.disable", {})
    
    # Удаляем дубликаты URL
    api_urls = list(set(api_urls))
    
    # Сохраняем обнаруженные URL
    if api_urls:
        with open('discovered_api_urls.txt', 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for url in api_urls:
                f.write(f"{timestamp} | {url}\n")
    
    return api_urls

def document_api_changes():
    """
    Создает или обновляет документацию по API на основе
    обнаруженных изменений
    """
    # Загружаем историю изменений
    changes = load_api_changes_history()
    
    # Создаем markdown-документацию
    with open('wb_api_documentation.md', 'w', encoding='utf-8') as f:
        f.write("# Wildberries API Documentation\n\n")
        f.write("## Endpoints for Reviews\n\n")
        
        # Группируем по базовым типам
        endpoints_by_type = {}
        for endpoint in changes['endpoints']:
            base_type = endpoint['url'].split('/')[3] if len(endpoint['url'].split('/')) > 3 else 'other'
            if base_type not in endpoints_by_type:
                endpoints_by_type[base_type] = []
            endpoints_by_type[base_type].append(endpoint)
        
        # Выводим каждый тип
        for base_type, endpoints in endpoints_by_type.items():
            f.write(f"### {base_type.capitalize()} API\n\n")
            
            for endpoint in endpoints:
                f.write(f"#### {endpoint['url']}\n")
                f.write(f"- Status: {endpoint['status']}\n")
                f.write(f"- Last checked: {datetime.fromtimestamp(endpoint['last_checked']).strftime('%Y-%m-%d %H:%M:%S')}\n")
                if 'structure' in endpoint and endpoint['structure']:
                    f.write("- Data structure:\n")
                    f.write("```json\n")
                    f.write(json.dumps(endpoint['structure'], indent=2))
                    f.write("\n```\n")
                f.write("\n")
        
        # Документируем структуры данных
        f.write("## Response Structures\n\n")
        
        for structure in changes['structures']:
            f.write(f"### Structure detected on {datetime.fromtimestamp(structure['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("- Reviews path: `" + structure.get('reviews_path', 'Unknown') + "`\n")
            f.write("- Count path: `" + structure.get('count_path', 'Unknown') + "`\n")
            if 'review_format' in structure:
                f.write("- Review format:\n")
                f.write("```\n")
                for key, type_name in structure['review_format'].items():
                    f.write(f"{key}: {type_name}\n")
                f.write("```\n")
            f.write("\n")
    
    logging.info("API документация обновлена")

def save_reviews_to_file(reviews, filename):
    """
    Сохраняет отзывы в файл JSON
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(reviews, file, ensure_ascii=False, indent=4)
        logging.info(f"Отзывы сохранены в файл {filename}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении отзывов в файл {filename}: {e}")

def main():
    """
    Основная функция программы
    """
    # Настраиваем логирование
    log_file = setup_logging()
    logging.info("Запуск программы парсинга отзывов Wildberries")
    
    # Запрашиваем артикул товара
    article = input("Введите артикул товара: ")
    logging.info(f"Введен артикул: {article}")
    
    # Получаем URL товара
    product_url = get_product_url(article)
    logging.info(f"Переходим на страницу товара: {product_url}")
    
    # Получаем imt_id товара
    imt_id = get_imt_id(product_url)
    
    if not imt_id:
        logging.info("Не удалось получить imt_id через Selenium. Пробуем через API карточки товара...")
        imt_id = get_imt_id_via_product_api(article)
    
    if imt_id:
        logging.info(f"Получен imt_id: {imt_id}")
        
        # Получаем отзывы по imt_id
        reviews = get_reviews(imt_id)
        if reviews:
            # Создаем уникальное имя файла, включающее артикул товара
            filename = f"reviews_{article}.json"
            # Сохраняем отзывы в файл
            save_reviews_to_file(reviews, filename)
            print(f"Отзывы для артикула {article} сохранены в файл {filename}")
            
            # Форматируем отзывы для AI
            ai_filename = format_reviews_for_ai(reviews, article)
            if ai_filename:
                print(f"Форматированные отзывы сохранены в файл {ai_filename}")
            
            # Запуск анализатора...
        else:
            logging.error("Не удалось получить отзывы")
            print("Не удалось получить отзывы")
    else:
        logging.error("Не удалось получить imt_id товара")
        print("Не удалось получить imt_id товара")
    
    logging.info(f"Работа программы завершена. Лог сохранен в файл {log_file}")
    print(f"\nЛог работы программы сохранен в файл {log_file}")

if __name__ == "__main__":
    main()