from sqlalchemy import Column, DATETIME, INTEGER, Enum
from sqlalchemy.orm import declarative_base
import enum

LaptopPowerDeclarativeModelBase = declarative_base()


class Battery(LaptopPowerDeclarativeModelBase):
    """Информация о питании батареи ноутбука"""
    __tablename__ = 'battery'

    class Status(enum.Enum):
        Charging = 0
        Discharging = 1

    date = Column(DATETIME, primary_key=True)
    power_now = Column(INTEGER, nullable=True)
    status = Column(Enum(Status), nullable=True)
    """str 'Discharging' or 'Charging'"""
    capacity = Column(INTEGER, nullable=True)
    cycle_count = Column(INTEGER, nullable=True)
    energy_full = Column(INTEGER, nullable=True)
    energy_now = Column(INTEGER, nullable=True)
    energy_full_design = Column(INTEGER, nullable=True)

    def __repr__(self):
        return f"<Battery data={self.date}" \
                      f" power_now={self.power_now}" \
                      f" status={self.status}" \
                      f" capacity={self.capacity}>" \
                      f" cycle_count={self.cycle_count}>" \
                      f" energy_full={self.energy_full}>" \
                      f" energy_now={self.energy_now}>" \
                      f" energy_full_design={self.energy_full_design}>"

    def __init__(self, date, power_now, status, capacity, cycle_count, energy_full, energy_now, energy_full_design):
        self.date = date
        self.power_now = power_now
        self.status = status
        self.capacity = capacity
        self.cycle_count = cycle_count
        self.energy_full = energy_full
        self.energy_now = energy_now
        self.energy_full_design = energy_full_design


class BatteryPowerNow(LaptopPowerDeclarativeModelBase):
    """информация только о текущем энергопотреблении"""
    __tablename__ = 'batterypowernow'

    date = Column(DATETIME, nullable=False, primary_key=True)
    power_now = Column(INTEGER, nullable=False)
    """power now consume in micro watts (10^-6)"""

    def __init__(self, date, power_now):
        self.date = date
        self.power_now = power_now

    def __repr__(self):
        return f"<BatteryPowerNow date={self.date} power_now={self.power_now}>"


class BatteryEnergyNow(LaptopPowerDeclarativeModelBase):
    """информация только о текущем энергопотреблении"""
    __tablename__ = 'batteryenergynow'

    date = Column(DATETIME, nullable=False, primary_key=True)
    energy_now = Column(INTEGER, nullable=False)
    """power now consume in micro watts (10^-6)"""

    def __init__(self, date, energy_now):
        self.date = date
        self.energy_now = energy_now

    def __repr__(self):
        return f"<BatteryEnergyNow date={self.date} energy_now={self.energy_now}>"
