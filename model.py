from sqlalchemy import Column, DATETIME, INTEGER, Enum
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()


class Battery(Base):
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

