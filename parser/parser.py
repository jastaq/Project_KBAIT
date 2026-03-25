import os
import csv
import time
import requests
import io
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from minio import Minio


def get_text(element, selector):
    try:
        return (
            element.find_element(By.CSS_SELECTOR, selector)
            .text.replace("\n", " ")
            .strip()
        )
    except:
        return ""


def get_array_texts(element, selector):
    try:
        elements = element.find_elements(By.CSS_SELECTOR, selector)
        return ", ".join([e.text.strip() for e in elements if e.text])
    except:
        return ""


s3 = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="SuperSecretPassword123",
    secure=False,
)
if not s3.bucket_exists("cian-images"):
    s3.make_bucket("cian-images")


def parse(max_pages):
    driver = webdriver.Safari()
    driver.maximize_window()

    base_url = "https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&location%5B0%5D=1&offer_type=flat&region=1&p="
    headers = [
        "Ссылка",
        "Фото",
        "Заголовок",
        "Срок сдачи",
        "Метро",
        "Точный адрес",
        "Цена",
        "Цена за м²",
        "Описание",
    ]

    with open("data/data.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()

        for page in range(1, max_pages + 1):
            driver.get(f"{base_url}{page}")
            time.sleep(1)

            cards = driver.find_elements(
                By.CSS_SELECTOR, "article[data-name='CardComponent']"
            )

            for card in cards:
                try:
                    link = card.find_element(
                        By.CSS_SELECTOR, "a[href*='/sale/flat/']"
                    ).get_attribute("href")
                except:
                    continue

                s3_uri = ""
                try:
                    img_url = card.find_element(
                        By.CSS_SELECTOR, "picture img"
                    ).get_attribute("src")
                    img_name = img_url.split("/")[-1]
                    img_bytes = requests.get(img_url, timeout=5).content
                    s3.put_object(
                        "cian-images", img_name, io.BytesIO(img_bytes), len(img_bytes)
                    )
                    s3_uri = f"s3://cian-images/{img_name}"
                except:
                    pass

                data = {
                    "Ссылка": link,
                    "Фото": s3_uri,
                    "Заголовок": get_text(card, "[data-mark='OfferTitle']"),
                    "Срок сдачи": get_text(card, "[data-mark='OfferSubtitle']"),
                    "Метро": get_text(card, "[data-name='SpecialGeo']"),
                    "Точный адрес": get_array_texts(card, "[data-name='GeoLabel']"),
                    "Цена": get_text(
                        card,
                        "[data-testid='offer-discount-new-price'], [data-mark='MainPrice']",
                    ),
                    "Цена за м²": get_text(card, "[data-mark='PriceInfo']"),
                    "Описание": get_text(card, "[data-name='Description']"),
                }

                writer.writerow(data)

            file.flush()

    driver.quit()
