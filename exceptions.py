class StatusNotOKError(Exception):
    """Запрос возвращает статус, отличный от статуса 200."""
    pass


class GetAPIError(Exception):
    """При получении ответа от API возникает проблема."""
    pass


class SendMessageError(Exception):
    """Не удалось отправить сообщение в телеграмм."""
    pass


class CheckResponseError(Exception):
    """Проблемы в функции check_response
    при проверке ответа на корректность."""
    pass
