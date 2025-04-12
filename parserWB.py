from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import requests
import json

def get_product_url(article):
    """
    Формирует URL товара на WildBerries по его артикулу
    """
    return f"https://www.wildberries.ru/catalog/{article}/detail.aspx"

def get_imt_id(product_url):
    # Настройка Selenium WebDriver с пользовательским агентом для ПК
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1366,768")  # Фиксированное разрешение для ПК
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")  # User-Agent для ПК

    driver = webdriver.Chrome(options=chrome_options)  # Убедитесь, что у вас установлен ChromeDriver
    driver.get(product_url)

    # Прокрутка страницы вниз с ожиданием появления кнопки
    try:
        wait = WebDriverWait(driver, 40)  # Увеличиваем время ожидания до 40 секунд
        for _ in range(10):  # Пробуем прокрутить страницу до 10 раз
            time.sleep(2)  # Ждем, чтобы элементы прогрузились
            driver.execute_script("window.scrollBy(0, 500);")  # Прокручиваем вниз на 500px
            try:
                button = driver.find_element(By.CSS_SELECTOR, "a.btn-base.comments__btn-all")
                feedback_url = button.get_attribute("href")
                driver.quit()

                # Извлечение imt_id из URL и очистка от дополнительных параметров
                if "imtId=" in feedback_url:
                    # Извлекаем только число imt_id
                    imt_id_with_params = feedback_url.split("imtId=")[-1]
                    # Очищаем от других параметров, если они есть (например, &size=35087411)
                    imt_id = imt_id_with_params.split("&")[0]
                    print(f"Extracted imt_id: {imt_id}")
                    return imt_id
                else:
                    print("imt_id not found in the URL.")
                    return None
            except Exception:
                pass  # Если кнопка не найдена, продолжаем прокручивать
        print("Button 'Смотреть все отзывы' not found after scrolling.")
        driver.quit()
        return None
    except Exception as e:
        print(f"Error finding the button: {e}")
        driver.quit()
        return None

def get_reviews(imt_id):
    """
    Получает отзывы о товаре по imt_id, перебирая разные хосты и версии API
    """
    # Список хостов API для проверки
    hosts = ["feedbacks.wb.ru", "feedbacks1.wb.ru", "feedbacks2.wb.ru", "feedbacks3.wb.ru"]
    # Список версий API для проверки
    versions = ["v1", "v2", "v3"]
    
    print(f"Попытка получить отзывы для imt_id: {imt_id}")
    
    for host in hosts:
        for version in versions:
            url = f"https://{host}/feedbacks/{version}/{imt_id}"
            print(f"Пробуем URL: {url}")
            
            # Добавляем заголовки для имитации обычного браузера
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://www.wildberries.ru/"
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Проверяем, есть ли в ответе непустые отзывы
                    feedbacks = data.get("feedbacks")
                    feedback_count = data.get("feedbackCount", 0)
                    
                    if feedbacks and isinstance(feedbacks, list) and len(feedbacks) > 0:
                        print(f"Найдены отзывы! URL: {url}")
                        print(f"Количество отзывов: {len(feedbacks)}")
                        return data
                    elif feedback_count > 0:
                        print(f"API указывает, что есть {feedback_count} отзывов, но не возвращает их. URL: {url}")
                    else:
                        print(f"Отзывы не найдены на {url}")
                else:
                    print(f"Ошибка запроса к {url}. Код ответа: {response.status_code}")
            except Exception as e:
                print(f"Ошибка при обращении к {url}: {e}")
    
    print("Отзывы не найдены ни на одном из API-эндпоинтов Wildberries")
    return None

def save_reviews_to_file(reviews, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(reviews, file, ensure_ascii=False, indent=4)
        print(f"Reviews saved to {filename}")
    except Exception as e:
        print(f"Error saving reviews to file: {e}")

def main():
    # Запрашиваем артикул товара у пользователя
    article = input("Введите артикул товара: ")
    
    # Формируем URL товара по артикулу
    product_url = get_product_url(article)
    print(f"Переходим на страницу товара: {product_url}")
    
    # Получаем imt_id из страницы товара
    imt_id = get_imt_id(product_url)
    
    if imt_id:
        # Получаем отзывы по imt_id
        reviews = get_reviews(imt_id)
        if reviews:
            # Создаем уникальное имя файла, включающее артикул товара
            filename = f"reviews_{article}.json"
            # Сохраняем отзывы в файл
            save_reviews_to_file(reviews, filename)
            print(f"Отзывы для артикула {article} сохранены в файл {filename}")
            
            # Запускаем анализатор для обработки полученных отзывов
            try:
                print("Запуск анализа отзывов...")
                import subprocess
                result = subprocess.run(["python", "analyzer.py", filename], 
                                        capture_output=True, text=True, encoding='utf-8')
                if result.returncode == 0:
                    print("Анализ отзывов успешно завершен")
                else:
                    print(f"Ошибка при анализе отзывов: {result.stderr}")
            except Exception as e:
                print(f"Не удалось запустить анализатор: {e}")

# Запускаем основную функцию
if __name__ == "__main__":
    main()