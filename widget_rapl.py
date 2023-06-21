#!/usr/bin/env python3
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt
import sys
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import logging

from service import IntelPowerCappingFramework
from utils import RingBuffer


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler())


class PlotViewer(QtWidgets.QWidget):

    doubleClickAction = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(PlotViewer, self).__init__(parent)

        self.figure = plt.figure(figsize=(5, 5))
        self.figureCanvas = FigureCanvas(self.figure)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.figureCanvas)
        self.setLayout(layout)

        self.intelrapl = IntelPowerCappingFramework()
        self.buffer = RingBuffer(30)
        self.buffer.fill_by_object(0)
        self.interval = 3

        self.refrash()
        self.timer = QTimer()
        self.timer.timeout.connect(self.refrash)
        self.timer.start(self.interval*1000)

    def refrash(self):
        x = range(self.buffer.size)
        w = self.intelrapl.get_current_watts(self.interval) / float(10 ** 6)
        self.buffer.append(w)
        y = self.buffer.get_last(self.buffer.size)

        ax = self.figure.add_subplot(111)
        ax.plot(x, y, linewidth=2.0)
        ax.set(xlabel='time (s)', ylabel='Watts', ylim=(0, 30))
        ax.grid()
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()


class RAPLWidget(QWidget):

    def __init__(self):
        super(RAPLWidget, self).__init__()

        ui_file_name = "widget_rapl.ui"
        uic.loadUi(ui_file_name, self)

        self.raplservice = IntelPowerCappingFramework()

        self.timer = QTimer()
        self.timer.timeout.connect(self.rapl_refresh)
        self.timer.start(2000)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(PlotViewer())
        self.widget_graph.setLayout(layout)

        self.pushButton_edit.clicked.connect(self.pushButton_edit_clicked)
        self.pushButton_cancel.clicked.connect(self.pushButton_cancel_clicked)
        self.pushButton_apply.clicked.connect(self.pushButton_apply_clicked)

    def pushButton_apply_clicked(self):
        mmio_enabled = self.checkBox_mmio_enabled.checkState() == Qt.CheckState.Checked
        if mmio_enabled:
            self.raplservice.enable_mmio_rapl()
        else:
            self.raplservice.disable_mmio_rapl()
        self.raplservice.long_term.set_power_limit_uw(int(self.doubleSpinBox_msr_pl1.value() * float(10 ** 6)))
        self.raplservice.long_term.set_time_window_us(int(self.doubleSpinBox_msr_pl1tw.value() * float(10 ** 6)))
        self.raplservice.short_term.set_power_limit_uw(int(self.doubleSpinBox_msr_pl2.value() * float(10 ** 6)))
        self.raplservice.short_term.set_time_window_us(int(self.doubleSpinBox_msr_pl2tw.value() * float(10 ** 6)))

        self.stackedWidget_button.setCurrentIndex(0)
        self.stackedWidget_rapl.setCurrentIndex(0)

    def pushButton_cancel_clicked(self):
        self.stackedWidget_button.setCurrentIndex(0)
        self.stackedWidget_rapl.setCurrentIndex(0)

    def pushButton_edit_clicked(self):
        self.stackedWidget_button.setCurrentIndex(1)
        self.stackedWidget_rapl.setCurrentIndex(1)

        self.doubleSpinBox_msr_pl1.setValue(
            self.raplservice.long_term.get_power_limit_uw() / float(10 ** 6)
        )
        self.doubleSpinBox_msr_pl1tw.setValue(
            self.raplservice.long_term.get_time_window_us() / float(10 ** 6)
        )
        self.doubleSpinBox_msr_pl2.setValue(
            self.raplservice.short_term.get_power_limit_uw() / float(10 ** 6)
        )
        self.doubleSpinBox_msr_pl2tw.setValue(
            self.raplservice.short_term.get_time_window_us() / float(10 ** 6)
        )
        if self.raplservice.get_mmio_rapl_enabled():
            self.checkBox_mmio_enabled.setChecked(True)
        else:
            self.checkBox_mmio_enabled.setChecked(False)

        self.lcdNumber_mmio_pl1_2.display(
            str(
                self.raplservice.mmio.long_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.lcdNumber_mmio_pl1tw_2.display(
            str(
                self.raplservice.mmio.long_term.get_time_window_us() / float(10 ** 6)
            )
        )
        self.lcdNumber_mmio_pl2_2.display(
            str(
                self.raplservice.mmio.short_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.lcdNumber_mmio_pl2tw_2.display(
            str(
                self.raplservice.mmio.short_term.get_time_window_us() / float(10 ** 6)
            )
        )

    def rapl_refresh(self):
        self.lcdNumber_watts.display(
            str(
                self.raplservice.get_current_watts(3) / float(10 ** 6)
            )
        )
        self.lcdNumber_msr_pl1.display(
            str(
                self.raplservice.long_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.lcdNumber_msr_pl1tw.display(
            str(
                self.raplservice.long_term.get_time_window_us() / float(10 ** 6)
            )
        )
        self.lcdNumber_msr_pl2.display(
            str(
                self.raplservice.short_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.lcdNumber_msr_pl2tw.display(
            str(
                self.raplservice.short_term.get_time_window_us() / float(10 ** 6)
            )
        )
        if self.raplservice.get_mmio_rapl_enabled():
            self.checkBox_mmio_enabled_ro.setChecked(True)
        else:
            self.checkBox_mmio_enabled_ro.setChecked(False)
        self.lcdNumber_mmio_pl1.display(
            str(
                self.raplservice.mmio.long_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.lcdNumber_mmio_pl1tw.display(
            str(
                self.raplservice.mmio.long_term.get_time_window_us() / float(10 ** 6)
            )
        )
        self.lcdNumber_mmio_pl2.display(
            str(
                self.raplservice.mmio.short_term.get_power_limit_uw() / float(10 ** 6)
            )
        )
        self.lcdNumber_mmio_pl2tw.display(
            str(
                self.raplservice.mmio.short_term.get_time_window_us() / float(10 ** 6)
            )
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = RAPLWidget()
    w.show()
    sys.exit(app.exec())
