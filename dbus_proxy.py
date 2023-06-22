"""
В именах методов подчеркивания нельзя
"""
import grp
import os
import logging
from dasbus.server.interface import dbus_interface, dbus_signal
from dasbus.connection import SystemMessageBus
from dasbus.client.proxy import InterfaceProxy
from dasbus.typing import Str, Int, Double, Bool

import service


DBUS_SERVICE_NAME = "world.nkt.laptoppower"

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler())


@dbus_interface("world.nkt.laptoppower.intelpstatedriver")
class Intelpstatedriver:
    OBJECT_INTERFACE = "world.nkt.laptoppower.intelpstatedriver"
    OBJECT_PATH = '/intelpstatedriver'

    def SetEnergyPerfBiasForAllCpu(self, epb: Int) -> None:
        service.IntelPStateDriver.set_energy_perf_bias_for_all_cpu(epb)


@dbus_interface("world.nkt.laptoppower.intelpstatedriver.speedshift")
class Speedshift:
    OBJECT_INTERFACE = "world.nkt.laptoppower.intelpstatedriver.speedshift"
    OBJECT_PATH = '/intelpstatedriver/speedshift'

    def Enable(self):
        service.IntelPStateDriver.SpeedShift.enable()

    def Disable(self):
        service.IntelPStateDriver.SpeedShift.disable()


@dbus_interface("world.nkt.laptoppower.intelpstatedriver.turbopstates")
class Turbopstates:
    OBJECT_INTERFACE = "world.nkt.laptoppower.intelpstatedriver.turbopstates"
    OBJECT_PATH = '/intelpstatedriver/turbopstates'

    def Enable(self):
        service.IntelPStateDriver.TurboPstates.enable()

    def Disable(self):
        service.IntelPStateDriver.TurboPstates.disable()


@dbus_interface("world.nkt.laptoppower.cpufrequency")
class Cpufrequency:
    OBJECT_INTERFACE = "world.nkt.laptoppower.cpufrequency"
    OBJECT_PATH = '/intelpstatedriver/cpufrequency'

    def SetScalingGovernor(self, cpu_id: Int, governor: Str):
        service.CpuFrequency().cpu[cpu_id].set_scaling_governor(governor)


@dbus_interface("world.nkt.laptoppower.intelpowercappingframework")
class Intelpowercappingframework:
    OBJECT_INTERFACE = "world.nkt.laptoppower.intelpowercappingframework"
    OBJECT_PATH = '/intelpstatedriver/intelpowercappingframework'

    def __init__(self):
        self.ipowerframe = service.IntelPowerCappingFramework()

    def GetEnergyUj(self) -> Str:
        # TODO не умею через dbus передавать double
        return str(self.ipowerframe.get_energy_uj())

    def DisableMmioRapl(self):
        self.ipowerframe.disable_mmio_rapl()

    def EnableMmioRapl(self):
        self.ipowerframe.enable_mmio_rapl()

    def GetCurrentWatts(self, time_interval: Int) -> Str:
        # TODO не умею через dbus передавать double
        return str(self.ipowerframe.get_current_watts(int(time_interval)))


@dbus_interface("world.nkt.laptoppower.intelpowercappingframework.long_term")
class Constraintlongterm:
    OBJECT_INTERFACE = "world.nkt.laptoppower.intelpowercappingframework.long_term"
    OBJECT_PATH = '/intelpstatedriver/intelpowercappingframework/long_term'

    def __init__(self):
        self.ipowerframe = service.IntelPowerCappingFramework()

    def SetPowerLimitUw(self, limit: Int):
        self.ipowerframe.long_term.set_power_limit_uw(limit)

    def SetTimeWindowUs(self, limit: Int):
        self.ipowerframe.long_term.set_time_window_us(limit)


@dbus_interface("world.nkt.laptoppower.intelpowercappingframework.short_term")
class Constraintshortterm:
    OBJECT_INTERFACE = "world.nkt.laptoppower.intelpowercappingframework.short_term"
    OBJECT_PATH = '/intelpstatedriver/intelpowercappingframework/short_term'

    def __init__(self):
        self.ipowerframe = service.IntelPowerCappingFramework()

    def SetPowerLimitUw(self, limit: Int):
        self.ipowerframe.short_term.set_power_limit_uw(limit)

    def SetTimeWindowUs(self, limit: Int):
        self.ipowerframe.short_term.set_time_window_us(limit)


class GetDBusInterfaceProxyOf:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GetDBusInterfaceProxyOf, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.bus = SystemMessageBus()
        # dasbus.client.observer import DBusObserver IS A SHIT AND DONT WORKS
        #if grp.getgrnam('wheel').gr_gid not in os.getgroups():
        #    msg = "can't connect to bus and take a proxy"
        #    _logger.error(msg)
        #    raise RuntimeError(msg)

    @property
    def Intelpstatedriver(self):
        if not hasattr(self, '_intelpstatedriver'):
            self._intelpstatedriver = InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Intelpstatedriver.OBJECT_PATH, Intelpstatedriver.OBJECT_INTERFACE)
        return self._intelpstatedriver

    @property
    def Speedshift(self):
        if not hasattr(self, '_speedshift'):
            self._speedshift = InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Speedshift.OBJECT_PATH, Speedshift.OBJECT_INTERFACE)
        return self._speedshift

    @property
    def Turbopstates(self):
        if not hasattr(self, '_turbopstates'):
            self._turbopstates = InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Turbopstates.OBJECT_PATH, Turbopstates.OBJECT_INTERFACE)
        return self._turbopstates

    @property
    def Cpufrequency(self):
        if not hasattr(self, '_cpufrequency'):
            self._cpufrequency = InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Cpufrequency.OBJECT_PATH, Cpufrequency.OBJECT_INTERFACE)
        return self._cpufrequency

    @property
    def Intelpowercappingframework(self):
        if not hasattr(self, '_intelpowercappingframework'):
            self._intelpowercappingframework = InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Intelpowercappingframework.OBJECT_PATH, Intelpowercappingframework.OBJECT_INTERFACE)
        return self._intelpowercappingframework

    @property
    def Constraintlongterm(self):
        if not hasattr(self, '_constraintlongterm'):
            self._constraintlongterm = InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Constraintlongterm.OBJECT_PATH, Constraintlongterm.OBJECT_INTERFACE)
        return self._constraintlongterm

    @property
    def Constraintshortterm(self):
        if not hasattr(self, '_constraintshortterm'):
            self._constraintshortterm = InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Constraintshortterm.OBJECT_PATH, Constraintshortterm.OBJECT_INTERFACE)
        return self._constraintshortterm
