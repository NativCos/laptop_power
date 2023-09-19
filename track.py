#!/usr/bin/env python3
from database import DBSession
import threading
import asyncio

from service import BatteryService


class Timer:
    def __init__(self, timeout, callback):
        self.task = None
        self._timeout = timeout
        self._callback = callback

        self.task = asyncio.create_task(self._job())

    async def _job(self):
        try:
            while True:
                await asyncio.sleep(self._timeout)
                self._callback()
        except asyncio.CancelledError:
            return

    def cancel(self):
        self.task.cancel()
        self.task = None
        return None  # timer should be destroyed


class Tracking:
    """singleton"""

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Tracking, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        self._batteryservice = BatteryService()
        self._db_session = DBSession()
        self._myloop = asyncio.get_event_loop()

        delay = 1.0  # this is minimum as possible. kernel will not provide faster
        self.gather_timers = asyncio.gather(
            Timer(15.0, self._db_session.commit).task,
            # Timer(300.0, self._once_track_battery).task,
            # Timer(delay, self._once_track_power_now).task,
            Timer(delay, self._once_track_energy_now).task,
        )

    def _once_track_battery(self):
        self._db_session.add(self._batteryservice.get())

    def _once_track_power_now(self):
        self._db_session.add(self._batteryservice.get_power_now())

    def _once_track_energy_now(self):
        self._db_session.add(self._batteryservice.get_energy_now())

    def cancel(self):
        """tread safe"""
        self._myloop.call_soon_threadsafe(self.gather_timers.cancel)


async def start_tracking():
    tracking = Tracking()
    await tracking.gather_timers


def start_tracking_in_new_thread():
    # create new thread for new asyncio event loop
    new_thread = threading.Thread(target=asyncio.run(start_tracking()), daemon=True)
    new_thread.start()
    return new_thread


if __name__ == '__main__':
    # this thread will wait
    start_tracking_in_new_thread().join()
