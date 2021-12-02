import unittest
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock, ANY

from pony.orm import rollback, db_session
from vk_api.bot_longpoll import VkBotMessageEvent

import settings
from bot import Bot
from generate_ticket import generate_ticket


def isolate_db(test_funk):
    def wrapper(*args, **kwargs):
        with db_session:
            test_funk(*args, **kwargs)
            rollback()
    return wrapper


class Test1(TestCase):
    RAW_EVENT = {
        'type': 'message_new',
        'object': {'message': {'date': 1615815564, 'from_id': 5070114, 'id': 184, 'out': 0,
                               'peer_id': 5070114, 'text': 'ghxfghjf', 'conversation_message_id': 183,
                               'fwd_messages': [], 'important': False, 'random_id': 0, 'attachments': [],
                               'is_hidden': False}, 'client_info':
                       {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback',
                                           'intent_subscribe',
                                           'intent_unsubscribe'], 'keyboard': True, 'inline_keyboard': True,
                        'carousel': False, 'lang_id': 0}}, 'group_id': 203109674,
        'event_id': '9adc69a65c7b7f5460168aea993fc4dcb91faa1b'
    }

    def test_run(self):
        count = 5
        obj = {"a": 1}
        events = [obj] * count  # [obj, obj, ...]
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch("bot.vk_api.VkApi"):
            with patch("bot.VkBotLongPoll", return_value=long_poller_listen_mock):
                bot = Bot("", "")
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    def test_on_event(self):
        event = VkBotMessageEvent(raw=self.RAW_EVENT)
        send_mock = Mock()
        with patch("bot.vk_api.VkApi"):
            with patch("bot.VkBotLongPoll"):
                bot = Bot("", "")
                bot.api = Mock()
                bot.api.messages.send = send_mock
                bot.on_event(event)
        send_mock.assert_called_once_with(
            message=f'Не знаю как ответить на Ваш запрос. Передам вопрос администрации сайта.Могу подсказать когда и '
                    f'где будет проходить конференция, а также зарегистрировать вас. Просто спросите об этом.',
            random_id=ANY,
            peer_id=self.RAW_EVENT['object']["message"]['peer_id']
        )

    INPUTS = [
        "Я Иван!",
        "привет",
        "когда",
        "где",
        "зарег",
        "Вася",
        "art@mail.ru",
        "Спасибо!",
    ]
    EXPECTED_OUTPUTS = [
        settings.DEFAULT_ANSWER,
        settings.INTENTS[0]["answer"],
        settings.INTENTS[2]["answer"],
        settings.INTENTS[3]["answer"],
        settings.SCENARIOS["registration"]["steps"]["step1"]["text"],
        settings.SCENARIOS["registration"]["steps"]["step2"]["text"],
        settings.SCENARIOS["registration"]["steps"]["step3"]["text"].format(name="Вася", email="art@mail.ru"),
        settings.INTENTS[5]["answer"],
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event["object"]["message"]["text"] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch("bot.VkBotLongPoll", return_value=long_poller_mock):
            bot = Bot(" ", " ")
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs["message"])
        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_image_generation(self):
        with open("files/art.jpg", "rb") as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()

        with patch("requests.get", return_value=avatar_mock):
            ticket_file = generate_ticket("Вася", "art")

        with open("files/ticket_example.png", "rb") as expected_file:
            expected_bytes = expected_file.read()

        assert ticket_file.read() == expected_bytes


if __name__ == '__main__':
    unittest.main()
