#!/usr/bin/env python3
"""
Демон. Работает из под привилегированного пользоваталя root.
Обеспечивает управление всеми системами питания ноутбука.
Предоставляет доступ к информации об энергопотреблении ноутбука.
"""
from dasbus.connection import SystemMessageBus
from dasbus.loop import EventLoop as DasBusEventLoop
import logging

import dbus_proxy

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def registration_dbus_interfaces():
    bus = SystemMessageBus()
    bus.register_service(dbus_proxy.DBUS_SERVICE_NAME)

    objs = [
        dbus_proxy.Intelpstatedriver(),
        dbus_proxy.Turbopstates(),
        dbus_proxy.Speedshift(),
        dbus_proxy.Cpufrequency(),
        dbus_proxy.Intelpowercappingframework(),
        dbus_proxy.Constraintlongterm(),
        dbus_proxy.Constraintshortterm(),
        dbus_proxy.Batteryservice()
    ]
    for obj in objs:
        bus.publish_object(obj.OBJECT_PATH, obj)


def main():
    registration_dbus_interfaces()

    loop = DasBusEventLoop()
    loop.run()


if __name__ == '__main__':
    _logger.setLevel(logging.DEBUG)
    _logger.addHandler(logging.StreamHandler())
    main()
