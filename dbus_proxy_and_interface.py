"""
В именах методов подчеркивания нельзя
"""
from dasbus.server.interface import dbus_interface, dbus_signal
from dasbus.connection import SystemMessageBus
from dasbus.client.proxy import InterfaceProxy
from dasbus.typing import Str, Int, Double, Bool
import service

DBUS_SERVICE_NAME = "world.nkt.laptoppower"


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

    def SetScalingGovernor(self, governor: Str):
        service.CpuFrequency().set_scaling_governor(governor)


@dbus_interface("world.nkt.laptoppower.intelpowercappingframework")
class Intelpowercappingframework:
    OBJECT_INTERFACE = "world.nkt.laptoppower.intelpowercappingframework"
    OBJECT_PATH = '/intelpstatedriver/intelpowercappingframework'

    def GetEnergyUj(self) -> Str:
        return str(service.IntelPowerCappingFramework().get_energy_uj())

    def DisableMmioRapl(self):
        service.IntelPowerCappingFramework().disable_mmio_rapl()

    def EnableMmioRapl(self):
        service.IntelPowerCappingFramework().enable_mmio_rapl()

    def GetCurrentWatts(self) -> Str:
        return str(service.IntelPowerCappingFramework().get_current_watts())


@dbus_interface("world.nkt.laptoppower.intelpowercappingframework.long_term")
class Constraintlongterm:
    OBJECT_INTERFACE = "world.nkt.laptoppower.intelpowercappingframework.long_term"
    OBJECT_PATH = '/intelpstatedriver/intelpowercappingframework/long_term'

    def SetPowerLimitUw(self, limit: Int):
        service.IntelPowerCappingFramework().long_term.set_power_limit_uw(limit)

    def SetTimeWindowUs(self, limit: Int):
        service.IntelPowerCappingFramework().long_term.set_time_window_us(limit)


@dbus_interface("world.nkt.laptoppower.intelpowercappingframework.short_term")
class Constraintshortterm:
    OBJECT_INTERFACE = "world.nkt.laptoppower.intelpowercappingframework.short_term"
    OBJECT_PATH = '/intelpstatedriver/intelpowercappingframework/short_term'

    def SetPowerLimitUw(self, limit: Int):
        service.IntelPowerCappingFramework().short_term.set_power_limit_uw(limit)

    def SetTimeWindowUs(self, limit: Int):
        service.IntelPowerCappingFramework().short_term.set_time_window_us(limit)


class GetDBusInterfaceProxyOf:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GetDBusInterfaceProxyOf, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.bus = SystemMessageBus()

    @property
    def Intelpstatedriver(self):
        InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Intelpstatedriver.OBJECT_PATH, Intelpstatedriver.OBJECT_INTERFACE)

    @property
    def Speedshift(self):
        InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Speedshift.OBJECT_PATH, Speedshift.OBJECT_INTERFACE)

    @property
    def Turbopstates(self):
        InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Turbopstates.OBJECT_PATH, Turbopstates.OBJECT_INTERFACE)

    @property
    def Cpufrequency(self):
        InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Cpufrequency.OBJECT_PATH, Cpufrequency.OBJECT_INTERFACE)

    @property
    def Intelpowercappingframework(self):
        InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Intelpowercappingframework.OBJECT_PATH,
                       Intelpowercappingframework.OBJECT_INTERFACE)

    @property
    def Constraintlongterm(self):
        InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Constraintlongterm.OBJECT_PATH, Constraintlongterm.OBJECT_INTERFACE)

    @property
    def Constraintshortterm(self):
        InterfaceProxy(self.bus, DBUS_SERVICE_NAME, Constraintshortterm.OBJECT_PATH,
                       Constraintshortterm.OBJECT_INTERFACE)
