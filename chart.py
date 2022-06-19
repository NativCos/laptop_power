import plotly.graph_objects as go
from database import DBSession
from model import Power
import datetime
import numpy as np


def get_data(session):
    time = 60 * 10  # 10 minutes
    data = session.query(Power) \
        .where(Power.date > datetime.datetime.now() - datetime.timedelta(seconds=time)) \
        .order_by(Power.date) \
        .all()
    return data


def show_charts(data):
    YY = []
    for d in data:
        YY.append(d.energy_now / pow(10, 6))

    window_size = 18
    window_size = 1
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
    speed = d_energy_now / time  # seconds
    remaining_time_to_live = data[-1].energy_now * ((100 - 6) / 100) / speed
    datetime_to_die = datetime.datetime.now() + datetime.timedelta(seconds=remaining_time_to_live)
    remaining_time_to_live = datetime.timedelta(seconds=remaining_time_to_live)
    full_time_live = data[0].energy_full / speed
    full_time_live = datetime.timedelta(seconds=full_time_live)

    print(f"{datetime_to_die.ctime()} time to die")
    print(f"{remaining_time_to_live} rest time to live in hours")
    print(f"{full_time_live} full time to live in hours")


def main():
    data = get_data(DBSession())
    calc_times(data)
    #show_charts(data)


if __name__ == '__main__':
    main()
