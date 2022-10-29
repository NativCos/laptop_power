#!/usr/bin/env python3
import datetime
from model import Power
from database import DBSession, create_schema
import asyncio


async def track(session):
    delay = 1  # seconds
    max_time_count = 10  # every seconds
    max_time_count = max_time_count / delay
    time_count = 0

    linux_uevent_file = open('/sys/class/power_supply/BAT0/uevent', 'rt')

    try:
        power_now = None
        status = None
        capacity = None
        cycle_count = None
        energy_full = None
        energy_now = None
        energy_full_design = None

        while True:
            for line in linux_uevent_file.read().split('\n')[0:-2]:
                key, value = line.split('=')
                if key == 'POWER_SUPPLY_STATUS':
                    status = Power.Status.Discharging if value == 'Discharging' else Power.Status.Charging
                elif key == 'POWER_SUPPLY_CYCLE_COUNT':
                    cycle_count = int(value)
                elif key == 'POWER_SUPPLY_POWER_NOW':
                    power_now = int(value)
                elif key == 'POWER_SUPPLY_ENERGY_FULL_DESIGN':
                    energy_full_design = int(value)
                elif key == 'POWER_SUPPLY_ENERGY_FULL':
                    energy_full = int(value)
                elif key == 'POWER_SUPPLY_ENERGY_NOW':
                    energy_now = int(value)
                elif key == 'POWER_SUPPLY_CAPACITY':
                    capacity = int(value)
            linux_uevent_file.seek(0)

            time_now = datetime.datetime.now()
            p = Power(time_now, power_now, status, capacity, cycle_count, energy_full, energy_now, energy_full_design)
            session.add(p)
            if time_count == max_time_count:
                session.commit()
                time_count = 0
            time_count += 1

            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        session.commit()
        linux_uevent_file.close()


if __name__ == '__main__':
    asyncio.run(track(DBSession()))


