#!/usr/bin/env python3
"""
Демон. Работает из под привилегированного пользоваталя root.
Обеспечивает управление всеми системами питания ноутбука.
Предоставляет доступ к информации об энергопотреблении ноутбука.
"""
import time
from dasbus.connection import SystemMessageBus, SessionMessageBus
from dasbus.server.interface import dbus_interface, dbus_signal
from dasbus.server.container import DBusContainer
from dasbus.typing import Str, Int, Double, Bool
from dasbus.loop import EventLoop as DasBusEventLoop
import threading
import logging

import service
import dbus_proxy_and_interface

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler())


DBUS_OBJECT_NAME = ""
DBUS_INTERFACE_NAME = ""


def my_loop():
    try:
        while True:
            pass
    except KeyboardInterrupt:
        return


def main():
    bus = SystemMessageBus()
    bus.register_service(dbus_proxy_and_interface.DBUS_SERVICE_NAME)

    objs = [
        dbus_proxy_and_interface.Intelpstatedriver(),
        dbus_proxy_and_interface.Turbopstates(),
        dbus_proxy_and_interface.Speedshift(),
        dbus_proxy_and_interface.Cpufrequency(),
        dbus_proxy_and_interface.Intelpowercappingframework(),
        dbus_proxy_and_interface.Constraintlongterm(),
        dbus_proxy_and_interface.Constraintshortterm(),
    ]
    for obj in objs:
        bus.publish_object(obj.OBJECT_PATH, obj)

    threading.Thread(target=my_loop).start()
    loop = DasBusEventLoop()
    loop.run()


if __name__ == '__main__':
    _logger.setLevel(logging.DEBUG)
    main()
