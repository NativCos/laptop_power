#!/usr/bin/env python3
from database import DBSession
import asyncio
from service import BatteryService


class Timer:
    def __init__(self, timeout, callback):
        self._task = None
        self._timeout = timeout
        self._callback = callback

    def start(self):
        self._task = asyncio.ensure_future(self._job())
        return self

    async def _job(self):
        while True:
            await asyncio.sleep(self._timeout)
            await self._callback()

    def cancel(self):
        self._task.cancel()


class Tracking:
    def __init__(self):
        self._batteryservice = BatteryService()
        self.db_session = DBSession()

    def once_track_battery_async(self):
        self.db_session.add(self._batteryservice.get())

    def track(self, session):
        delay = 1  # seconds
        max_time_count = 10  # every seconds
        max_time_count = max_time_count / delay
        time_count = 0

        try:
            while True:
                session.add(self._batteryservice.get())

                if time_count == max_time_count:
                    session.commit()
                    time_count = 0
                time_count += 1

                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            session.commit()


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


async def main():
    db_session = DBSession()
    await track(db_session)

if __name__ == '__main__':
    asyncio.run(main())


