import telebot
from telebot import types
from moex_exchange import MoexExchange

# Creating MoexExchange class
moex = MoexExchange()

# Creating telebot class
bot = telebot.TeleBot("6798743608:AAH605Riu5divstJJMlOtoJ5oGrj2A761gM")

# Dict for collecting user data for request
dataset = {}


# Processing /start command
@bot.message_handler(commands=['start'])
def start(message):
    """
    Function, that processes first bot launch and re-launch
    :param message: command
    :type message: str
    :return: None
    :rtype: None
    :raises:
    """
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text='Сделать запрос', callback_data='request')
    markup.add(button)
    bot.send_message(message.chat.id, 'Welcome to EDP BOT! Press button below', reply_markup=markup)

# Processing inline-button press
@bot.callback_query_handler(func=lambda call: call.data == 'request')
def request(call):
    """
    Function, that gets request type
    :param call: telebot method for handle InlineKeyBoard responses
    :type call: Any
    :return: None
    :rtype: None
    :raises:
    """
    bot.send_message(call.message.chat.id, 'Укажите тип запроса:')
    bot.send_message(call.message.chat.id, '1. exchange_stream: send_exchange_data\n'
                                           '2. klines_stream: send_klines\n'
                                           '3. ticker_stream: send_ticker_data\n'
                                           '4. moex_stream: get_ticker_data')
    bot.register_next_step_handler(call.message, process_stream_function)

def process_stream_function(message):
    """
    Function, that gets stream_function param for request
    :param message: user reply for stream_function
    :type message: str
    :return: None
    :rtype: None
    :raises:
    """
    stream_function = message.text.strip()
    if stream_function not in ['exchange_stream', 'klines_stream', 'ticker_stream', 'moex_stream']:
        bot.send_message(message.chat.id, 'Неверный тип запроса. Пожалуйста, введите еще раз.')
        bot.register_next_step_handler(message, process_stream_function)
    else:
        dataset["stream_function"] = stream_function
        bot.send_message(message.chat.id, 'Введите интересующий вас тикер криптовалюты или акции с биржи MOEX')
        bot.register_next_step_handler(message, process_ticker)

def process_ticker(message):
    """
    Function, that gets ticker param for request
    :param message: user reply for ticker
    :type message: str
    :return: None
    :rtype: None
    :raises:
    """
    ticker = message.text.strip()
    if not ticker.isalpha():
        bot.send_message(message.chat.id, 'Некорректный тикер. Пожалуйста, введите еще раз.')
        bot.register_next_step_handler(message, process_ticker)
    else:
        dataset["ticker"] = ticker
        bot.send_message(message.chat.id, 'Введите количество обновлений данных по тикеру')
        bot.register_next_step_handler(message, process_count)

def process_count(message):
    """
    Function, that gets count param for request
    :param message: user reply for count
    :type message: int
    :return: None
    :rtype: None
    :raises:
    """
    count = message.text.strip()
    if not count.isdigit():
        bot.send_message(message.chat.id, 'Некорректное количество. Пожалуйста, введите еще раз.')
        bot.register_next_step_handler(message, process_count)
    else:
        dataset["count"] = count
        bot.send_message(message.chat.id, 'Введите интервал, в котором вам будут приходить обновления в секундах')
        bot.register_next_step_handler(message, process_timeout)


def process_timeout(message):
    """
    Function, that gets timeout param for request
    :param message: user reply for timeout
    :type message: int
    :return: None
    :rtype: None
    :raises:
    """
    timeout = message.text.strip()
    if not timeout.isdigit():
        bot.send_message(message.chat.id, 'Некорректный интервал. Пожалуйста, введите еще раз.')
        bot.register_next_step_handler(message, process_timeout)
    else:
        dataset["timeout"] = timeout
        # Все параметры получены, выполняем нужные действия
        # .
        show_user(message, dataset)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """
    Function, that gets yes/no answer for correction of dataset
    :param call: telebot method for handle InlineKeyBoard responses
    :type call: Any
    :return: None
    :rtype: None
    :raises:
    """
    if call.data == 'yes':
        work_func()
    elif call.data == 'no':
        bot.send_message(call.message.chat.id, "Введите /start и заново укажите данные")
    else:
        bot.send_message(call.message.chat.id, "Неверный ответ. Нажмите 'Да' или 'Нет'")


def show_user(message, dataset):
    """
    Function, that shows input data for user and makes buttons for approve or rejection
    :param message: user last message
    :type message: Any
    :param dataset: dict with data for response (stream_type)
    :type dataset: dict
    :return: None
    :rtype: None
    :raises:
    """
    text = f'Параметры запроса:\n\nТип запроса: {dataset["stream_function"]}\nТикер: {dataset["ticker"]}\nКоличество обновлений: {dataset["count"]}\nИнтервал: {dataset["timeout"]} секунд\n\nКорректны ли введенные данные?'
    markup = telebot.types.InlineKeyboardMarkup()
    button_yes = telebot.types.InlineKeyboardButton(text='Да', callback_data='yes')
    button_no = telebot.types.InlineKeyboardButton(text='Нет', callback_data='no')
    markup.add(button_yes, button_no)
    bot.send_message(message.chat.id, text, reply_markup=markup)


def work_func():
    print(11)


"""
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Добро пожаловать! Выберите одну из кнопок:")

    # Создаем и отправляем inline-клавиатуру с двумя кнопками
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="Получить данные по тикеру", callback_data="get_ticker_info")
    button2 = types.InlineKeyboardButton(text="Получить график по тикеру", callback_data="plot_price_chart")
    keyboard.add(button1, button2)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "get_ticker_info":
        bot.send_message(call.message.chat.id, "Введите тикер:")
        bot.register_next_step_handler(call.message, get_ticker_info)
    elif call.data == "plot_price_chart":
        bot.send_message(call.message.chat.id, "Введите тикер:")
        bot.register_next_step_handler(call.message, plot_price_chart)
    else:
        bot.send_message(call.message.chat.id, "Некорректная команда. Пожалуйста, выберите одну из кнопок.")


def get_ticker_info(message):
    if message.text.isalpha():
        ticker = message.text
    else:
        pass
    def send_ticker_info():
        pe_ratio, current_price, market_cap = moex.get_ticker_info(ticker)

        if pe_ratio is not None:
            response = f"Данные по тикеру {ticker}:\n\nP/E ratio: {pe_ratio}\nТекущая цена: {current_price}\nMarketCap: {market_cap}"
        else:
            response = f"Не удалось получить данные по тикеру {ticker}"

        bot.send_message(message.chat.id, response)

    # Отправляем данные по тикеру после ввода
    bot.send_chat_action(message.chat.id, 'typing')
    send_ticker_info()


def plot_price_chart(message):
    ticker = message.text

    def send_price_chart():
        moex.plot_price_chart(ticker)

        # Отправляем картинку с графиком
        with open(f"{ticker}_chart.png", "rb") as chart:
            bot.send_photo(message.chat.id, chart)

    # Отправляем график по тикеру после ввода
    bot.send_chat_action(message.chat.id, 'typing')
    send_price_chart()
"""

# Запускаем бота
bot.polling()