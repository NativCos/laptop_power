import plotly.graph_objects as go
import asyncio
from database import DBSession
from model import Power
import datetime
import numpy as np


async def show_charts(session):
    time = 60 * 10
    data = session.query(Power) \
                .where(Power.date > datetime.datetime.now() - datetime.timedelta(seconds=time)) \
                .order_by(Power.date) \
                .all()
    YY = []
    for d in data:
        YY.append(d.power_now)

    window_size = 18
    for i in range(len(YY) - window_size):
        YY[i] = np.mean(YY[i:i + window_size])
    YY = YY[0:len(YY) - window_size]
    XX = list(range(len(YY)))
    fig = go.Figure()
    fig.add_scatter(x=XX, y=YY)
    fig.show()

    d_energy_now = data[0].energy_now - data[-1].energy_now
    speed = d_energy_now / time  # seconds
    time_to_die = datetime.datetime.now() + datetime.timedelta(seconds=(data[0].energy_now*(1.0-0.06) / speed))
    print(f"{time_to_die} time to die")
    print(f"{(data[0].energy_now / speed / 60 / 60):.2f} rest time to live")
    print(f"{(data[0].energy_full / speed / 60 / 60):.2f} full time to live hour")


async def main():
    task2 = asyncio.create_task(show_charts(DBSession()))
    await asyncio.gather(task2)

asyncio.run(main())
