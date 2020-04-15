
from datetime import datetime, timedelta

def get_time_range(time_interval):
    if time_interval == 'day':
        interval = timedelta(days=1)
    elif time_interval == 'week':
        interval = timedelta(days=7)
    elif time_interval == 'month':
        interval = timedelta(days=31)

    now = datetime.now()
    print(datetime.strftime(now, '%d.%m.%Y %H:%M'))

    result = now-interval
    result = datetime.strftime(result, '%d.%m.%Y %H:%M')
    print(result)
    return result

get_time_range("week")