from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import requests
import json

def get_imt_id(product_url):
    # Настройка Selenium WebDriver с пользовательским агентом для ПК
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Открыть браузер в полноэкранном режиме
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

                # Извлечение imt_id из URL
                if "imtId=" in feedback_url:
                    imt_id = feedback_url.split("imtId=")[-1]
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
    versions = ["v1", "v2", "v3"]
    for version in versions:
        url = f"https://feedbacks1.wb.ru/feedbacks/{version}/{imt_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data:  # Проверяем, что данные не пустые
                    print(f"Reviews fetched successfully from {version}")
                    return data
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from {version}")
        else:
            print(f"Failed to fetch reviews from {version}. Status code: {response.status_code}")
    
    print("No reviews found in any API version.")
    return None

def save_reviews_to_file(reviews, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(reviews, file, ensure_ascii=False, indent=4)
        print(f"Reviews saved to {filename}")
    except Exception as e:
        print(f"Error saving reviews to file: {e}")

# Пример использования
product_url = "https://www.wildberries.ru/catalog/172152349/detail.aspx"  # Замените на нужный URL товара
imt_id = get_imt_id(product_url)

if imt_id:
    reviews = get_reviews(imt_id)
    if reviews:
        save_reviews_to_file(reviews, "reviews.json")