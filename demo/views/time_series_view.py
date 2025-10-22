from collections import deque

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)


class TimeSeriesView(QWidget):

    def __init__(self):
        super().__init__()
        self.plot_widget = pg.PlotWidget(background="#252525")
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen(color="#999999"))
        self.plot_widget.getAxis("left").setPen(pg.mkPen(color="#999999"))
        self.plot_widget.getAxis("bottom").setTextPen(pg.mkPen(color="#cccccc"))
        self.plot_widget.getAxis("left").setTextPen(pg.mkPen(color="#cccccc"))
        # plot use deque

        self.x_curve = self.plot_widget.plot(pen="r", name="X轴")
        self.y_curve = self.plot_widget.plot(pen="g", name="Y轴")
        self.z_curve = self.plot_widget.plot(pen="b", name="Z轴")
        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
        self.x_deque = deque(maxlen=100)
        self.y_deque = deque(maxlen=100)
        self.z_deque = deque(maxlen=100)
        self.plot_widget.setXRange(0, 100)
        self.plot_widget.setYRange(-1.5, 1.5)

    def update_curves(self, latest_data):
        x, y, z = latest_data
        # append the new data to the deque
        self.x_deque.append(x)
        self.y_deque.append(y)
        self.z_deque.append(z)

        self.x_curve.setData(self.x_deque)
        self.y_curve.setData(self.y_deque)
        self.z_curve.setData(self.z_deque)

        return
