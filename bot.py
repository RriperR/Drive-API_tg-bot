import telebot
from googleapiclient.discovery import build
from fpdf import FPDF
import os
from io import BytesIO
from google.oauth2 import service_account
from dotenv import load_dotenv
from googleapiclient.http import MediaIoBaseUpload

# Настройка Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'q-bot.json'  # Укажите ваш JSON-файл с сервисным аккаунтом
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Инициализация бота
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Ассалам Алейкум!")


# Функция для создания PDF с фото и текстом
def create_pdf(text, image_data):
    pdf = FPDF()
    pdf.add_page()

    # Добавляем текст в PDF
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.ln(10)

    # Сохраняем фото временно в памяти и добавляем его в PDF
    with open("temp_image.jpg", "wb") as temp_img:
        temp_img.write(image_data)
    pdf.image("temp_image.jpg", x=10, y=pdf.get_y() + 10, w=100)

    # Создаем объект BytesIO для хранения PDF в памяти
    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))  # Выводим PDF в объект BytesIO
    pdf_output.seek(0)  # Возвращаем указатель в начало файла
    os.remove("temp_image.jpg")  # Удаляем временный файл изображения

    return pdf_output



# Функция для загрузки PDF на Google Диск
def upload_to_google_drive(file_data, file_name, folder_id='1G-Db6gF7aGppr4U1mfJR6blYbQYyRAVl'):
    file_metadata = {
        'name': file_name,
        'mimeType': 'application/pdf',
    }
    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaIoBaseUpload(file_data, mimetype='application/pdf', resumable=True)

    try:
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get("id")
    except Exception as e:
        raise e


# Обработчик получения фото и сохранения его на Google Диск в PDF
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id

    # Получаем file_id фото и скачиваем его
    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Текст, который будет добавлен в PDF
    text = f"Photo from user {message.from_user.username or chat_id}"

    # Имя файла PDF
    file_name = f"{chat_id}_photo.pdf"

    # Создаем PDF с фото и текстом
    pdf_file = create_pdf(text, downloaded_file)

    # Загружаем PDF на Google Диск
    try:
        file_id = upload_to_google_drive(pdf_file, file_name)
        bot.send_message(chat_id, "Ваше фото и текст успешно сохранены на Google Диске в формате PDF!")
    except Exception as e:
        bot.send_message(chat_id, f"Не удалось загрузить PDF на Google Диск: {e}")

    pdf_file.close()  # Закрываем буфер памяти после загрузки

bot.polling(none_stop=True)