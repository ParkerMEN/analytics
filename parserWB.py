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
from datetime import datetime

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

def get_product_url(article):
    """
    Формирует URL товара на WildBerries по его артикулу
    """
    return f"https://www.wildberries.ru/catalog/{article}/detail.aspx"

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
            
        # Прокручиваем страницу в поисках кнопки отзывов
        logging.info("Страница загружена, начинаем поиск кнопки отзывов...")
        
        # Расширенный список селекторов для поиска кнопки отзывов, в порядке приоритета
        review_button_selectors = [
            ".product-page__reviews a",
            "a.btn-base.comments__btn-all",
            "a.product-feedbacks__button",
            "a.j-reviews-count",
            "a.show-all-reviews",
            "a[href*='feedbacks']",
            "a.review-button",
            "div.product-page__review-block a",
            "button:contains('Смотреть все отзывы')",
            ".comments-list-header a",
            ".product-review__button"
        ]
        
        # Прокручиваем страницу постепенно и ищем кнопку отзывов
        found_button = False
        max_scroll_attempts = 15
        
        for i in range(max_scroll_attempts):
            logging.info(f"Прокрутка {i+1}/{max_scroll_attempts}, поиск кнопки отзывов")
            
            # Плавная прокрутка вниз
            driver.execute_script(f"window.scrollTo(0, {i * 500});")
            time.sleep(1)
            
            # Проверяем все селекторы
            for selector in review_button_selectors:
                try:
                    # Пробуем найти элемент с XPath, если это содержит текст
                    if ":contains" in selector:
                        text = selector.split(":contains('")[1].split("')")[0]
                        xpath = f"//*[contains(text(), '{text}')]"
                        elements = driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            logging.info(f"Найдена кнопка отзывов: {element.text or selector}")
                            
                            # Делаем скриншот для подтверждения
                            driver.save_screenshot(f"found_review_button_{int(time.time())}.png")
                            
                            # Прокручиваем к элементу
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(1)
                            
                            # Извлекаем URL или текст перед кликом
                            element_href = element.get_attribute("href") if element.tag_name == "a" else None
                            element_text = element.text
                            
                            logging.info(f"Кнопка отзывов: href='{element_href}', text='{element_text}'")
                            
                            if element_href and "imtId=" in element_href:
                                imt_id = element_href.split("imtId=")[1].split("&")[0]
                                logging.info(f"Извлечен imtId из URL кнопки: {imt_id}")
                                driver.quit()
                                return imt_id
                                
                            # Пытаемся кликнуть на кнопку
                            logging.info("Кликаем на кнопку отзывов...")
                            element.click()
                            time.sleep(3)  # Ждем загрузки страницы отзывов
                            
                            # Проверяем, изменился ли URL
                            current_url = driver.current_url
                            logging.info(f"URL после клика: {current_url}")
                            
                            if "feedbacks" in current_url or "reviews" in current_url or "imtId=" in current_url:
                                if "imtId=" in current_url:
                                    imt_id = current_url.split("imtId=")[1].split("&")[0]
                                    logging.info(f"Извлечен imtId из URL после клика: {imt_id}")
                                    driver.quit()
                                    return imt_id
                                else:
                                    # Пытаемся найти imtId на странице отзывов
                                    logging.info("Ищем imtId на странице отзывов...")
                                    time.sleep(2)
                                    page_source = driver.page_source
                                    imt_id_match = re.search(r'"imtId"\s*:\s*"?(\d+)"?', page_source) or \
                                                   re.search(r"'imtId'\s*:\s*'?(\d+)'?", page_source) or \
                                                   re.search(r'imtId=(\d+)', page_source)
                                    
                                    if imt_id_match:
                                        imt_id = imt_id_match.group(1)
                                        logging.info(f"Извлечен imtId из кода страницы отзывов: {imt_id}")
                                        driver.quit()
                                        return imt_id
                                    
                                    # Берем ID товара из URL как fallback
                                    product_id = product_url.split('/catalog/')[1].split('/detail')[0]
                                    if product_id.isdigit():
                                        logging.info(f"Используем ID товара как imtId: {product_id}")
                                        driver.quit()
                                        return product_id
                            
                            found_button = True
                            break
                except Exception as e:
                    continue
                    
            if found_button:
                break
                
        # Если кнопку не нашли, попробуем использовать ID товара как imtId
        if not found_button:
            logging.warning("Кнопка 'Смотреть все отзывы' не найдена. Пробуем альтернативный способ...")
            
            # Делаем скриншот для диагностики
            driver.save_screenshot(f"no_review_button_{int(time.time())}.png")
            
            # Пытаемся найти imtId в исходном коде страницы
            page_source = driver.page_source
            imt_id_match = re.search(r'"imtId"\s*:\s*"?(\d+)"?', page_source) or \
                           re.search(r"'imtId'\s*:\s*'?(\d+)'?", page_source) or \
                           re.search(r'imtId=(\d+)', page_source)
            
            if imt_id_match:
                imt_id = imt_id_match.group(1)
                logging.info(f"Извлечен imtId из исходного кода: {imt_id}")
                driver.quit()
                return imt_id
                
            # В качестве последнего резерва используем ID товара
            product_id = product_url.split('/catalog/')[1].split('/detail')[0]
            if product_id.isdigit():
                logging.info(f"Используем ID товара как имя imtId: {product_id}")
                driver.quit()
                return product_id
                
            logging.error("Не удалось найти imtId товара")
            driver.quit()
            return None
            
    except Exception as e:
        logging.error(f"Ошибка при поиске кнопки отзывов: {e}")
        # Делаем скриншот для диагностики
        try:
            driver.save_screenshot(f"error_{int(time.time())}.png")
        except:
            pass
        driver.quit()
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
                    # Сохраняем ответ в файл для отладки
                    debug_file = f"debug_response_{host}_{version}_{int(time.time())}.json"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logging.info(f"Ответ API сохранен в файл {debug_file} для отладки")
                    
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
                        # Если это не JSON, возможно это HTML - попробуем найти данные в нём
                        logging.info("Пробуем найти данные в HTML ответе...")
                        
                        # Ищем данные отзывов в HTML или скриптах страницы
                        html_content = response.text
                        
                        # Сохраняем HTML для анализа
                        with open(f"debug_html_{host}_{version}_{int(time.time())}.html", 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        
                        # Ищем JSON данные в скриптах
                        json_data_pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
                        matches = re.findall(json_data_pattern, html_content, re.DOTALL)
                        
                        if matches:
                            for match in matches:
                                try:
                                    data = json.loads(match)
                                    logging.info("Найдены данные в HTML скрипте")
                                    
                                    # Ищем отзывы в объекте данных
                                    if 'reviews' in str(data) or 'feedbacks' in str(data):
                                        logging.info("Обнаружены данные отзывов в извлеченном объекте")
                                        # Сохраняем извлеченные данные для анализа
                                        with open(f"extracted_data_{int(time.time())}.json", 'w', encoding='utf-8') as f:
                                            json.dump(data, f, ensure_ascii=False, indent=2)
                                        return data
                                except Exception as e:
                                    logging.error(f"Ошибка при разборе извлеченных данных: {e}")
                else:
                    logging.warning(f"Ошибка запроса к {url}. Код ответа: {response.status_code}")
            except Exception as e:
                logging.error(f"Ошибка при обращении к {url}: {e}")
    
    logging.error("Отзывы не найдены ни на одном из API-эндпоинтов Wildberries")
    return None

def save_reviews_to_file(reviews, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(reviews, file, ensure_ascii=False, indent=4)
        logging.info(f"Reviews saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving reviews to file: {e}")

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
    
    if imt_id:
        logging.info(f"Получен imt_id: {imt_id}")
        
        # Получаем отзывы
        reviews_data = get_reviews(imt_id)
        
        if reviews_data:
            # Сохраняем отзывы в файл
            filename = f"reviews_{article}.json"
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(reviews_data, file, ensure_ascii=False, indent=4)
            
            logging.info(f"Отзывы сохранены в файл {filename}")
            print(f"\nОтзывы успешно получены и сохранены в файл {filename}")
            
            # Выводим статистику по отзывам
            feedbacks = reviews_data.get('feedbacks', [])
            feedback_count = len(feedbacks)
            
            if feedback_count > 0:
                # Рассчитываем среднюю оценку
                ratings = [f.get('productValuation', 0) for f in feedbacks if f.get('productValuation') is not None]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0
                
                logging.info(f"Получено {feedback_count} отзывов. Средняя оценка: {avg_rating:.1f}")
                print(f"Получено {feedback_count} отзывов")
                print(f"Средняя оценка: {avg_rating:.1f} из 5")
                
                # Распределение по оценкам
                rating_counts = {}
                for r in range(1, 6):
                    count = sum(1 for rating in ratings if rating == r)
                    rating_counts[r] = count
                    print(f"Оценка {r}/5: {count} отзыв(ов) ({count/len(ratings)*100:.1f}%)")
                
                logging.info(f"Распределение оценок: {rating_counts}")
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