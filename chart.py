#!/usr/bin/env python3
import plotly.graph_objects as go
from database import DBSession
from model import Power
import datetime
import numpy as np
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler())


def get_data(session):
    time = 60 * 4  # 10 minutes
    data = session.query(Power) \
        .where(Power.date > datetime.datetime.now() - datetime.timedelta(seconds=time)) \
        .order_by(Power.date) \
        .all()
    return data


def show_charts(data):
    YY = []
    for d in data:
        YY.append(d.power_now / pow(10, 6))

    window_size = 18
    for i in range(len(YY) - window_size):
        YY[i] = np.mean(YY[i:i + window_size])
    YY = YY[0:len(YY) - window_size]
    XX = list(range(len(YY)))
    fig = go.Figure()
    fig.add_scatter(x=XX, y=YY)
    fig.show()


def calc_times(data):
    time = (data[-1].date - data[0].date).seconds
    d_energy_now = data[0].energy_now - data[-1].energy_now
    speed = d_energy_now / time  # (seconds). Микро-Ват-Часы делятся на секунды. да-да... Я знаю
    if speed != 0:
        if data[0].status == Power.Status.Discharging:
            remaining_time_to_live = (data[-1].energy_now - (data[-1].energy_full * 6 / 100)) / speed
            """В строчке выше высчитывается оставшиеся время жизни батареи.
               Преполагается что батарея может разрядиться только до 6%.
               formula: (<энергии сейчас> - <6% от полной емкости>) / <скорость разрядки>"""
            datetime_to_die = datetime.datetime.now() + datetime.timedelta(seconds=remaining_time_to_live)
            remaining_time_to_live = datetime.timedelta(seconds=remaining_time_to_live)
            full_time_live = data[0].energy_full / speed
            full_time_live = datetime.timedelta(seconds=full_time_live)

            print(f"Status: {data[0].status}")
            print(f"{datetime_to_die.ctime()} time to die")
            print(f"{remaining_time_to_live} rest time to live in hours")
            print(f"{full_time_live} full time to live in hours")
        elif data[0].status == Power.Status.Charging:
            speed = -speed
            remaining_time_to_done = (data[-1].energy_full - data[-1].energy_now) / speed
            datetime_to_done = datetime.datetime.now() + datetime.timedelta(seconds=remaining_time_to_done)

            print(f"Status: {data[0].status}")
            print(f"{datetime_to_done.ctime()} time to done")
            print(f"{datetime.timedelta(seconds=remaining_time_to_done)} rest time to done")
        else:
            print("WTF? unknow battary status...")
    elif speed == 0:
        print('Status: FULL')


def main():
    data = get_data(DBSession())
    _logger.debug(data[0])
    calc_times(data)
    show_charts(data)


if __name__ == '__main__':
    _logger.setLevel(logging.WARNING)
    main()
