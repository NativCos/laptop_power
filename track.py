#!/usr/bin/env python3
from database import DBSession
import asyncio
from service import BatteryService


async def track(session):
    delay = 1  # seconds
    max_time_count = 10  # every seconds
    max_time_count = max_time_count / delay
    time_count = 0

    batteryservice = BatteryService()

    try:
        while True:
            session.add(batteryservice.get())
            if time_count == max_time_count:
                session.commit()
                time_count = 0
            time_count += 1

            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        session.commit()
        del batteryservice


if __name__ == '__main__':
    asyncio.run(track(DBSession()))


