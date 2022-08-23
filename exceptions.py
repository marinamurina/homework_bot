class StatusNotOK(Exception):
    """Запрос возвращает статус, отличный от статуса 200."""
    pass


class GetAPIProblem(Exception):
    """При получении ответа от API возникла проблема."""
    pass


class SendMessageProblem(Exception):
    """Не удалось отправить сообщение в телеграмм."""
    pass


class CheckResponseProblem(Exception):
    """Проблемы в функции check_response
    при проверке ответа на корректность."""
    pass
