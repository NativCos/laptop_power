#!/usr/bin/env python3
import sys
import logging
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QTimer, Qt, QCoreApplication
from PySide6.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction

from widget_rapl import RAPLWidget
from service import IntelPStateDriver, CpuFrequency, BatteryService, GTSysFsDriver, DPTF

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
        layout = QVBoxLayout()
        layout.addWidget(rapl)
        self.ui.tab_rapl.setLayout(layout)

        self.ui.menu.triggered.connect(QCoreApplication.instance().quit)

        # --- Logic --
        self.cpuFrequency = CpuFrequency()
        self.batteryService = BatteryService()
        self.gtsysfsdriver = GTSysFsDriver()

        # --- again UI ---
        self.ui.label_driver_name.setText(self.cpuFrequency.cpu[0].get_driver_name())
        self.ui.comboBox_scaling_governor.addItems(self.cpuFrequency.cpu[0].get_scaling_available_governors())
        self.ui.comboBox_scaling_governor.setCurrentText(self.cpuFrequency.cpu[0].get_scaling_governor())
        self.ui.comboBox_scaling_governor.currentTextChanged.connect(self.comboBox_scaling_governor_currentTextChanged)
        self.ui.comboBox_energy_performance_preference.addItems(self.cpuFrequency.cpu[0].get_energy_performance_available_preferences())
        self.ui.comboBox_energy_performance_preference.addItems("1")
        self.ui.comboBox_energy_performance_preference.setCurrentText(self.cpuFrequency.cpu[0].get_energy_performance_preference())
        self.ui.comboBox_energy_performance_preference.currentTextChanged.connect(self.comboBox_energy_performance_preference_currentTextChanged)
        self.ui.spinBox_start_charging.setValue(self.batteryService.get_charge_control_thresholds()[0])
        self.ui.spinBox_stop_charging.setValue(self.batteryService.get_charge_control_thresholds()[1])
        self.ui.spinBox_start_charging.valueChanged.connect(self.spinBox_start_stop_charging_valueChanged)
        self.ui.spinBox_stop_charging.valueChanged.connect(self.spinBox_start_stop_charging_valueChanged)
        self.ui.checkBox_speedshift.stateChanged.connect(self.checkBox_speedshift_stateChanged)
        self.ui.checkBox_turbo_pstates.stateChanged.connect(self.checkBox_turbo_pstates_stateChanged)
        self.ui.spinBox_intel_epb.valueChanged.connect(self.spinBox_intel_epb_valueChanged)

        # add the system tray
        self.ui.tray = QSystemTrayIcon()
        self.ui.tray.setIcon(QIcon('icon.png'))
        self.ui.tray.setVisible(True)
        self.ui.tray.my_menu = QMenu()
        self.ui.tray.my_menu.my_action_set_power_performance = QAction('Set CPU Performance')
        self.ui.tray.my_menu.my_action_set_power_performance.triggered.connect(
            lambda: self.cpuFrequency.set_energy_performance_preference_for_all('balance_performance')
        )
        self.ui.tray.my_menu.addAction(self.ui.tray.my_menu.my_action_set_power_performance)
        self.ui.tray.my_menu.my_action_set_power_save = QAction('Set CPU PowerSave')
        self.ui.tray.my_menu.my_action_set_power_save.triggered.connect(
            lambda: self.cpuFrequency.set_energy_performance_preference_for_all('power')
        )
        self.ui.tray.my_menu.addAction(self.ui.tray.my_menu.my_action_set_power_save)
        self.ui.tray.my_menu.my_action_quit = QAction('Quit')
        self.ui.tray.my_menu.my_action_quit.triggered.connect(QCoreApplication.instance().quit)
        self.ui.tray.my_menu.addAction(self.ui.tray.my_menu.my_action_quit)
        self.ui.tray.setContextMenu(self.ui.tray.my_menu)
        self.ui.tray.activated.connect(self.ui.show)

        # --- Timers ---
        self.timer_update_tab_intelpstate = QTimer()
        self.timer_update_tab_intelpstate.timeout.connect(self.update_tab_intelpstate)
        self.timer_update_tab_intelpstate.start(2000)
        self.timer_update_tab_cpufrequency = QTimer()
        self.timer_update_tab_cpufrequency.timeout.connect(self.update_timer_update_tab_cpufrequency)
        self.timer_update_tab_cpufrequency.start(2000)
        self.timer_update_tab_temperature = QTimer()
        self.timer_update_tab_temperature.timeout.connect(self.update_timer_update_tab_temperature)
        self.timer_update_tab_temperature.start(800)

    def update_timer_update_tab_temperature(self):
        text = ""
        for t_p in self.gtsysfsdriver.thermal_points:
            text += t_p.label + '\t' + str(t_p.input) + '°C \n'
        text += 'temp offset \t -' + str(DPTF.get_tcc_offset()) + '°C \n'
        text += f'hardware max temp \t {str(self.gtsysfsdriver.thermal_points[0].critic_temperature)}°C \n'
        self.ui.textEdit_temperature.setText(text)

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
        self.ui.comboBox_energy_performance_preference.setCurrentText(self.cpuFrequency.cpu[0].get_energy_performance_preference())

    def update_tab_intelpstate(self):
        self.ui.checkBox_speedshift.setChecked(IntelPStateDriver.SpeedShift.get())
        self.ui.checkBox_turbo_pstates.setChecked(IntelPStateDriver.TurboPstates.get())
        self.ui.spinBox_intel_epb.valueChanged.disconnect(self.spinBox_intel_epb_valueChanged)
        self.ui.spinBox_intel_epb.setValue(IntelPStateDriver.get_energy_perf_bias_for_all_cpu()) # will emit valueChanged()
        self.ui.spinBox_intel_epb.valueChanged.connect(self.spinBox_intel_epb_valueChanged)

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
    app.setQuitOnLastWindowClosed(False)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
