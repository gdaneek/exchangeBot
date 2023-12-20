import telebot
from telebot import types
from websockets.sync.client import connect
import threading
import json
import matplotlib.pyplot as plt
import time


# Creating telebot class
bot = telebot.TeleBot("6798743608:AAH605Riu5divstJJMlOtoJ5oGrj2A761gM")

# Dict for collecting user data for request
dataset = {}

# Dict of dicts for collecting unique requests and updating requests, that was done earlier
ids = {"exchange_stream": {},
       "klines_stream": {},
       "ticker_stream": {}}

# Dict of scriner lists
scriner_lists = {}

# chat_id parametr
chat_ident = ""

IP = "127.0.0.1"

# Processing /start command
@bot.message_handler(commands=['start'])
def start(message):
    """
    Function, that processes first bot launch and re-launch
    :param message: command
    :type message: str
    :return: -
    :rtype: None
    :raises:
    """
    global chat_ident
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='Cделать запрос', callback_data='request')
    button2 = types.InlineKeyboardButton(text='Cоздать скринер-лист', callback_data='scriner')
    markup.add(button1, button2)
    chat_ident = message.chat.id
    print(chat_ident, "ID")
    bot.send_message(message.chat.id, 'Это стартовый экран EDP BOT. Нажмите на кнопку ниже', reply_markup=markup)



# Processing inline-button press
@bot.callback_query_handler(func=lambda call: call.data == 'request')
def request(call):
    """
    Function, that gets request type
    :param call: telebot method for handle InlineKeyBoard responses
    :type call: Any
    :return: -
    :rtype: None
    :raises:
    """
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='Данные по бирже', callback_data='exchange_stream')
    button2 = types.InlineKeyboardButton(text='График', callback_data='klines_stream')
    button3 = types.InlineKeyboardButton(text='Данные по тикеру', callback_data='ticker_stream')
    markup.add(button1, button2, button3)
    bot.send_message(call.message.chat.id, 'Укажите тип запроса:')
    bot.send_message(call.message.chat.id, '1. exchange_stream: получить данные с конкретной биржи по всем тикерам\n'
                                           '2. klines_stream: получить график изменения цены по тикеру\n'
                                           '3. ticker_stream: получить данные по конкретному тикеру', reply_markup=markup)
    bot.register_next_step_handler(call.message, process_stream_function)


@bot.callback_query_handler(func=lambda call: call.data == 'scriner')
def scriner_list_start(call):
    """
    Function, that processes creating scriner-list by user
    :param call: param, that contains data about button, that was pressed by user
    :type call:  telebot.TeleBot
    :return: -
    :rtype: None
    """
    global chat_ident
    print("scriner is running")
    bot.send_message(chat_ident, 'Введите интересущие вас тикеры в строку через пробел \n'
                                 'В конце через пробел укажите параметры count, timeout, exchange \n'
                                 'count: количество обновлений данных \n'
                                 'timeout: интервал обновления данных \n'
                                 'exchange: биржа\n')
    bot.register_next_step_handler(call.message, scriner_list_processing)


def scriner_list_processing(message):
    global chat_ident
    try:
        tickers = message.text.strip().split()
        k = len(scriner_lists)
        scriner_lists[k+1] = tickers
        print(scriner_lists)
        dataset["stream_function"] = "ticker_stream"
        dataset["count"] = tickers[-3]
        dataset["timeout"] = tickers[-2]
        dataset["exchange"] = tickers[-1]
        tickers.pop(-1)
        tickers.pop(-1)
        for ticker in tickers:
            dataset[ticker] = ticker
            usage()
    except ValueError:
        bot.send_message(chat_ident, text='В запросе должен быть хотя бы один тикер и параметры count, timeout и exchange. \n'
                                          'Попробуйте снова!')
        bot.register_next_step_handler(message, scriner_list_start)


@bot.message_handler(commands=['update'])
def scriner_list_updater(message):
    global chat_ident
    scriner_lists_ans = ("Введите id скринер-листов, которые вы хотите обновить \n"
                         "Список доступных скринер-листов для обновления: \n")
    for key in scriner_lists:
        dkey = scriner_lists[key]
        scriner_lists_ans += f'{int(key)}. {", ".join(dkey)} \n'
    bot.send_message(chat_ident, text=scriner_lists_ans)
    bot.register_next_step_handler(message, scriner_update_sender)


def scriner_update_sender(message):
    ids_for_update = message.text.strip().split()
    dataset["stream_function"] = "ticker_stream"
    for id in ids_for_update:
        tickers = scriner_lists[int(id)]
        for ticker in tickers:
            dataset[ticker] = ticker
            usage()


@bot.callback_query_handler(func=lambda call: call.data == 'exchange_stream' or call.data == 'klines_stream' or call.data == 'ticker_stream')
def process_stream_function(call):
    """
    Function, that gets stream_function param for request

    :param message: user reply for stream_function
    :type message: str
    :return: -
    :rtype: None
    :raises:
    """
    global chat_ident
    # print(call.data)
    stream_function = call.data
    if stream_function not in ['exchange_stream', 'klines_stream', 'ticker_stream']:
        bot.send_message(chat_ident, 'Неверный тип запроса. Пожалуйста, выберите еще раз.')
        bot.register_next_step_handler(chat_ident, process_stream_function)
    else:
        dataset["stream_function"] = stream_function
        if dataset["stream_function"] == "ticker_stream" or dataset["stream_function"] == "klines_stream":
            bot.send_message(chat_ident, 'Введите интересующий вас тикер криптовалюты или акции с биржи MOEX:')
        else:
            bot.send_message(chat_ident, 'Введите интересующую вас криптобиржу')
        bot.register_next_step_handler(call.message, process_ticker)

def process_ticker(message):
    """
    Function, that gets ticker param for request
    :param message: user reply for ticker
    :type message: str
    :return: -
    :rtype: None
    :raises:
    """
    ticker = message.text.strip()
    if "1" in ticker:
        bot.send_message(message.chat.id, 'Некорректный тикер. Пожалуйста, введите еще раз.')
        bot.register_next_step_handler(message, process_ticker)
    else:
        dataset["ticker"] = ticker
        if dataset["stream_function"] == "ticker_stream" or dataset["stream_function"] == "klines_stream":
            bot.send_message(message.chat.id, 'Введите количество обновлений данных по тикеру:')
        else:
            bot.send_message(message.chat.id, 'Введите количество обновлений данных по бирже:')
        bot.register_next_step_handler(message, process_count)

def process_count(message):
    """
    Function, that gets count param for request
    :param message: user reply for count
    :type message: int
    :return: -
    :rtype: None
    :raises:
    """
    count = message.text.strip()
    if not count.isdigit():
        bot.send_message(message.chat.id, 'Некорректное количество. Пожалуйста, введите еще раз.')
        bot.register_next_step_handler(message, process_count)
    else:
        dataset["count"] = count
        bot.send_message(message.chat.id, 'Введите интервал, в котором вам будут приходить обновления в секундах:')
        bot.register_next_step_handler(message, process_timeout)


def process_timeout(message):
    """
    Function, that gets timeout param for request
    :param message: user reply for timeout
    :type message: int
    :return: -
    :rtype: None
    :raises:
    """
    timeout = message.text.strip()
    if not timeout.isdigit():
        bot.send_message(message.chat.id, 'Некорректный интервал. Пожалуйста, введите еще раз.')
        bot.register_next_step_handler(message, process_timeout)
    else:
        dataset["timeout"] = timeout
        if dataset["stream_function"] == "exchange_stream":
            dataset["exchange"] = dataset["ticker"]
            show_user(message, dataset)
        else:
            bot.send_message(message.chat.id, 'Введите название интересующей биржи:')
            bot.register_next_step_handler(message, process_exchange)

def process_exchange(message):
    exchange = message.text.strip()
    if not exchange.isalpha():
        bot.send_message(message.chat.id, 'Некорректное название биржи. Пожалуйста, введите еще раз.')
        bot.register_next_step_handler(message, process_exchange)
    else:
        dataset["exchange"] = exchange
        show_user(message, dataset)


@bot.callback_query_handler(func=lambda call: call.data == "yes" or call.data == "no")
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
        usage()
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
    if dataset["stream_function"] == "exchange_stream":
        text = f'Параметры запроса:\n\nТип запроса: {dataset["stream_function"]}\nБиржа: {dataset["exchange"]}\nКоличество обновлений: {dataset["count"]}\nИнтервал: {dataset["timeout"]} секунд\n\nКорректны ли введенные данные?'
    else:
        text = f'Параметры запроса:\n\nТип запроса: {dataset["stream_function"]}\nТикер: {dataset["ticker"]}\nБиржа: {dataset["exchange"]}\nКоличество обновлений: {dataset["count"]}\nИнтервал: {dataset["timeout"]} секунд\n\nКорректны ли введенные данные?'
    markup = telebot.types.InlineKeyboardMarkup()
    button_yes = telebot.types.InlineKeyboardButton(text='Да', callback_data='yes')
    button_no = telebot.types.InlineKeyboardButton(text='Нет', callback_data='no')
    markup.add(button_yes, button_no)
    bot.send_message(message.chat.id, text, reply_markup=markup)
    dataset["block_id"] = message.message_id + 1
    # print(dataset)
    # print(message.text)


def ip_updater(message, *args):
    global IP, chat_ident
    IP = message.text.strip()
    bot.send_message(chat_ident, text=f'Ok, пробуем подключиться к IP: {IP}')
    send(*args)


def send(req, count, block_id, func):
    global chat_ident, IP
    try:
        with connect(IP) as websocket:
            websocket.send(json.dumps(req))
            while count > 0:
                response = websocket.recv()
                try:
                    response = json.loads(response)
                except json.decoder.JSONDecodeError:
                    bot.send_message(chat_ident, text=response)
                    bot.register_next_step_handler(chat_ident, start)
                    return
                threading.Thread(target=func,args=[response, block_id]).start()
                count -= 1
    except ConnectionRefusedError:
        bot.send_message(chat_ident, text="Не удалось подключиться. Введите IP сервера")
        bot.register_next_step_handler(chat_ident, ip_updater, req, count, block_id, func)


def emul_send(req, count, block_id, func):
        responses = [
            {"Exchange": "Binance", "Trade pair": "BTCUSDT", "Price": "41033.13000000", "Fluctuation": "-2.506%"},
            [{"Exchange": "BitMart", "Trade pair": "AFIN_USDT", "Price": "0.002039", "Fluctuation": "0.94%"},
             {"Exchange": "BitMart", "Trade pair": "BMX_ETH", "Price": "0.00006942", "Fluctuation": "-0.7%"}],
            {"exchange": "Binance", "ticker": "BTCUSDT", "from": 1671408000.0, "to": 1702857600.0, "interval": 86400,
             "close_price": ["16438.88000000", "16895.56000000", "16824.67000000"]}
        ]
        while int(count) > 0:
            for i in range(100):
                responses[1].append(responses[1][0])
            response = responses[1]
            threading.Thread(target=func, args=[response, block_id]).start()
            count = int(count) - 1


def process_ex_stream(response, block_id):
    global chat_ident
    print(response)
    response_text = f'{dataset["ticker"]}'
    with open(f'{dataset["ticker"]}.txt', 'w') as file:
        file.write(f'EXCHANGE: {dataset["ticker"]} \n')
        for s in response:
            for key in s:
                if key == "Exchange":
                    continue
                to_write = f'{key}: {s[key]} \n'
                file.write(to_write)
    with open(f'{dataset["ticker"]}.txt', 'rb') as file:
        bot.send_document(chat_ident, file, caption=response_text)

    """
    fig, ax = plt.subplots()
    res = []
    for d in response:
        for key in d:
            res.append([key, d[key]])
            print(res)
    table = ax.table(cellText=res, loc='center')
    # table.set_fontsize(14)
    # table.scale(1, 4)
    ax.axis('off')
    pdf = PdfPages("file2.pdf")
    pdf.savefig()
    # plt.savefig('t.png', transparent=True)
    pdf.close()
    """


def process_ticker_stream(response, block_id):
    global chat_ident
    print(response)
    if response["Trade pair"] not in ids["ticker_stream"]:
        key = response["Trade pair"]
        ids["ticker_stream"][key] = [block_id]
        response_result = (f'Current price for {response["Trade pair"]}: {response["Price"]}. \n'
                           f'Exchange: {response["Exchange"]} \n'
                           f'Fluctuation of {response["Trade pair"]}: {response["Fluctuation"]}')
        bot.send_message(chat_ident, text=response_result)
        print(ids["ticker_stream"])
    elif response["Trade pair"] in ids["ticker_stream"]:
        response_result = (f'UPD: Current price for {response["Trade pair"]}: {response["Price"]}. \n'
                           f'Exchange: {response["Exchange"]} \n'
                           f'Fluctuation of {response["Trade pair"]}: {response["Fluctuation"]}')
        bot.send_message(chat_ident, text=response_result)
        # bot.edit_message_text(text=response_result, chat_id=chat_ident, message_id=block_id)
        # print("edited")

    # check = response["Exchange"] + response["Trade pair"] + response["Fluctuation"]
    # check for moex need change
    # if ids[dataset["stream_function"]][check] not in ids:
        # ids[dataset["stream_function"]][check] = list(block_id)
        # print(ids)
    # else:
        # ids[dataset["stream_function"]][check].append(block_id)
        # print("OK: ", ids)


def process_klines_stream(response, block_id):
    global chat_ident
    print(response)
    # x = range(int(response['from']), int(response['to']) + 1, int(response['interval']))
    x = range(0, 3)
    y = [int(float(y)) for y in response['close_price']]
    plt.plot(x, y)
    step = 7
    x_ticks = [x[len(x) * i // step - int(i == step)] for i in range(step + 1)]
    f = lambda x: "0" * int(len(str(x)) == 1) + str(x)
    x_labels = [f"{f(time.gmtime(x)[2])}.{f(time.gmtime(x)[1])}.{f(time.gmtime(x)[0])}" for x in x_ticks]
    plt.xticks(ticks=x_ticks, labels=x_labels)
    """
    x = range(0,3)
    y = [int(float(y)) for y in response['close_price']]
    plt.plot(x, y)
    """
    img_name = str(dataset["ticker"] + ".png")
    plt.savefig(img_name, transparent=True)
    caption = dataset["ticker"]
    with open(img_name, 'rb') as img:
        bot.send_photo(chat_ident, img, caption=caption)


stream_functions = {
            "exchange_stream": process_ex_stream,
            "klines_stream":process_klines_stream,
            "ticker_stream": process_ticker_stream}


def usage():
    # if dataset["stream_function"] == "ticker_exchange":
    #     ticker_stream_processing(dataset)
    # print(dataset, type(dataset))

    req = {"type": dataset['stream_function'], "data": {}, "count": dataset['count'], "timeout": dataset['timeout']}
    req_id = abs(hash(str(dataset)))
    dataset.pop('stream_function')
    dataset.pop('count')
    dataset.pop('timeout')
    dataset.pop('block_id')
    req['data'].update(dataset)
    print(req)
    _args = [req, req['count'], req_id, stream_functions[req['type']]]
    threading.Thread(target=emul_send,args=_args).start()


if __name__ == "__main__":
    bot.polling()