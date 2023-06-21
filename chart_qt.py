import sys
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

from service import IntelPowerCappingFramework
from utils import RingBuffer


class PlotViewer(QtWidgets.QWidget):

    doubleClickAction = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(PlotViewer, self).__init__(parent)

        self.figure = plt.figure(figsize=(5, 5))
        self.figureCanvas = FigureCanvas(self.figure)
        self.navigationToolbar = NavigationToolbar(self.figureCanvas, self)

        # create main layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.navigationToolbar)
        layout.addWidget(self.figureCanvas)
        self.setLayout(layout)

        self.intelrapl = IntelPowerCappingFramework()
        self.buffer = RingBuffer(30)
        self.buffer.fill_by_object(0)
        self.interval = 1

        self.refrash()
        self.timer = QTimer()
        self.timer.timeout.connect(self.refrash)
        self.timer.start(self.interval*1000)

    def refrash(self):
        # create an axis
        x = range(self.buffer.size)
        self.buffer.append(self.intelrapl.get_current_watts(self.interval) / float(10 ** 6))
        y = self.buffer.get_last(self.buffer.size)

        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        ax = self.figure.add_subplot(111)
        ax.plot(x, y, linewidth=2.0)
        #ax.set(xlim=(0, 8), xticks=np.arange(1, 8), ylim=(0, 8), yticks=np.arange(1, 8))


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    widget = PlotViewer()
    widget.show()
    app.exec()
