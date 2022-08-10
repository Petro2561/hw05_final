import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    dt_now = datetime.datetime.now()
    b = int(dt_now.strftime('%Y'))
    return {
        'year': b,
    }
