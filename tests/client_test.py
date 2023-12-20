import pytest
from unittest.mock import Mock
import telebot
from .. import client as c


def test_start_successful():
    telebot.types = Mock()
    telebot.TeleBot.send_message = Mock()
    message = Mock()
    message.chat.id = 123
    c.start(message)

    assert telebot.TeleBot.send_message.call_count == 1
    assert c.chat_ident == message.chat.id


def test_request_successful():
    call = Mock()
    telebot.TeleBot.send_message, telebot.TeleBot.register_next_step_handler = Mock(), Mock()
    c.request(call)

    assert telebot.TeleBot.send_message.call_count == 2
    telebot.TeleBot.register_next_step_handler.assert_called_with(call.message, c.process_stream_function)


def test_scriner_list_start_successful():
    telebot.TeleBot.send_message, telebot.TeleBot.register_next_step_handler = Mock(), Mock()
    call = Mock()
    c.scriner_list_start(call)

    telebot.TeleBot.register_next_step_handler.assert_called_with(call.message, c.scriner_list_processing)


def test_scriner_list_processing_successful():
    message = Mock()
    message.text = "ETH-USDT BTC-USDT"
    c.usage = Mock()
    c.scriner_list_processing(message)

    assert c.usage.call_count == 2


def test_handle_callback_query_call_data_no():
    call = Mock()
    c.usage = Mock()
    call.data = "no"
    telebot.TeleBot.send_message = Mock()
    c.handle_callback_query(call)

    telebot.TeleBot.send_message.assert_called_with(call.message.chat.id, "Введите /start и заново укажите данные")
    assert c.usage.call_count == 0


def test_handle_callback_query_call_data_invalid():
    call = Mock()
    c.usage = Mock()
    call.data = "abcde"
    telebot.TeleBot.send_message = Mock()
    c.handle_callback_query(call)

    telebot.TeleBot.send_message.assert_called_with(call.message.chat.id, "Неверный ответ. Нажмите 'Да' или 'Нет'")
    assert c.usage.call_count == 0


def test_handle_callback_query_call_data_yes():
    call = Mock()
    call.data = "yes"
    c.usage = Mock()
    c.handle_callback_query(call)

    assert c.usage.call_count == 1



