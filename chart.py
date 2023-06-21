#!/usr/bin/env python3
import plotly.graph_objects as go
from database import DBSession
from model import Battery
from service import BatteryService
import datetime
import numpy as np
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler())


def get_data(session):
    time = 60 * 10  # 10 minutes
    data = session.query(Battery) \
        .where(Battery.date > datetime.datetime.now() - datetime.timedelta(seconds=time)) \
        .order_by(Battery.date) \
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


def main():
    data = get_data(DBSession())
    _logger.debug(data[0])
    BatteryService.calc_times(data)
    show_charts(data)


if __name__ == '__main__':
    _logger.setLevel(logging.WARNING)
    main()
