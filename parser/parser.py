import os
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

def get_text(element, selector):
    try:
        return element.find_element(By.CSS_SELECTOR, selector).text.replace('\n', ' ').strip()
    except:
        return ""

def get_array_texts(element, selector):
    try:
        elements = element.find_elements(By.CSS_SELECTOR, selector)
        return ", ".join([e.text.strip() for e in elements if e.text])
    except:
        return ""
    
def parse(max_pages):
    driver = webdriver.Safari()
    driver.maximize_window()
    
    base_url = "https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&location%5B0%5D=1&offer_type=flat&region=1&p="
    headers = ['Ссылка', 'Заголовок', 'Срок сдачи', 'Метро', 'Точный адрес', 'Цена', 'Цена за м²', 'Описание']
    
    with open('data/data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        
        for page in range(1, max_pages + 1):
            driver.get(f"{base_url}{page}")
            time.sleep(1)
            
            cards = driver.find_elements(By.CSS_SELECTOR, "article[data-name='CardComponent']")
            
            for card in cards:
                try:
                    link = card.find_element(By.CSS_SELECTOR, "a[href*='/sale/flat/']").get_attribute("href")
                except:
                    continue 

                data = {
                    'Ссылка': link,
                    'Заголовок': get_text(card, "[data-mark='OfferTitle']"),
                    'Срок сдачи': get_text(card, "[data-mark='OfferSubtitle']"),
                    'Метро': get_text(card, "[data-name='SpecialGeo']"),
                    'Точный адрес': get_array_texts(card, "[data-name='GeoLabel']"),
                    'Цена': get_text(card, "[data-testid='offer-discount-new-price'], [data-mark='MainPrice']"), 
                    'Цена за м²': get_text(card, "[data-mark='PriceInfo']"),
                    'Описание': get_text(card, "[data-name='Description']")
                }
                
                writer.writerow(data)
                
            file.flush()
                
    driver.quit()
