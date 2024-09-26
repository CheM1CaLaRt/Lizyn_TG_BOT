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
    bot.reply_to(message, "Привет! Отправь команду /vk, чтобы скачать видео с ВКонтакте или /youtube для скачивания видео с YouTube.")

# Обработчик команды /vk
@bot.message_handler(commands=['vk'])
def ask_for_vk_link(message):
    msg = bot.reply_to(message, "Пожалуйста, отправьте ссылку на видео ВКонтакте.")
    bot.register_next_step_handler(msg, ask_for_vk_quality)

# Обработчик команды /youtube
@bot.message_handler(commands=['youtube'])
def ask_for_youtube_link(message):
    msg = bot.reply_to(message, "Пожалуйста, отправьте ссылку на видео YouTube.")
    bot.register_next_step_handler(msg, ask_for_youtube_quality)

# Запрос качества у пользователя для VK
def ask_for_vk_quality(message):
    video_url = message.text
    chat_id = message.chat.id
    user_data[chat_id] = {'video_url': video_url, 'platform': 'vk'}

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('720p', '480p', '360p')

    msg = bot.reply_to(message, "Выберите качество видео:", reply_markup=markup)
    bot.register_next_step_handler(msg, download_video)

# Запрос качества у пользователя для YouTube
def ask_for_youtube_quality(message):
    video_url = message.text
    chat_id = message.chat.id
    user_data[chat_id] = {'video_url': video_url, 'platform': 'youtube'}

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('720p', '480p', '360p')

    msg = bot.reply_to(message, "Выберите качество видео:", reply_markup=markup)
    bot.register_next_step_handler(msg, download_video)

# Функция для загрузки видео
def download_video(message):
    quality = message.text
    chat_id = message.chat.id
    video_url = user_data[chat_id].get('video_url')
    platform = user_data[chat_id].get('platform')

    ydl_opts = {
        'format': f'bestvideo[height<={quality[:-1]}]+bestaudio/best',
        'outtmpl': f'{chat_id}_video.mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        video_file = f'{chat_id}_video.mp4'

        if os.path.exists(video_file):
            file_size = os.path.getsize(video_file)
            max_size = 50 * 1024 * 1024  # 50 MB

            if file_size > max_size:
                bot.reply_to(message, "Файл слишком большой для отправки через Telegram.")
                os.remove(video_file)
            else:
                with open(video_file, 'rb') as video:
                    bot.send_video(message.chat.id, video)
                os.remove(video_file)
        else:
            bot.reply_to(message, "Произошла ошибка: видео не удалось скачать.")

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

    # Очистка данных пользователя после обработки
    user_data.pop(chat_id, None)

bot.polling()
