import datetime
import time

from model import Battery
import os


class Constraint:
    """Ограничение пакета RAPL. Описаны не все. Только обязательные"""
    name = None

    def __init__(self, sysfsMasterPackage, id):
        self._sysfsMasterPackage = sysfsMasterPackage
        self._id = id
        # TODO: name is optional by docs (may be errors)
        #  https://www.kernel.org/doc/html/next/power/powercap/powercap.html
        with open(f'{self._sysfsMasterPackage}/constraint_{self._id}_name', 'rt') as f:
            self.name = f.read().replace('\n', '')

    def get_power_limit_uw(self):
        """ МИКРОВАТТЫ
        :return: int
        """
        with open(f'{self._sysfsMasterPackage}/constraint_{self._id}_power_limit_uw', 'rt') as f:
            return int(f.read())

    def set_power_limit_uw(self, power_limit_uw):
        """
        :param power_limit_uw: int МИКРОВАТТЫ
        """
        with open(f'{self._sysfsMasterPackage}/constraint_{self._id}_power_limit_uw', 'wt') as f:
            f.write(str(power_limit_uw))

    def get_time_window_us(self):
        """ МИКРОСЕКУНДЫ
        :return: int
        """
        with open(f'{self._sysfsMasterPackage}/constraint_{self._id}_time_window_us', 'rt') as f:
            return int(f.read())

    def set_time_window_us(self, time_window_us):
        """
        :param time_window_us: int МИКРОСЕКУНДЫ
        """
        with open(f'{self._sysfsMasterPackage}/constraint_{self._id}_time_window_us', 'wt') as f:
            f.write(str(time_window_us))


class ConstraintLongTerm(Constraint):
    """Long Term or PL1"""
    def __init__(self, sysfsMasterPackage):
        super().__init__(sysfsMasterPackage, 0)


class ConstraintShortTerm(Constraint):
    """Short Term or PL2"""
    def __init__(self, sysfsMasterPackage):
        super().__init__(sysfsMasterPackage, 1)


class IntelPowerCappingFramework:
    """Интеловский фреймворк управления питанием их процессоров.
        Intel "Running Average Power Limit" (RAPL) technology
    """
    _SYSFS_MASTER_PACKAGE_MSR = '/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0'
    _SYSFS_MASTER_PACKAGE_MMIO = '/sys/devices/virtual/powercap/intel-rapl-mmio/intel-rapl-mmio:0'
    """Мы будем управлять только всем пакетом (core, outcore, dram)"""

    _linux_energy_uj_file = None

    def __init__(self):
        with open('/sys/devices/virtual/powercap/intel-rapl/enabled', 'rt') as rapl_enable:
            if '1' not in rapl_enable.read():
                raise RuntimeError("Intel \"Running Average Power Limit\" (RAPL) technology wasn't enabled.")
        with open(f'{self._SYSFS_MASTER_PACKAGE_MSR}/enabled', 'rt') as rapl_matercpu_enable:
            if '1' not in rapl_matercpu_enable.read():
                raise RuntimeError("Intel \"Running Average Power Limit\" (RAPL) technology wasn't enabled for CPU.")

        self.long_term = ConstraintLongTerm(self._SYSFS_MASTER_PACKAGE_MSR)
        self.short_term = ConstraintShortTerm(self._SYSFS_MASTER_PACKAGE_MSR)
        self.mmio = lambda: None
        setattr(self.mmio, 'long_term', ConstraintLongTerm(self._SYSFS_MASTER_PACKAGE_MMIO))
        setattr(self.mmio, 'short_term', ConstraintShortTerm(self._SYSFS_MASTER_PACKAGE_MMIO))


    def get_energy_uj(self):
        """"Текущие значение счётчика энергии.
        :return: int МИКРОДЖОУЛЯХ
        """
        if '_linux_energy_uj_file' not in self:
            self._linux_energy_uj_file = open(self._SYSFS_MASTER_PACKAGE_MSR + '/energy_uj', 'rt')
        return int(self._linux_energy_uj_file.read())

    def disable_mmio_rapl(self):
        with open(f'{self._SYSFS_MASTER_PACKAGE_MMIO}/enabled', 'wt') as f:
            f.write(str(0))

    def enable_mmio_rapl(self):
        with open(f'{self._SYSFS_MASTER_PACKAGE_MMIO}/enabled', 'wt') as f:
            f.write(str(0))

    def get_mmio_rapl_enabled(self):
        with open(self._SYSFS_MASTER_PACKAGE_MMIO + '/enabled', 'rt') as f:
            return True if '1' in f.read() else False

    def get_current_watts(self, time_interval=1):
        """ В этом верменном промежутке была средняя мощьность"""
        if time_interval <= 0:
            raise ValueError("time_interval <= 0 is meaninglessly")
        before = self.get_energy_uj()
        time.sleep(time_interval)
        after = self.get_energy_uj()
        return (after - before) / float(time_interval)

    def __del__(self):
        if self._linux_energy_uj_file is not None:
            del self._linux_energy_uj_file


class BatteryService:
    """Управление батареей ноутбука"""
    _LINUX_SYSFS_FILE = '/sys/class/power_supply/BAT0/uevent'
    _uevent_file = None

    def __init__(self):
        self._uevent_file = open(self._LINUX_SYSFS_FILE, 'rt')

    def __del__(self):
        self._uevent_file.close()

    def get(self):
        power_now = None
        status = None
        capacity = None
        cycle_count = None
        energy_full = None
        energy_now = None
        energy_full_design = None

        for line in self._uevent_file.read().split('\n')[0:-2]:
            key, value = line.split('=')
            if key == 'POWER_SUPPLY_STATUS':
                status = Battery.Status.Discharging if value == 'Discharging' else Battery.Status.Charging
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
        self._uevent_file.seek(0)

        time_now = datetime.datetime.now()
        return Battery(time_now,
                       power_now,
                       status,
                       capacity,
                       cycle_count,
                       energy_full,
                       energy_now,
                       energy_full_design
                       )

    def get_charge_control_thresholds(self):
        """
        :return: (start_charge: int, stop_charge: int)
        """
        with open('/sys/devices/platform/huawei-wmi/charge_control_thresholds', 'rt') as f:
            start_charge, stop_charge = f.read().replace('\n', '').split(' ')
            return start_charge, stop_charge

    def set_charge_control_thresholds(self, start_charge: int, stop_charge: int):
        if start_charge < 0 or start_charge > 100 or stop_charge <= 0 or stop_charge > 100:
            raise ValueError('start_charge < 0 or start_charge > 100 or stop_charge <= 0 or stop_charge > 100')
        with open('/sys/devices/platform/huawei-wmi/charge_control_thresholds', 'rt') as f:
            f.write(f"{start_charge} {stop_charge}")

