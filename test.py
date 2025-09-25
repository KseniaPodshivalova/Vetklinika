import sqlite3
import base64
import requests

DATABASE_FILE = "mydatabase.db"

# Функция для скачивания изображения и преобразования в BLOB
def download_image_to_blob(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        image_data = response.content
        return image_data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании изображения {url}: {e}")
        return None


def sql_connection():
    con = None
    try:
        con = sqlite3.connect(DATABASE_FILE)
        return con
    except sqlite3.Error as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None

def create_table(con):
    cursor = con.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Pacienti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            image BLOB,
            type TEXT,
            date TEXT,
            creator TEXT,
            address TEXT,
            phone INTEGER
        )
    """)
    con.commit()


def insert_patient(name, image_url, type, date, creator, address, phone):
    con = sql_connection()
    if con is None:
        print("Не удалось подключиться к базе данных")
        return

    try:
        image_blob = download_image_to_blob(image_url)
        if image_blob is None:
            print(f"Не удалось скачать изображение для {name}")
            return

        cursor = con.cursor()
        cursor.execute("""
            INSERT INTO Pacienti (name, image, type, date, creator, address, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, image_blob, type, date, creator, address, phone))
        con.commit()
        print(f"Пациент {name} успешно добавлен в базу данных.")

    except sqlite3.Error as e:
        print(f"Ошибка при добавлении пациента: {e}")
        con.rollback()

    finally:
        if con:
            con.close()


if __name__ == "__main__":
    con = sql_connection()
    if con:
        create_table(con)
        con.close()

    patients_data = [
        {
            "name": "КОЛЯ ПОТАПОВ",
            "image_url": "https://avatars.mds.yandex.net/i?id=472c1e9cc742abfd5d50eb92be4a6b58_l-4902992-images-thumbs&n=13",
            "type": "ПЕТУХ",
            "date": "07.09.2000",
            "creator": "Денис Перетягин",
            "address": "Ленина 16а 326",
            "phone": 89005848756
        },
        {
            "name": "сенька",
            "image_url": "https://avatars.mds.yandex.net/i?id=53608c49dc2899a47304164dbc6f5c19f4a06e2e1dd8ba9d-12363187-images-thumbs&n=13",
            "type": "чертосвин",
            "date": "08.07.2020",
            "creator": "Денис Перетягин",
            "address": "Ленина 16а 326",
            "phone": 89435848756
        },
        {
            "name": "егор",
            "image_url": "https://a.d-cd.net/8AAAAgJ5HOA-1920.jpg",
            "type": "чертосвин",
            "date": "02.01.2019",
            "creator": "Денис Перетягин",
            "address": "Ленина 16а 416",
            "phone": 89874238685
        },
        {
            "name": "слава",
            "image_url": "https://avatars.mds.yandex.net/i?id=b4a6a04772917093825f343b0b24b1a9_l-4118916-images-thumbs&n=13",
            "type": "свинка",
            "date": "01.01.2023",
            "creator": "Денис Перетягин",
            "address": "Ленина 16а 327",
            "phone": 8965349765
        },
        {
            "name": "ваня",
            "image_url": "https://avatars.mds.yandex.net/i?id=119a3a44fe6645f773bda6ba3d43a808_l-4571216-images-thumbs&n=13",
            "type": "псинка",
            "date": "01.04.2020",
            "creator": "Денис Перетягин",
            "address": "Ленина 16а 303",
            "phone": 89054388567
        }
    ]

    # Добавляем данные в базу данных
    for patient_data in patients_data:
        insert_patient(
            patient_data["name"],
            patient_data["image_url"],
            patient_data["type"],
            patient_data["date"],
            patient_data["creator"],
            patient_data["address"],
            patient_data["phone"]
        )
    print("База данных заполнена.")