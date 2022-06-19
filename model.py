from sqlalchemy import Column, DATETIME, INTEGER, Enum
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()


class Power(Base):
    """Информация и питании ноутбука"""
    __tablename__ = 'power'

    class Status(enum.Enum):
        Charging = 0
        Discharging = 1

    date = Column(DATETIME, primary_key=True)
    power_now = Column(INTEGER, nullable=True)
    status = Column(Enum(Status), nullable=True)
    capacity = Column(INTEGER, nullable=True)
    cycle_count = Column(INTEGER, nullable=True)
    energy_full = Column(INTEGER, nullable=True)
    energy_now = Column(INTEGER, nullable=True)

    def __repr__(self):
        return f"<Power data={self.date}" \
                      f" power_now={self.power_now}" \
                      f" status={self.status}" \
                      f" capacity={self.capacity}>" \
                      f" cycle_count={self.cycle_count}>" \
                      f" energy_full={self.energy_full}>" \
                      f" energy_now={self.energy_now}>"

    def __init__(self, date, power_now, status, capacity, cycle_count, energy_full, energy_now):
        self.date = date
        self.power_now = power_now
        self.status = status
        self.capacity = capacity
        self.cycle_count = cycle_count
        self.energy_full = energy_full
        self.energy_now = energy_now

