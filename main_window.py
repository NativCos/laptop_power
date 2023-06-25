#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QMainWindow, QApplication, QVBoxLayout
from PySide6 import QtWidgets, QtCore
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QTimer, Qt
import logging
from widget_rapl import RAPLWidget
from service import IntelPStateDriver, CpuFrequency, BatteryService

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file_name = "main_window.ui"
        loader = QUiLoader(self)
        self.ui = loader.load(ui_file_name)
        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)
        rapl = RAPLWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(rapl)
        self.ui.tab_rapl.setLayout(layout)

        self.ui.menu.triggered.connect(QtCore.QCoreApplication.instance().quit)

        self.ui.checkBox_speedshift.stateChanged.connect(self.checkBox_speedshift_stateChanged)
        self.ui.checkBox_turbo_pstates.stateChanged.connect(self.checkBox_turbo_pstates_stateChanged)
        self.ui.spinBox_intel_epb.valueChanged.connect(self.spinBox_intel_epb_valueChanged)

        # --- Logic --
        self.cpuFrequency = CpuFrequency()
        self.batteryService = BatteryService()

        # --- again UI ---
        self.ui.label_driver_name.setText(self.cpuFrequency.cpu[0].get_driver_name())
        self.ui.comboBox_scaling_governor.addItems(self.cpuFrequency.cpu[0].get_scaling_available_governors())
        self.ui.comboBox_scaling_governor.setCurrentText(self.cpuFrequency.cpu[0].get_scaling_governor())
        self.ui.comboBox_scaling_governor.currentTextChanged.connect(self.comboBox_scaling_governor_currentTextChanged)
        self.ui.comboBox_energy_performance_preference.addItems(self.cpuFrequency.cpu[0].get_energy_performance_available_preferences())
        self.ui.comboBox_energy_performance_preference.setCurrentText(self..cpuFrequency.cpu[0].get_energy_performance_preference())
        self.ui.comboBox_energy_performance_preference.currentTextChanged.connect(self.comboBox_energy_performance_preference_currentTextChanged)
        self.ui.spinBox_start_charging.setValue(self.batteryService.get_charge_control_thresholds()[0])
        self.ui.spinBox_stop_charging.setValue(self.batteryService.get_charge_control_thresholds()[1])
        self.ui.spinBox_start_charging.valueChanged.connect(self.spinBox_start_stop_charging_valueChanged)
        self.ui.spinBox_stop_charging.valueChanged.connect(self.spinBox_start_stop_charging_valueChanged)

        # --- Timers ---
        self.timer_update_tab_intelpstate = QTimer()
        self.timer_update_tab_intelpstate.timeout.connect(self.update_tab_intelpstate)
        self.timer_update_tab_intelpstate.start(2000)
        self.timer_update_tab_cpufrequency = QTimer()
        self.timer_update_tab_cpufrequency.timeout.connect(self.update_timer_update_tab_cpufrequency)
        self.timer_update_tab_cpufrequency.start(2000)

    def spinBox_start_stop_charging_valueChanged(self):
        self.batteryService.set_charge_control_thresholds(
            self.ui.spinBox_start_charging.value(),
            self.ui.spinBox_stop_charging.value()
        )

    def show(self):
        self.ui.show()

    def comboBox_scaling_governor_currentTextChanged(self, text):
        self.cpuFrequency.set_scaling_governor_for_all(text)

    def comboBox_energy_performance_preference_currentTextChanged(self, text):
        self.cpuFrequency.set_energy_performance_preference_for_all(text)

    def update_timer_update_tab_cpufrequency(self):
        self.ui.comboBox_scaling_governor.setCurrentText(self.cpuFrequency.cpu[0].get_scaling_governor())

    def update_tab_intelpstate(self):
        self.ui.checkBox_speedshift.setChecked(IntelPStateDriver.SpeedShift.get())
        self.ui.checkBox_turbo_pstates.setChecked(IntelPStateDriver.TurboPstates.get())
        self.ui.spinBox_intel_epb.setValue(IntelPStateDriver.get_energy_perf_bias_for_all_cpu()) # will emit valueChanged()

    def checkBox_speedshift_stateChanged(self, state):
        if not ((self.ui.checkBox_speedshift.checkState() == Qt.CheckState.Checked) != IntelPStateDriver.SpeedShift.get()):
            return
        if self.ui.checkBox_speedshift.checkState() == Qt.CheckState.Checked:
            IntelPStateDriver.SpeedShift.enable()
        else:
            IntelPStateDriver.SpeedShift.disable()

    def checkBox_turbo_pstates_stateChanged(self, state):
        if not ((self.ui.checkBox_turbo_pstates.checkState() == Qt.CheckState.Checked) != IntelPStateDriver.TurboPstates.get()):
            return
        if self.ui.checkBox_turbo_pstates.checkState() == Qt.CheckState.Checked:
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
