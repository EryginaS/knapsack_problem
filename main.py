import config
import telebot
import os
import shutil
import logging
from logic import xlsx_valid, get_selected_items_list, convert_result_task_to_xls

from collections import defaultdict
import phrases
# сессии пользователей
# state 0- начал диалог 1- должен отправить число (груз) 2 - должен отправить файл xlsx
#  3- ожидает решения 4- могут решить еще одну задачу или выйти
users = defaultdict(dict)

# бот
bot = telebot.TeleBot(config.token)

# стандартная клава
keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard1.row('/help')
keyboard1.row('Начать решать мою задачу')
keyboard1.row('Посмотреть пример')
keyboard1.row('Выйти')

keyboard2 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard2.row('Посмотреть пример')
keyboard2.row('Выйти')

keyboard3 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard3.row('Решить еще одну задачу')
keyboard3.row('Выйти')


# отправка документа
def send_doc_exemple(message, name_file, text, reply_markup_= None):
    f = open( name_file, 'rb')
    bot.send_document(chat_id=message.chat.id,
                      data=f,
                      caption=text,
                      reply_markup = reply_markup_)

# отправка картинки
def send_img(message, path):
    f = open(path, 'rb')
    bot.send_photo(message.chat.id, f, caption='График Ценности для площади\веса с набором элементов')

# старт
@bot.message_handler(commands=['start'], content_types=["text"])
def hello_message(message): # Название функции не играет никакой роли
    users[message.chat.id] = {'state' : 0}
    bot.send_message(message.chat.id,
                     phrases.hello_text,
                     reply_markup=keyboard1)

# отправка клавиатуры
@bot.message_handler(commands=['help'], content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли
    bot.send_message(message.chat.id,
                     phrases.help_text,
                     reply_markup=keyboard1)

# обработка текста
@bot.message_handler(content_types=['text'])
def send_text(message):

    # в случае если юзер не нажал старт
    if not users[message.chat.id]:
        users[message.chat.id] = {'state': 0}
        bot.send_message(message.chat.id,
                         phrases.hello_text,
                         reply_markup=keyboard1)

    elif message.text.lower() == 'выйти':
        bot.send_message(message.chat.id,
                         phrases.bye_text)
        users.pop(message.chat.id)
    #  если мы ожидаем грузоподьемность
    # отправит пример
    elif message.text.lower() == 'посмотреть пример':
        send_doc_exemple(message,
                        os.path.join('examples', 'example.xlsx'),
                        phrases.example_text )
    #  это когда юзер нажал начать решать задачу
    elif message.text.lower() == 'начать решать мою задачу' or message.text.lower() == 'решить еще одну задачу':
        users[message.chat.id]['state'] = 1
        bot.send_message(message.chat.id,
                         phrases.start_task_text)

    elif users[message.chat.id]['state'] == 0:
        bot.send_message(message.chat.id,
                         phrases.forgot_what_do_text,
                         reply_markup=keyboard1)

    elif users[message.chat.id]['state'] == 1:
        try:
            users[message.chat.id]['carrying_capacity'] = int(message.text)
            users[message.chat.id]['state'] = 2
            bot.send_message(message.chat.id,
                             phrases.carrying_capacity_text,
                             reply_markup=keyboard2)
        except Exception as e:
            bot.send_message(message.chat.id,
                             phrases.error_capacity_text)

    # если юзер должен был прислать документ априслал текс или хуй знает что
    elif users[message.chat.id]['state'] == 2:
        bot.send_message(message.chat.id,
                         phrases.error_file_text)
    else:
        bot.send_message(message.chat.id,
                         phrases.unknow_comand_text)


@bot.message_handler(content_types=['document'])
def handle_docs_photo(message):

    if not users[message.chat.id] or users[message.chat.id]['state'] != 2:
        bot.send_message(message.chat.id,
                         phrases.user_send_file_without_capacity)
        return

    try:
        # информация о файле
        file_info = bot.get_file(message.document.file_id)
        # сам файл
        downloaded_file = bot.download_file(file_info.file_path)
        # махинации с путями
        name_dir = os.path.join('docs', str(message.chat.id))
        os.mkdir(name_dir)
        src = os.path.join(name_dir,  message.document.file_name)

        #  сохранение файла на диск
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        users[message.chat.id]['data_from_doc'], valid, mes = xlsx_valid(src)

        if valid:
            users[message.chat.id]['file_name'] = src
            users[message.chat.id]['state'] = 3
            bot.reply_to(message, phrases.message_about_save_file_xlsx)
            stuff = get_selected_items_list(users[message.chat.id]['data_from_doc'],
                                            users[message.chat.id]['carrying_capacity'],
                                            name_dir)

            df_for_answer = convert_result_task_to_xls(users[message.chat.id]['data_from_doc'],stuff)
            path_to_doc_for_answer = os.path.join(name_dir, "output.xlsx")
            df_for_answer.to_excel(path_to_doc_for_answer)

            send_doc_exemple(message, path_to_doc_for_answer,
                             phrases.result_task_text,
                             keyboard3)

            send_img(message,
                     os.path.join(name_dir, 'mygraph.png'))

            shutil.rmtree(name_dir)
            users[message.chat.id] =  {}
            users[message.chat.id]['state'] = 4

        else:
            bot.reply_to(message, f"Ваш файл не прошел валидацию! {mes}")
            shutil.rmtree(name_dir)

    except Exception as e:
        logging.log(1, e)


if __name__ == '__main__':
     bot.infinity_polling()

