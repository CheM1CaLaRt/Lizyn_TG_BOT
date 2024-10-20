import re
import subprocess
from config import TG_TOKEN
import telebot
import yt_dlp
import os

bot = telebot.TeleBot(TG_TOKEN)

# Словарь для хранения данных пользователей
user_data = {}


# Обработчик команды /start
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
                 "Привет! Отправь команду /vk, чтобы скачать видео с ВКонтакте, или команду /vkmp3 для скачивания аудио в формате MP3.")


# Обработчик команды /vk для скачивания видео
@bot.message_handler(commands=['vk'])
def ask_for_link(message):
    msg = bot.reply_to(message, "Пожалуйста, отправьте ссылку на видео ВКонтакте.")
    bot.register_next_step_handler(msg, ask_for_quality)


# Запрос качества у пользователя
def ask_for_quality(message):
    video_url = message.text
    chat_id = message.chat.id

    # Проверка правильности ссылки
    if not re.match(r'https?://(www\.)?vk\.com/video', video_url):
        bot.reply_to(message, "Неверная ссылка на видео ВКонтакте. Попробуйте снова.")
        return

    user_data[chat_id] = {'video_url': video_url}  # Сохраняем ссылку на видео

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('720p', '480p', '360p')

    msg = bot.reply_to(message, "Выберите качество видео:", reply_markup=markup)
    bot.register_next_step_handler(msg, download_video)


# Функция для загрузки видео
def download_video(message):
    quality = message.text
    chat_id = message.chat.id

    # Если выбрано неверное качество, выдаем предупреждение
    if quality not in ['720p', '480p', '360p']:
        bot.reply_to(message, "Неверное качество. Попробуйте снова.")
        return

    video_url = user_data[chat_id].get('video_url')  # Получаем ссылку из данных пользователя

    ydl_opts = {
        'format': f'bestvideo[height<={quality[:-1]}]+bestaudio',
        'outtmpl': f'{chat_id}_video.%(ext)s',  # Имя файла зависит от chat_id
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        video_file = f'{chat_id}_video.mp4'

        if os.path.exists(video_file):
            file_size = os.path.getsize(video_file)
            max_size = 50 * 1024 * 1024  # 50 MB

            if file_size > max_size:
                bot.reply_to(message, "Файл слишком большой для отправки через Telegram. Сжимаем видео...")

                # Сжатие видео с использованием ffmpeg
                compressed_file = f'{chat_id}_video_compressed.mp4'
                ffmpeg_command = [
                    'ffmpeg', '-i', video_file, '-vcodec', 'libx264', '-crf', '28', compressed_file
                ]

                # Выполняем команду
                subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                if os.path.exists(compressed_file):
                    compressed_file_size = os.path.getsize(compressed_file)
                    if compressed_file_size > max_size:
                        bot.reply_to(message, "Сжатое видео все равно слишком большое для отправки через Telegram.")
                        os.remove(compressed_file)
                    else:
                        with open(compressed_file, 'rb') as video:
                            bot.send_video(message.chat.id, video)
                        os.remove(compressed_file)

            else:
                with open(video_file, 'rb') as video:
                    bot.send_video(message.chat.id, video)
                os.remove(video_file)

        else:
            bot.reply_to(message, "Произошла ошибка: видео не удалось скачать.")

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")
        print(f"Ошибка при скачивании видео: {str(e)}")  # Логирование ошибки

    # Очистка данных пользователя после обработки
    user_data.pop(chat_id, None)


# Обработчик команды /vkmp3 для скачивания аудио в формате MP3
@bot.message_handler(commands=['vkmp3'])
def ask_for_link_mp3(message):
    msg = bot.reply_to(message, "Пожалуйста, отправьте ссылку на видео ВКонтакте для извлечения аудио.")
    bot.register_next_step_handler(msg, download_mp3)


# Функция для скачивания аудио в формате MP3
def download_mp3(message):
    video_url = message.text
    chat_id = message.chat.id

    # Проверка правильности ссылки
    if not re.match(r'https?://(www\.)?vk\.com/video', video_url):
        bot.reply_to(message, "Неверная ссылка на видео ВКонтакте. Попробуйте снова.")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{chat_id}_audio.%(ext)s',  # Имя файла зависит от chat_id
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',  # Качество MP3
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        audio_file = f'{chat_id}_audio.mp3'

        if os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            max_size = 50 * 1024 * 1024  # 50 MB

            if file_size > max_size:
                bot.reply_to(message, "Файл слишком большой для отправки через Telegram.")
                os.remove(audio_file)
            else:
                with open(audio_file, 'rb') as audio:
                    bot.send_audio(message.chat.id, audio)
                os.remove(audio_file)
        else:
            bot.reply_to(message, "Произошла ошибка: аудио не удалось скачать.")

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")
        print(f"Ошибка при скачивании аудио: {str(e)}")  # Логирование ошибки


bot.polling()
