# подсветка клавиатуры потребляет 0.5 Ватт и 1.0 Ватт
# экран потребляет 3,6 ВАтт на 100%
# wireless почти не тратит энергию
import datetime
import os
import threading
import time
import logging
import deprecation

import dbus_proxy
from model import Battery, BatteryPowerNow, BatteryEnergyNow
from utils import RingBuffer


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler())


class GTSysFsDriver:
    """Generic Thermal Sysfs driver
    see else: https://docs.kernel.org/driver-api/thermal/sysfs-api.html
    """
    thermal_points = None
    """list[HWMONClass]"""

    class HWMONClass:
        def __init__(self, base_path, number_temp):
            self.base_path = base_path
            self.number_temp = number_temp
            self.file_critic_temperature = open(os.path.join(self.base_path, f'temp{self.number_temp}_crit'), 'rt')
            self.file_critic_alarm_temperature = open(os.path.join(self.base_path, f'temp{self.number_temp}_crit_alarm'), 'rt')
            self.file_input = open(os.path.join(self.base_path, f'temp{self.number_temp}_input'), 'rt')
            self.file_label = open(os.path.join(self.base_path, f'temp{self.number_temp}_label'), 'rt')

        @property
        def critic_temperature(self) -> int:
            """
            :return: The degree Celsius
            """
            self.file_critic_temperature.seek(0)
            return int(self.file_critic_temperature.read()) // 1000

        @property
        def critic_alarm_temperature(self) -> bool:
            self.file_critic_alarm_temperature.seek(0)
            return False if '0' in self.file_critic_alarm_temperature.read() else True

        @property
        def input(self) -> int:
            """
            :return: The degree Celsius
            """
            self.file_input.seek(0)
            return int(self.file_input.read()) // 1000

        @property
        def label(self) -> str:
            self.file_label.seek(0)
            return self.file_label.read().replace('\n', '')

    def __init__(self):
        hwmon_i = None
        for hwmon_i in os.listdir('/sys/class/hwmon/'):
            with open(f'/sys/class/hwmon/{hwmon_i}/name', 'rt') as f:
                if 'coretemp' in f.read():
                    break  # we found CPU temperature

        all_files = os.listdir(f'/sys/class/hwmon/{hwmon_i}')
        all_files.sort()
        max_index = 1
        for max_index in range(1,999):
            if f'temp{max_index}_label' in all_files:
                continue
            else:
                max_index -= 1
                break
        self.thermal_points = list()
        for index in range(1, max_index+1):
            self.thermal_points.append(GTSysFsDriver.HWMONClass(f'/sys/class/hwmon/{hwmon_i}', index))


class DPTF:
    """Intel(R) Dynamic Platform and Thermal Framework (DPTF)

    Intel(R) Dynamic Platform and Thermal Framework (DPTF) is a platform level hardware/software solution
    for power and thermal management.
    As a container for multiple power/thermal technologies, DPTF provides a coordinated approach for different policies
    to effect the hardware state of a system.

    See else https://docs.kernel.org/driver-api/thermal/intel_dptf.html
    """
    @staticmethod
    def get_tcc_offset():
        """TCC offset from the critical temperature where hardware will throttle CPU.
        By design the critical temperature is 100 C. But it can be decrees and
        by default it is 10 that mean 100C - 10C = 90C
        """
        with open("/sys/bus/pci/devices/0000:00:04.0/tcc_offset_degree_celsius", 'rt') as f:
            return f.read().replace('\n', '')


class IntelPStateDriver:
    """intel P-state scaling driver that realization Intel SpeedStep Technology"""

    class SpeedShift:
        """Intel SpeedShift aka Hardware P-states.
        У меня не работает почему-то. нет эффекта.
        Если включено, то P состояниями управляет процессор а не драйвер и
        для контроля производительности процессора нужно крутить:
            /sys/devices/system/cpu/cpu*/energy_performance_preference
            /sys/devices/system/cpu/cpu*/energy_performance_available_preferences
        там словами пишешь (универсально для всех процессоров не только intel)
        или же крутить напрямую intel крутилку производительности:
            /sys/devices/system/cpu/cpu*/power/energy_perf_bias"""
        @staticmethod
        def enable():
            if os.getuid() != 0:  # is not "root' user
                dbus_proxy.GetDBusInterfaceProxyOf().Speedshift.Enable()
                return
            with open('/sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost', 'wt') as f:
                f.write('1')

        @staticmethod
        def get():
            with open('/sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost', 'rt') as f:
                return False if '0' in f.read() else True

        @staticmethod
        def disable():
            if os.getuid() != 0:  # is not "root' user
                dbus_proxy.GetDBusInterfaceProxyOf().Speedshift.Disable()
                return
            with open('/sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost', 'wt') as f:
                f.write('0')

    class TurboPstates:
        """Intel allow p_state drive set CPU to turbo P states.
        Изменять бессмысленно.
        Позволять ли драйверу переходить в драйв P states."""

        @staticmethod
        def enable():
            if os.getuid() != 0:  # is not "root' user
                dbus_proxy.GetDBusInterfaceProxyOf().Turbopstates.Enable()
                return
            with open('/sys/devices/system/cpu/intel_pstate/no_turbo', 'wt') as f:
                f.write('0')

        @staticmethod
        def get():
            with open('/sys/devices/system/cpu/intel_pstate/no_turbo', 'rt') as f:
                return True if '0' in f.read() else False

        @staticmethod
        def disable():
            if os.getuid() != 0:  # is not "root' user
                dbus_proxy.GetDBusInterfaceProxyOf().Turbopstates.Disable()
                return
            with open('/sys/devices/system/cpu/intel_pstate/no_turbo', 'wt') as f:
                f.write('1')

    @staticmethod
    def get_energy_perf_bias_for_all_cpu() -> int:
        with open('/sys/devices/system/cpu/cpu0/power/energy_perf_bias', 'rt') as f:
            return int(f.read())

    @staticmethod
    @deprecation.deprecated()
    def set_energy_perf_bias_for_all_cpu(epb: int):
        """The Intel performance and energy bias hint (EPB) is an interface provided by Intel CPUs
        to allow for user space to specify the desired power-performance tradeoff,
        on a scale of 0 (highest performance) to 15 (highest energy savings).
        :param epb: int 0 (highest performance) to 15 (highest energy savings).
        """
        if os.getuid() != 0:  # is not "root' user
            dbus_proxy.GetDBusInterfaceProxyOf().Intelpstatedriver.SetEnergyPerfBiasForAllCpu(epb)
            return
        if epb < 0 or epb > 15:
            raise ValueError('epb: int 0 (highest performance) to 15 (highest energy savings).')
        with open('/sys/devices/system/cpu/possible', 'rt') as f:
            start_id, stop_id = f.read().replace('\n', '').split('-')
            start_id, stop_id = int(start_id), int(stop_id)
        for id in range(start_id, stop_id + 1):
            with open(f"/sys/devices/system/cpu/cpu{id}/power/energy_perf_bias", 'wt') as f:
                f.write(str(epb))


class CpuFrequency:
    """Управление частотами ядер процессора"""
    cpu = []
    _cpu_id = None

    def __init__(self, cpu_id=None):
        if cpu_id is None:
            with open('/sys/devices/system/cpu/possible', 'rt') as f:
                start_id, stop_id = f.read().replace('\n', '').split('-')
                start_id, stop_id = int(start_id), int(stop_id)
            for id in range(start_id, stop_id + 1):
                self.cpu.append(CpuFrequency(id))
            self.cpu = tuple(self.cpu)
        else:
            self._cpu_id = cpu_id

    @staticmethod
    def use_particular_cpu(func):
        def wrapper(*args, **kwargs):
            pass
            if args[0]._cpu_id is None:
                raise RuntimeError('use CpuFrequency().cpu[0].FUNCTION()')
            return func(*args, **kwargs)
        return wrapper

    @use_particular_cpu
    def get_energy_performance_available_preferences(self) -> list:
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/energy_performance_available_preferences', 'rt') as f:
            return f.read().replace('\n', '').split(' ')[:-1]

    @use_particular_cpu
    def get_energy_performance_preference(self) -> str:
        """Current value of the energy vs performance hint for the given policy (or the CPU represented by it)."""
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/energy_performance_preference', 'rt') as f:
            return f.read().replace('\n', '')
    
    @use_particular_cpu
    def set_energy_performance_preference(self, preference: str):
        """Current value of the energy vs performance hint for the given policy (or the CPU represented by it)."""
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/energy_performance_preference', 'wt') as f:
            f.write(preference)

    def set_energy_performance_preference_for_all(self, preference: str):
        if os.getuid() != 0:  # is not "root' user
            dbus_proxy.GetDBusInterfaceProxyOf().Cpufrequency.Setenergyperformancepreferenceforall(preference)
            return
        for c in self.cpu:
            c.set_energy_performance_preference(preference)

    @use_particular_cpu
    def get_driver_name(self):
        """лучше чтобы было intel_pstate"""
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/scaling_driver', 'rt') as f:
            return f.read().replace('\n', '')

    @use_particular_cpu
    def get_scaling_max_freq(self):
        """ Безполезно.
        :return: КИЛЛОГЕРЦЫ 10**3
        """
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/scaling_max_freq', 'rt') as f:
            return int(f.read())

    @use_particular_cpu
    def get_scaling_min_freq(self):
        """ Безполезно.
        :return: КИЛЛОГЕРЦЫ 10**3
        """
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/scaling_min_freq', 'rt') as f:
            return int(f.read())

    @use_particular_cpu
    def get_scaling_cur_freq(self):
        """
        :return: КИЛЛОГЕРЦЫ 10**3
        """
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/scaling_cur_freq', 'rt') as f:
            return int(f.read())

    def get_scaling_available_governors(self):
        """
        :return: list
        """
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/scaling_available_governors', 'rt') as f:
            return f.read().replace('\n','').split(' ')

    @use_particular_cpu
    def get_scaling_governor(self):
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/scaling_governor', 'rt') as f:
            return f.read().replace('\n','')

    @use_particular_cpu
    def set_scaling_governor(self, governor: str):
        """
        :param governor: see CpuFrequency.get_scaling_available_governors
        """
        if os.getuid() != 0:  # is not "root' user
            dbus_proxy.GetDBusInterfaceProxyOf().Cpufrequency.SetScalingGovernor(self._cpu_id, governor)
            return
        with open(f'/sys/devices/system/cpu/cpu{self._cpu_id}/cpufreq/scaling_governor', 'wt') as f:
            return f.write(governor)

    def set_scaling_governor_for_all(self, governor: str):
        for c in self.cpu:
            c.set_scaling_governor(governor)


class Constraint:
    """Ограничение пакета RAPL. Описаны не все параметры. Только обязательные."""
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
        if not hasattr(self, '_power_limit_uw'):
            self._power_limit_uw = open(f'{self._sysfsMasterPackage}/constraint_{self._id}_power_limit_uw', 'rt')
        self._power_limit_uw.seek(0)
        return int(self._power_limit_uw.read())

    def set_power_limit_uw(self, power_limit_uw: int):
        """
        :param power_limit_uw: int МИКРОВАТТЫ
        """
        # TODO: спагетти код. впихнул авторизацию в логику. была обстракция от типа Constraint, а Я опять впихнул
        if os.getuid() != 0:  # is not "root' user
            if self._id == 0:
                dbus_proxy.GetDBusInterfaceProxyOf().Constraintlongterm.SetPowerLimitUw(power_limit_uw)
                return
            elif self._id == 1:
                dbus_proxy.GetDBusInterfaceProxyOf().Constraintshortterm.SetPowerLimitUw(power_limit_uw)
                return
        with open(f'{self._sysfsMasterPackage}/constraint_{self._id}_power_limit_uw', 'wt') as f:
            f.write(str(power_limit_uw))

    def get_time_window_us(self):
        """ МИКРОСЕКУНДЫ
        :return: int
        """
        if not hasattr(self, '_time_window_us'):
            self._time_window_us = open(f'{self._sysfsMasterPackage}/constraint_{self._id}_time_window_us', 'rt')
        self._time_window_us.seek(0)
        return int(self._time_window_us.read())

    def set_time_window_us(self, time_window_us):
        """
        :param time_window_us: int МИКРОСЕКУНДЫ
        """
        # TODO: спагетти код. впихнул авторизацию в логику. была обстракция от типа Constraint, а Я опять впихнул
        if os.getuid() != 0:  # is not "root' user
            if self._id == 0:
                dbus_proxy.GetDBusInterfaceProxyOf().Constraintlongterm.SetTimeWindowUs(time_window_us)
                return
            elif self._id == 1:
                dbus_proxy.GetDBusInterfaceProxyOf().Constraintshortterm.SetTimeWindowUs(time_window_us)
                return
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
        Мы будем управлять только всем пакетом (core, outcore, dram)
    """
    _SYSFS_MASTER_PACKAGE_MSR = '/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0'
    _SYSFS_MASTER_PACKAGE_MMIO = '/sys/devices/virtual/powercap/intel-rapl-mmio/intel-rapl-mmio:0'

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

        self.energy_uj_buffer_by_seconds = RingBuffer(100)
        def update_energy_uj():
            while True:
                self.energy_uj_buffer_by_seconds.append(self.get_energy_uj())
                time.sleep(1.0)
        threading.Thread(daemon=True,
                         target=update_energy_uj
                         ).start()

    def get_energy_uj(self):
        """"Текущие значение счётчика энергии.
        :return: int МИКРОДЖОУЛЯХ
        """
        if os.getuid() != 0:  # is not "root' user
            return dbus_proxy.GetDBusInterfaceProxyOf().Intelpowercappingframework.GetEnergyUj()
        if hasattr(self, '_linux_energy_uj_file'):
            self._linux_energy_uj_file = open(self._SYSFS_MASTER_PACKAGE_MSR + '/energy_uj', 'rt')
        value_str = ''
        while value_str == '':
            value_str = self._linux_energy_uj_file.read()
        value_int = int(value_str)
        return value_int

    def disable_mmio_rapl(self):
        if os.getuid() != 0:  # is not "root' user
            dbus_proxy.GetDBusInterfaceProxyOf().Intelpowercappingframework.DisableMmioRapl()
            return
        with open(f'{self._SYSFS_MASTER_PACKAGE_MMIO}/enabled', 'wt') as f:
            f.write(str(0))

    def enable_mmio_rapl(self):
        if os.getuid() != 0:  # is not "root' user
            dbus_proxy.GetDBusInterfaceProxyOf().Intelpowercappingframework.EnableMmioRapl()
            return
        with open(f'{self._SYSFS_MASTER_PACKAGE_MMIO}/enabled', 'wt') as f:
            f.write(str(1))

    def get_mmio_rapl_enabled(self):
        with open(self._SYSFS_MASTER_PACKAGE_MMIO + '/enabled', 'rt') as f:
            return True if '1' in f.read() else False

    def get_current_watts(self, time_interval=1):
        """ В этом верменном промежутке была средняя мощьность

        :param time_interval int СЕКУНДЫ
        :return: float МИКРОВАТТ"""
        if os.getuid() != 0:  # is not "root' user
            return float(dbus_proxy.GetDBusInterfaceProxyOf().Intelpowercappingframework.GetCurrentWatts(time_interval))
        if time_interval <= 0:
            raise ValueError("time_interval <= 0 is meaninglessly")
        energy_uj = self.energy_uj_buffer_by_seconds.get_last(time_interval + 1)
        return (energy_uj[0] - energy_uj[-1]) / float(time_interval)

    def __del__(self):
        if self._linux_energy_uj_file is not None:
            del self._linux_energy_uj_file


class BatteryService:
    """Управление батареей ноутбука"""
    _LINUX_SYSFS_FILE = '/sys/class/power_supply/BAT0/uevent'
    _LINUX_SYSFS_POWERNOW = '/sys/class/power_supply/BAT0/power_now'
    _LINUX_SYSFS_ENERGYNOW = '/sys/class/power_supply/BAT0/energy_now'
    _uevent_file = None
    _powernow_file = None
    _energynow_file = None

    def __init__(self):
        self._uevent_file = open(self._LINUX_SYSFS_FILE, 'rt')
        self._powernow_file = open(self._LINUX_SYSFS_POWERNOW, 'rt')
        self._energynow_file = open(self._LINUX_SYSFS_ENERGYNOW, 'rt')

    def __del__(self):
        self._uevent_file.close()
        self._powernow_file.close()
        self._energynow_file.close()

    def get_power_now(self):
        self._powernow_file.seek(0)
        return BatteryPowerNow(time.time_ns(), int(self._powernow_file.read()))

    def get_energy_now(self):
        self._energynow_file.seek(0)
        return BatteryEnergyNow(time.time_ns(), int(self._energynow_file.read()))

    def get(self) -> Battery:
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
            return int(start_charge), int(stop_charge)

    def set_charge_control_thresholds(self, start_charge: int, stop_charge: int):
        if os.getuid() != 0:
            dbus_proxy.GetDBusInterfaceProxyOf().Batteryservice.Setchargecontrolthresholds(start_charge, stop_charge)
            return
        if start_charge < 0 or start_charge > 99 or stop_charge < 1 or stop_charge > 100 or start_charge > stop_charge:
            raise ValueError('start_charge < 0 or start_charge > 99 or stop_charge < 1 or stop_charge > 100 or start_charge > stop_charge')
        with open('/sys/devices/platform/huawei-wmi/charge_control_thresholds', 'wt') as f:
            f.write(f"{start_charge} {stop_charge}")

    @staticmethod
    def calc_times(data):
        time = (data[-1].date - data[0].date).seconds
        d_energy_now = data[0].energy_now - data[-1].energy_now
        speed = d_energy_now / time  # (seconds). Микро-Ват-Часы делятся на секунды. да-да... Я знаю
        if speed != 0:
            if data[0].status == Battery.Status.Discharging:
                remaining_time_to_live = (data[-1].energy_now - (data[-1].energy_full * 6 / 100)) / speed
                """В строчке выше высчитывается оставшиеся время жизни батареи.
                   Преполагается что батарея может разрядиться только до 6%.
                   formula: (<энергии сейчас> - <6% от полной емкости>) / <скорость разрядки>"""
                datetime_to_die = datetime.datetime.now() + datetime.timedelta(seconds=remaining_time_to_live)
                remaining_time_to_live = datetime.timedelta(seconds=remaining_time_to_live)
                full_time_live = data[0].energy_full / speed
                full_time_live = datetime.timedelta(seconds=full_time_live)

                print(f"Status: {data[0].status}")
                print(f"{datetime_to_die.ctime()} time to die")
                print(f"{remaining_time_to_live} rest time to live in hours")
                print(f"{full_time_live} full time to live in hours")
            elif data[0].status == Battery.Status.Charging:
                speed = -speed
                remaining_time_to_done = (data[-1].energy_full - data[-1].energy_now) / speed
                datetime_to_done = datetime.datetime.now() + datetime.timedelta(seconds=remaining_time_to_done)

                print(f"Status: {data[0].status}")
                print(f"{datetime_to_done.ctime()} time to done")
                print(f"{datetime.timedelta(seconds=remaining_time_to_done)} rest time to done")
            else:
                print("WTF? unknow battary status...")
        elif speed == 0:
            print('Status: FULL')

