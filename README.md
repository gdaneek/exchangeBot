
# EDP Bot #
Telegram-бот для получения актуальных сводок по криптовалютам и ценным бумагам с возможностью построения графиков. <br>

## Установка и запуск ##

Необходимо скачать архив с исходным кодом и запустить файл *ws_server.py* на устройстве, выполняющем роль *сервера*, и файл *client.py* на устройстве, на котором должен быть запущен Telegram-бот. 

> Сервер и бот могут быть запущены на одном устройстве. В таком случае в поле *"IP сервера"* необходимо указать следующий адрес: *127.0.0.1* <u>(см. раздел "EDP bot")</u>

После успешного запуска сервера и настройки бота данные о криптовалютных и фондовых биржах можно получать в Telegram: https://t.me/ExchangeDataProcessing_bot

## WebSocket-сервер ##

Сервер собирает и обрабатывает данные криптобирж (Binance, Bybit, BitMart, KuCoin)  и фондовых бирж (MOEX). 

> Код сервера содержится в файле *ws_server.py*

Сервер запускается командой `python ws_server.py` из корневого каталога проекта.

+ *IP: 127.0.0.1*
+ *Порт: 8765*
+ *Протокол: ws*

#### Сервер-API ####

Для получения данных необходимо отправить запрос вида ws://xxx.xxx.xxx.xxx:8765, указав IP-адрес WebSocket-сервера (<u>IP совпадает с IP-сервера, если он запущен на том же устройстве, что и клиент-приложение</u>), включающей в себя следующие параметры:

+ *type* (**обязательный**): указывает тип потока данных, отправляемых сервером 
+ *data* (**обязательный**): параметры запроса к бирже
+ *count* (необязательный): количество запросов к бирже, которое необходимо сделать. По умолчанию: 1
+ *timeout* (необязательный): задержка между запросами к бирже. По умолчанию: 1 секунда

> Для поключения к серверу, запущенному на другом устройстве, необхлжимо указать локальный или глобальный IP устройства с сервером

<u>Определённые значения параметра type:</u>
1. **ticker_stream**. Отправляет стоимость и изменение стоимости(в процентах) тикера за 24 часа.
2. **exchange_stream**. Отправляет стоимость и изменение за 24 часа всех тикеров биржи.
3. **klines_stream**. Отправляет список стоимостей тикера за указанный период для построения графиков. 

<u>Возможные ключи параметра data:</u>
1. **ticker**. Название тикера 
2. **exchange**. Название биржи
3. **extype**. Тип биржи. По умолчанию *crypto* (криптовалютная биржа)
4. **interval**. Интервал, с которым необходимо получать данные для графика
5. **limit**. Количество значений стоимости, которое необходимо взять для построения графика с шагом *interval* до настоящего времени

> Словарь параметров должен быть преобразован в JSON перед отправкой

<u>Пример корректного запроса на получение данных для построения графика стоимости тикера BTC-USDT биржи Binance:</u>

```
{
"type":"klines_stream",
"data":
    {
	"ticker":"BTC-USDT",
	"interval":"1d",
	"limit": 7
    },
}
```

<u>Пример корректного запроса для получения данных о тикере SBER биржи MOEX 5 раз с интервалом 10 секунд:</u>

```
{
"type":"ticker_stream",
"data":
    {
	"ticker":"SBER",
	"exchange":"MOEX",
	"extype":"stock",
    },
"timeout":10,
"count":5
}
```

*Для получения аналогичных данных для криптобирж параметр extype можно не указывать*

#### Ответы сервера ####

Обычный ответ сервера является JSON-строкой и содержит обработанные данные. 

> Если в процессе работы возникает ошибка, сервер возвращает код ошибки и её краткое описание. Значения кодов ошибок приведены ниже

<u>Список ошибок:</u>

+ **WRF 0x01** *(Wrong Request Format)*: запрос не является JSON-строкой
+ **RPM 0x01** *(Required Parameter Missed):* не указан обязательный параметр type
+ **RPM 0x02** *(Required Parameter Missed):* не указан обязательный параметр data
+ **BExR 0x01** *(Bad Exchange Response):* ответ биржи имеет код ошибки
+ **WPV 0x01** *(Wrong Parameter Value):* некоторые из параметров имеют некорректное значение или тип данных
+ **WPV 0x02** *(Wrong Parameter Value):* ticker не содержит разделителя '-'
+ **WPV 0x03** *(Wrong Parameter Value):* биржа exchange не поддерживается сервером
+ **WPV 0x04** *(Wrong Parameter Value):* type/extype должен быть сторокой
+ **WPV 0x05** *(Wrong Parameter Value):* count/timeout должен состоять только из цифр
+ **WPV 0x06** *(Wrong Parameter Value):* type/extype имеет неизвестное значение
+ **UnErr** *(Undefined Error):* неизвестная ошибка

<u>Ответы сервера для двух примеров выше:</u>

```
{
"exchange": "Binance", 
"ticker": "BTCUSDT", 
"from": 1702339200.0, 
"to": 1702857600.0, 
"interval": 86400, 
"close_price": 
	[
	"41492.39000000", 
	"42869.03000000", 
	"43022.26000000", 
	"41940.30000000", 
	"42278.03000000", 
	"41374.65000000", 
	"41560.00000000"
	]
}
```


```
{
"Ticker": "SBER", 
"Current price": "263.49 RUB", 
"Market cap": "50428140 RUB", 
"P/E": "4.57"
}
```

Ответы сервера принимают клиент-приложения. 
<u>Наше приложение</u> - *Telegram-бот EDP bot* 
## EDP bot ##
Telegram-бот для получения информации о тикерах фондовых и/или криптовалютных бирж с возможностью построения графиков.

## Как пользоваться ##

1. Переходим по ссылке https://t.me/ExchangeDataProcessing_bot и вводим команду /start.
2. Указываем тип запроса. Если тип запроса указан неверно - бот предложит ввести его заново
		![Image alt](https://github.com/gdaneek/exchangeBot/raw/master/img/1.png)

3. Выбираем тикер или биржу. После выбора тикера и биржи указываем необязательные параметры 
		![Image alt](https://github.com/gdaneek/exchangeBot/raw/master/img/2.png)

4. Подтверджаем корректность введённых данных:
		![Image alt](https://github.com/gdaneek/exchangeBot/raw/master/img/3.png)

		*Если данные введены неверно, бот откинет вас в точку /start*

5.  Получаем результат
		![Image alt](https://github.com/gdaneek/exchangeBot/raw/master/img/4.png)
		Результат для ticker_stream:
		![Image alt](https://github.com/gdaneek/exchangeBot/raw/master/img/5.png)

> Бот может попросить вас ввести IP сервера вручную, если запрос окажется неудачным. Если сервер недоступен - укажите IP-адрес (локальный или глобальный) устройства, на котором запущен сервер и попробуйте подключиться ещё раз.