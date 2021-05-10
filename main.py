import config
import telebot
from telebot import types
import re
import os
import logging
from bag_task import xlsx_valid

from collections import defaultdict
# сессии пользователей
# state 0- начал диалог 1- должен отправить число (груз) 2 - должен отправить файл xlsx
#  3- ожидает решения
users = defaultdict(dict)

# бот
bot = telebot.TeleBot(config.token)

# стандартная клава
keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard1.row('/help')
keyboard1.row('Начать решать мою задачу')
keyboard1.row('Посмотреть пример')

keyboard2 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard2.row('Посмотреть пример')

# отправка примера
def send_doc_exemple(message):
    f = open('exemples/exemple.xlsx', 'rb')
    bot.send_document(message.chat.id, f, None)


# старт
@bot.message_handler(commands=['start'], content_types=["text"])
def hello_message(message): # Название функции не играет никакой роли
    users[message.chat.id] = {'state' : 0}
    bot.send_message(message.chat.id, 'Привет,  я бот, который решает задачу о наполении рюкзака 🎒.\n'
                                      'Узнай, как работает бот и как решить свою задачу /help', reply_markup=keyboard1)

# отправка клавиатуры
@bot.message_handler(commands=['help'], content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли
    bot.send_message(message.chat.id, 'Правила пользования.', reply_markup=keyboard1)

# обработка текста
@bot.message_handler(content_types=['text'])
def send_text(message):

    # в случае если юзер не нажал старт
    if not users[message.chat.id]:
        users[message.chat.id] = {'state': 0}
        bot.send_message(message.chat.id, 'Привет,  я бот, который решает задачу о наполении рюкзака 🎒.\n'
                                          'Узнай, как работает бот и как решить свою задачу /help.'
                                          '\n Если ты уже знаешь, как пользоваться ботом, жми'
                                          'на кнопку "начать решать мою задачу".',
                         reply_markup=keyboard1)


    #  если мы ожидаем грузоподьемность
    elif users[message.chat.id]['state'] == 1:
        try:
            users[message.chat.id]['carrying_capacity'] = int(message.text)
            users[message.chat.id]['state'] = 2
            bot.send_message(message.chat.id, 'Отправьте xlsx/ xls документ. В котором первый столбец- имя предмета, второй -его вес (в кг), третий - ценность от 0 до 100.'
                                              '\n Также можно посмотреть пример файла, просто нажав на "Посмотреть пример"', reply_markup=keyboard2)
        except Exception as e:
            bot.send_message(message.chat.id, 'Вы отправили не то, что ожидалось. '
                                              '\n Ожидается число (грузопоъемность в кг).')
    # отправит пример
    elif message.text.lower() == 'посмотреть пример':
        send_doc_exemple(message)

    # если юзер должен был прислать документ априслал текс или хуй знает что
    elif users[message.chat.id]['state'] == 2:
        bot.send_message(message.chat.id, 'Вы отправили не то, что ожидалось. '
                                          '\n Ожидается файл!')
    #  это когда юзер нажал начать решать задачу
    elif message.text.lower() == 'начать решать мою задачу':
        users[message.chat.id]['state'] = 1
        bot.send_message(message.chat.id, 'Пожалуйста, введите грузоподъемность (в кг).')

    elif message.text.lower() == 'пока':
        bot.send_message(message.chat.id, f'Прощай пользователь.')
    else:
        bot.send_message(message.chat.id, 'Я не знаю такой команды')


@bot.message_handler(content_types=['document'])
def handle_docs_photo(message):
    try:
        # информация о файле
        file_info = bot.get_file(message.document.file_id)
        # сам файл
        downloaded_file = bot.download_file(file_info.file_path)
        # махинации с путями
        name_dir = 'docs/'+ str(message.chat.id)
        os.mkdir(name_dir)
        src = os.path.join(name_dir,  message.document.file_name)

        #  сохранение файла на диск
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        users[message.chat.id]['data_from_doc'], valid, mes = xlsx_valid(src)
        if valid:
            users[message.chat.id]['file_name'] = src
            users[message.chat.id]['state'] = 3
            bot.reply_to(message, "Пожалуй, я сохраню это. \nПожалуйста подождите, ваша задача решается.")
            # TODO: передать в вфункцию users[message.chat.id]['carrying_capacity'], users[message.chat.id]['data_from_doc']
            # TODO: сообщение отпарвить
            # TODO: удалять папку юзера
            # TODO: статус юзера 0
        else:
            bot.reply_to(message, f"Ваш файл не прошел валидацию! {mes}")
            # TODO: удалять папку юзера
    except Exception as e:
        bot.reply_to(message, e)


if __name__ == '__main__':
     bot.infinity_polling()

