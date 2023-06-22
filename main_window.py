import sys

from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6 import uic, QtWidgets, QtCore
from PyQt6.QtCore import QTimer, Qt
import logging
from widget_rapl import RAPLWidget
from service import IntelPStateDriver, CpuFrequency

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file_name = "mainwindow.ui"
        uic.loadUi(ui_file_name, self)
        rapl = RAPLWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(rapl)
        self.tab_rapl.setLayout(layout)

        self.menu.triggered.connect(QtCore.QCoreApplication.instance().quit)

        self.checkBox_speedshift.stateChanged.connect(self.checkBox_speedshift_stateChanged)
        self.checkBox_turbo_pstates.stateChanged.connect(self.checkBox_turbo_pstates_stateChanged)
        self.spinBox_intel_epb.valueChanged.connect(self.spinBox_intel_epb_valueChanged)

        # --- Logic --
        self.cpuFrequency = CpuFrequency()

        # --- again UI ---
        self.label_driver_name.setText(self.cpuFrequency.cpu[0].get_driver_name())
        self.comboBox_scaling_governor.addItems(self.cpuFrequency.cpu[0].get_scaling_available_governors())
        self.comboBox_scaling_governor.setCurrentText(self.cpuFrequency.cpu[0].get_scaling_governor())
        self.comboBox_scaling_governor.currentTextChanged.connect(self.comboBox_scaling_governor_currentTextChanged)

        # --- Timers ---
        self.timer_update_tab_intelpstate = QTimer()
        self.timer_update_tab_intelpstate.timeout.connect(self.update_tab_intelpstate)
        self.timer_update_tab_intelpstate.start(2000)
        self.timer_update_tab_cpufrequency = QTimer()
        self.timer_update_tab_cpufrequency.timeout.connect(self.update_timer_update_tab_cpufrequency)
        self.timer_update_tab_cpufrequency.start(2000)

    def comboBox_scaling_governor_currentTextChanged(self, text):
        self.cpuFrequency.set_scaling_governor_for_all(text)

    def update_timer_update_tab_cpufrequency(self):
        self.comboBox_scaling_governor.setCurrentText(self.cpuFrequency.cpu[0].get_scaling_governor())

    def update_tab_intelpstate(self):
        self.checkBox_speedshift.setChecked(IntelPStateDriver.SpeedShift.get())
        self.checkBox_turbo_pstates.setChecked(IntelPStateDriver.TurboPstates.get())
        self.spinBox_intel_epb.setValue(IntelPStateDriver.get_energy_perf_bias_for_all_cpu()) # will emit valueChanged()

    def checkBox_speedshift_stateChanged(self, state):
        if not (self.checkBox_speedshift.checkState() == Qt.CheckState.Checked != IntelPStateDriver.SpeedShift.get()):
            return
        if self.checkBox_speedshift.checkState() == Qt.CheckState.Checked:
            IntelPStateDriver.SpeedShift.enable()
        else:
            IntelPStateDriver.SpeedShift.disable()

    def checkBox_turbo_pstates_stateChanged(self, state):
        if not (self.checkBox_turbo_pstates.checkState() == Qt.CheckState.Checked != IntelPStateDriver.TurboPstates.get()):
            return
        if self.checkBox_turbo_pstates.checkState() == Qt.CheckState.Checked:
            IntelPStateDriver.TurboPstates.enable()
        else:
            IntelPStateDriver.TurboPstates.disable()

    def spinBox_intel_epb_valueChanged(self, value):
        IntelPStateDriver.set_energy_perf_bias_for_all_cpu(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
