import datetime
from model import Battery
import os


class IntelPowerCappingFramework:
    """Интеловский фреймворк управления питанием их процессоров.
        Intel "Running Average Power Limit" (RAPL) technology
    """
    _SYSFS_MASTER_PACKAGE = '/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0'
    """Мы будем управлять только всем пакетом (core, outcore, dram)"""

    class Constraint:
        """Ограничение пакета RAPL. Описаны не все. Только обязательные"""
        name = None

        def __init__(self, sysfsMasterPackage, id):
            self._sysfsMasterPackage = sysfsMasterPackage
            self._id = id
            # TODO: name is optional by docs (may be errors)
            #  https://www.kernel.org/doc/html/next/power/powercap/powercap.html
            with open(f'{self._sysfsMasterPackage}/constraint_{self._id}_name', 'rt') as f:
                self.name = f.read().replace('\n','')

        @staticmethod
        def find_all_constraint_in_package(sysfsMasterPackage):
            """Все ограничения пакета. Я переусердствовал.
            На самом деле ограничения всего два long_term и short_term.
            И они даже исветны по номерами. 0 и 1 соответственно.
            """
            ids = set()
            for name in os.listdir(sysfsMasterPackage):
                if 'constraint' in name:
                    ids.add(int(name.split('_')[1]))
            constraints = [IntelPowerCappingFramework.Constraint(sysfsMasterPackage, id) for id in ids]
            return constraints

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

    def __init__(self):
        with open('/sys/devices/virtual/powercap/intel-rapl/enabled', 'rt') as rapl_enable:
            if '1' not in rapl_enable.read():
                raise RuntimeError("Intel \"Running Average Power Limit\" (RAPL) technology wasn't enabled.")
        with open(f'{self._SYSFS_MASTER_PACKAGE}/enabled', 'rt') as rapl_matercpu_enable:
            if '1' not in rapl_matercpu_enable.read():
                raise RuntimeError("Intel \"Running Average Power Limit\" (RAPL) technology wasn't enabled for CPU.")

        constraints = IntelPowerCappingFramework.Constraint.find_all_constraint_in_package(self._SYSFS_MASTER_PACKAGE)
        # Reflection
        for c in constraints:
            self.__setattr__(c.name, c)

    def get_energy_uj(self):
        """"Текущие значение счётчика энергии.
        :return: int МИКРОДЖОУЛЯХ
        """
        with open(self._SYSFS_MASTER_PACKAGE + '/energy_uj', 'rt') as f:
            return int(f.read())


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


