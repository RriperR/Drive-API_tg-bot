import telebot
import os
from pydub import AudioSegment
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from datetime import datetime
from dotenv import load_dotenv

bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

# Авторизация и создание объекта Google Drive
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Аутентификация пользователя в браузере
drive = GoogleDrive(gauth)


# Старт бота
@bot.message_handler(commands=['start'])
def main(message):
    welcome_text = 'Привет! Отправьте мне голосовое сообщение, и я сохраню его в Google Drive.'
    bot.send_message(message.chat.id, welcome_text)


# Функция для создания папки на Google Drive с текущей датой и временем
def create_drive_folder():
    folder_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']


# Функция для загрузки файла на Google Drive
def upload_file_to_drive(file_name, file_path, folder_id):
    file_drive = drive.CreateFile({'title': file_name, 'parents': [{'id': folder_id}]})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()


# Обработка и отправка голосового сообщения
@bot.message_handler(content_types=['voice'])
def get_voice(message):
    # Получение и скачивание голосового файла
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохранение голосового сообщения в формате .ogg
    voice_file_name = "voice_message.ogg"
    with open(voice_file_name, "wb") as new_file:
        new_file.write(downloaded_file)

    # Конвертация в формат WAV (при необходимости)
    audio = AudioSegment.from_ogg(voice_file_name)
    wav_file_name = "voice_message.wav"
    audio.export(wav_file_name, format="wav")

    # Создание папки на Google Drive и загрузка оригинального аудиофайла
    folder_id = create_drive_folder()
    upload_file_to_drive(voice_file_name, voice_file_name, folder_id)

    # Отправка подтверждения пользователю
    bot.send_message(message.chat.id, "Ваше голосовое сообщение сохранено на Google Drive.")

    # Удаление временных файлов с локального компьютера
    os.remove(voice_file_name)
    os.remove(wav_file_name)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.send_message(message.chat.id, "Пожалуйста, отправьте голосовое сообщение.")


bot.polling(none_stop=True)
