# File: main.py
import sys
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QFile, QIODevice, QTimer

from service import IntelPowerCappingFramework


class RAPLWidget(QWidget):

    def __init__(self):
        super(RAPLWidget, self).__init__()

        ui_file_name = "widget_rapl.ui"
        ui_file = QFile(ui_file_name)
        ui_file.open(QIODevice.ReadOnly)
        loader = QUiLoader()
        self.raplw = loader.load(ui_file, self)
        ui_file.close()

        self.raplservice = IntelPowerCappingFramework()

        self.timer = QTimer()
        self.timer.timeout.connect(self.rapl_refresh)
        self.timer.start(1000)

    def rapl_refresh(self):
        self.raplw.lcdNumber_msr_pl1.display(
            str(
                self.raplservice.long_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.raplw.lcdNumber_msr_pl1tw.display(
            str(
                self.raplservice.long_term.get_time_window_us() / float(10 ** 6)
            )
        )
        self.raplw.lcdNumber_msr_pl2.display(
            str(
                self.raplservice.short_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.raplw.lcdNumber_msr_pl2tw.display(
            str(
                self.raplservice.short_term.get_time_window_us() / float(10 ** 6)
            )
        )
        if self.raplservice.get_mmio_rapl_enabled():
            self.raplw.checkBox_mmio.setChecked(True)
        self.raplw.lcdNumber_mmio_pl1.display(
            str(
                self.raplservice.mmio.long_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.raplw.lcdNumber_msr_pl1tw.display(
            str(
                self.raplservice.mmio.long_term.get_time_window_us() / float(10 ** 6)
            )
        )
        self.raplw.lcdNumber_mmio_pl2.display(
            str(
                self.raplservice.mmio.short_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.raplw.lcdNumber_mmio_pl2tw.display(
            str(
                self.raplservice.mmio.short_term.get_time_window_us() / float(10 ** 6)
            )
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = RAPLWidget()
    w.show()
    sys.exit(app.exec())
