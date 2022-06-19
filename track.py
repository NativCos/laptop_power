#!/usr/bin/env python
import sys
import datetime
from model import Power
from database import DBSession
import enum
import asyncio


def classproperty(func):
    class Property:
        def __get__(self, a, b):
            return func()
    return Property()


class WhatTracking(enum.Flag):
    power_now = enum.auto()
    status = enum.auto()
    capacity = enum.auto()
    cycle_count = enum.auto()
    energy_full = enum.auto()
    energy_now = enum.auto()
    NONE = 0

    @classproperty
    def ALL():
        return WhatTracking.power_now \
               | WhatTracking.status \
               | WhatTracking.capacity \
               | WhatTracking.cycle_count \
               | WhatTracking.energy_full \
               | WhatTracking.energy_now


async def track(session, what_tracking=WhatTracking.ALL):
    delay = 1  # seconds
    max_time_count = 30  # every seconds
    max_time_count = max_time_count / delay
    time_count = 0

    linux_power_now_file = open('/sys/class/power_supply/BAT0/power_now', 'rt')
    linux_status_file = open('/sys/class/power_supply/BAT0/status', 'rt')
    linux_capacity_file = open('/sys/class/power_supply/BAT0/capacity', 'rt')
    linux_cycle_count_file = open('/sys/class/power_supply/BAT0/cycle_count', 'rt')
    linux_energy_full_file = open('/sys/class/power_supply/BAT0/energy_full', 'rt')
    linux_energy_now_file = open('/sys/class/power_supply/BAT0/energy_now', 'rt')

    power_now = None
    status = None
    capacity = None
    cycle_count = None
    energy_full = None
    energy_now = None

    try:
        while True:
            if what_tracking & WhatTracking.power_now:
                power_now = linux_power_now_file.read().replace('\n', '')
                linux_power_now_file.seek(0)
            if what_tracking & WhatTracking.status:
                status = linux_status_file.read().replace('\n', '')
                status = Power.Status.Discharging if status == 'Discharging' else Power.Status.Charging
                linux_status_file.seek(0)
            if what_tracking & WhatTracking.capacity:
                capacity = linux_capacity_file.read().replace('\n', '')
                linux_capacity_file.seek(0)
            if what_tracking & WhatTracking.cycle_count:
                cycle_count = linux_cycle_count_file.read().replace('\n', '')
                linux_cycle_count_file.seek(0)
            if what_tracking & WhatTracking.energy_full:
                energy_full = linux_energy_full_file.read().replace('\n', '')
                linux_energy_full_file.seek(0)
            if what_tracking & WhatTracking.energy_now:
                energy_now = linux_energy_now_file.read().replace('\n', '')
                linux_energy_now_file.seek(0)

            time_now = datetime.datetime.now()
            p = Power(time_now, power_now, status, capacity, cycle_count, energy_full, energy_now)
            session.add(p)
            if time_count == max_time_count:
                session.commit()
                time_count = 0
            time_count += 1

            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        session.commit()
        linux_power_now_file.close()
        linux_capacity_file.close()
        linux_status_file.close()
        linux_cycle_count_file.close()
        linux_energy_full_file.close()
        linux_energy_now_file.close()


if __name__ == '__main__':
    asyncio.run(track(DBSession(), WhatTracking.ALL))


