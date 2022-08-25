import json
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)


def send_message(bot, message):
    """Отправка сообщения в телеграм-чат."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f'{message}',
        )
    except telegram.TelegramError as error:
        logger.error(
            f'Ошибка при отправке сообщения:{error}!')


def get_api_answer(current_timestamp):
    """Запрос к сервису API Яндекс.Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except requests.RequestException as error:
        raise exceptions.GetAPIError(
            f'Ошибка при запросе к сервису API:{error}!')
    if homework_statuses.status_code != HTTPStatus.OK:
        raise exceptions.StatusNotOKError(
            f'Статус ответа сервера {homework_statuses.status_code}!'
        )
    try:
        response = homework_statuses.json()
    except json.JSONDecodeError:
        raise json.JSONDecodeError('Ошибка перевода ответа из json в python.')
    return response


def check_response(response):
    """Проверка ответа API Яндекс.Практикум на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ответ сервера не является словарем!')
    try:
        homeworks = response['homeworks']
    except KeyError as error:
        raise KeyError(f'Ошибка доступа по ключу - {error}')
    except Exception as error:
        raise exceptions.CheckResponseError(
            f'Не получен список работ - {error}'
        )
    if not isinstance(homeworks, list):
        raise TypeError('Данные не являются списком!')
    return homeworks


def parse_status(homework):
    """Получение статуса домашней работы."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    except KeyError as key_error:
        raise KeyError(
            f'Отсутствуют ожидаемые ключи - {key_error}!')
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as key_error:
        raise KeyError(
            f'Неизвестный статус домашней работы - {key_error}!')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # дата нулевого запроса Sun May 01 2022 20:00:00 - 1651424400
    current_timestamp = 1651424400
    error = None

    if not check_tokens():
        logger.critical(
            'Отсутствие необходимых токенов для работы программы!')
        sys.exit(['Отсутствие необходимых токенов для работы программы!'])

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homeworks = check_response(response)
            if len(homeworks) == 0:
                logger.info('Статус домашней работы не изменился.')
            else:
                message = parse_status(homeworks[0])
                send_message(bot, message)
                logger.info(
                    f'В телеграм отправлено сообщение: {message}')

        except Exception as new_error:
            message = f'Сбой в работе программы: {new_error}.'
            logger.error(f'Сбой в работе программы: {new_error}')
            if error != str(new_error):
                error = str(new_error)
                send_message(bot, message)
                logger.info(f'В телеграм отправлено сообщение: {message}')

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
