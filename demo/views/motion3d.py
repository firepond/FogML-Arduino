from PyQt6 import QtCore, QtWidgets

from PyQt6.QtWidgets import QVBoxLayout, QWidget
import numpy as np

from pyqtgraph.Qt import QtCore
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)
import PyQt6.QtWidgets as QtWidgets


import pyqtgraph.opengl as gl


class Motion3DView(QWidget):
    def __init__(self):
        super().__init__()

        # Create 3D view widget
        self.view = gl.GLViewWidget()
        self.view.setCameraPosition(distance=24)

        # Create grid for reference
        grid = gl.GLGridItem()
        grid.setSize(x=10, y=10, z=10)
        grid.setSpacing(x=1, y=1, z=1)
        self.view.addItem(grid)

        # Create 3D scatter plot for motion path
        self.motion_path = gl.GLScatterPlotItem(
            size=8, color=(1, 1, 1, 1), pxMode=False  # Increased point size
        )
        self.view.addItem(self.motion_path)

        # Add line plot for continuous path visualization
        self.motion_line = gl.GLLinePlotItem(width=2, color=(0, 1, 1, 1))
        self.view.addItem(self.motion_line)

        # Create arrow for current acceleration
        self.acc_arrow = gl.GLLinePlotItem(width=3, color=(1, 0, 0, 1))
        self.view.addItem(self.acc_arrow)

        # Store position and acceleration history
        self.positions = np.zeros((100, 3))  # Store last 100 positions
        self.position_idx = 0
        self.current_position = np.array([0.0, 0.0, 0.0])

        # Gravity compensation
        self.gravity_calibrated = False
        self.gravity_offset = np.array([0.0, 0.0, 0.0])
        self.calibration_samples = []
        self.calibration_count = 0

        # Amplification control
        self.amplification_factor = 3.0  # Default amplification

        # Add reset button and amplification slider
        self.reset_button = QtWidgets.QPushButton("Reset & Calibrate")
        self.reset_button.clicked.connect(self.reset_motion)

        self.amp_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.amp_slider.setMinimum(1)
        self.amp_slider.setMaximum(10)
        self.amp_slider.setValue(3)  # Default value
        self.amp_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.amp_slider.setTickInterval(1)
        self.amp_slider.valueChanged.connect(self.update_amplification)

        self.amp_label = QtWidgets.QLabel(
            f"Amplification: {self.amplification_factor}x"
        )

        # Layout
        layout = QVBoxLayout()
        # Add 3D view to layout, and set the layout for the widget
        # 80% space for 3D view, 20% for controls
        layout.addWidget(self.view, stretch=8)
        # layout.addWidget(self.view)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.amp_label)
        layout.addWidget(self.amp_slider)
        self.setLayout(layout)

    def update_amplification(self):
        self.amplification_factor = self.amp_slider.value()
        self.amp_label.setText(f"Amplification: {self.amplification_factor}x")

    def reset_motion(self):
        # Reset position tracking
        self.positions = np.zeros((100, 3))
        self.position_idx = 0
        self.current_position = np.array([0.0, 0.0, 0.0])
        self.motion_path.setData(pos=self.positions)
        self.motion_line.setData(pos=np.array([[0, 0, 0], [0, 0, 0]]))
        self.acc_arrow.setData(pos=np.array([[0, 0, 0], [0, 0, 0]]))

        # Reset gravity calibration
        self.gravity_calibrated = False
        self.calibration_samples = []
        self.calibration_count = 0
        self.gravity_offset = np.array([0.0, 0.0, 0.0])

    def update_motion(self, acc_data):
        x, y, z = acc_data
        current_acc = np.array([x, y, z])

        # Gravity calibration
        if not self.gravity_calibrated:
            # Collect initial samples to determine gravity offset
            self.calibration_samples.append(current_acc)
            self.calibration_count += 1

            if self.calibration_count >= 10:
                # Average the first 10 samples to estimate gravity
                self.gravity_offset = np.mean(self.calibration_samples, axis=0)
                self.gravity_calibrated = True
                print(f"Gravity calibrated: {self.gravity_offset}")
            return

        # Subtract gravity offset from acceleration
        adjusted_acc = current_acc - self.gravity_offset

        # Apply a smaller decay factor to make motion more persistent
        decay_factor = 0.95
        self.current_position *= decay_factor

        # Amplified integration to make small movements more visible
        scale_factor = 0.15 * self.amplification_factor  # Increased and adjustable
        delta_pos = adjusted_acc * scale_factor
        self.current_position += delta_pos

        # Update position history
        self.positions[self.position_idx] = self.current_position
        self.position_idx = (self.position_idx + 1) % 100

        # Update visualization
        self.motion_path.setData(pos=self.positions)

        # Update line visualization for continuous path
        self.motion_line.setData(pos=self.positions)

        # Update acceleration arrow to show adjusted acceleration (also amplified)
        arrow_start = self.current_position
        arrow_end = self.current_position + adjusted_acc * (
            0.5 * self.amplification_factor
        )
        self.acc_arrow.setData(pos=np.array([arrow_start, arrow_end]))
