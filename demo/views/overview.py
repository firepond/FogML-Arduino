import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from PyQt6.QtWidgets import (
    QWidget,
)
import math
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem
import PyQt6.QtGui as QtGui
import PyQt6.QtWidgets as QtWidgets


class OverView(QWidget):
    def __init__(self):
        super().__init__()

        # Apply a stylesheet to the whole widget
        self.setStyleSheet(
            """
            QWidget {background-color: #2D2D30; color: #E0E0E0;}
            QLabel {font-size: 14px; padding: 5px;}
            QGroupBox {font-size: 16px; font-weight: bold; border: 2px solid #3E3E42; border-radius: 8px; margin-top: 15px; padding-top: 10px;}
            QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 5px;}
        """
        )

        # Create layout
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        # === Status Panel ===
        status_group = QtWidgets.QGroupBox("System Status")
        status_layout = QtWidgets.QHBoxLayout()
        status_group.setLayout(status_layout)

        # LOF Score with circular gauge
        self.lof_gauge = self.create_gauge("LOF Score", 0, 10, 2.5)

        # Sample rate with progress bar
        rate_widget = QWidget()
        rate_layout = QtWidgets.QVBoxLayout()
        rate_widget.setLayout(rate_layout)
        self.sample_rate_label = QtWidgets.QLabel("Sample Rate")
        rate_layout.addWidget(
            self.sample_rate_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        # close button in the top right corner
        close_button = QtWidgets.QPushButton("X")
        close_button.setStyleSheet(
            "background-color: #FF0000; color: white; border-radius: 5px;"
        )
        close_button.setFixedSize(30, 30)
        # close the whole application
        close_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        close_button.setToolTip("Close Application")
        close_button.setToolTipDuration(2000)
        # close the application when clicked
        close_button.clicked.connect(QtWidgets.QApplication.instance().quit)
        rate_layout.addWidget(
            close_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        rate_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        rate_layout.setSpacing(0)

        status_layout.addWidget(self.lof_gauge)
        status_layout.addWidget(rate_widget)

        # === Classification Panel ===
        class_group = QtWidgets.QGroupBox("Motion Detection")
        class_layout = QtWidgets.QVBoxLayout()
        class_group.setLayout(class_layout)

        # Class detection with icon
        class_row = QtWidgets.QHBoxLayout()
        self.class_icon = QtWidgets.QLabel()
        self.class_icon.setPixmap(
            QtWidgets.QApplication.style()
            .standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton)
            .pixmap(32, 32)
        )
        self.detected_class_label = QtWidgets.QLabel("Normal Motion")
        self.detected_class_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        class_row.addWidget(self.class_icon)
        class_row.addWidget(self.detected_class_label)
        class_row.addStretch()

        class_layout.addLayout(class_row)

        # Feature vector display as numbers
        self.feature_frame = QtWidgets.QFrame()
        self.feature_frame.setFrameStyle(
            QtWidgets.QFrame.Shape.StyledPanel | QtWidgets.QFrame.Shadow.Raised
        )
        self.feature_frame.setStyleSheet(
            "background-color: #242426; border-radius: 5px; padding: 10px;"
        )

        feature_frame_layout = QtWidgets.QVBoxLayout()
        self.feature_frame.setLayout(feature_frame_layout)

        # Title
        feature_title = QtWidgets.QLabel("Feature Vector")
        feature_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        feature_frame_layout.addWidget(feature_title)

        # Grid layout for feature values
        self.features_grid = QtWidgets.QGridLayout()
        self.feature_labels = []
        self.feature_values = []

        # Create labels for each feature
        cols = 4  # Display in a 3x4 grid
        for i in range(12):
            row = i // cols
            col = i % cols

            # Feature label
            label = QtWidgets.QLabel(f"F{i+1}:")
            label.setStyleSheet("color: #aaaaaa;")
            self.features_grid.addWidget(label, row, col * 2)
            self.feature_labels.append(label)

            # Feature value
            value = QtWidgets.QLabel("0.000")
            value.setStyleSheet(
                "font-family: monospace; font-weight: bold; color: cyan;"
            )
            self.features_grid.addWidget(value, row, col * 2 + 1)
            self.feature_values.append(value)

        feature_frame_layout.addLayout(self.features_grid)
        class_layout.addWidget(self.feature_frame)

        # Add panels to main layout
        main_layout.addWidget(status_group)
        main_layout.addWidget(class_group)

    def create_gauge(self, label, min_val, max_val, threshold):
        # Create a circular gauge widget using pyqtgraph
        gauge_widget = QWidget()
        gauge_layout = QtWidgets.QVBoxLayout()
        gauge_widget.setLayout(gauge_layout)

        # Create circular progress bar - increase size by setting minimum height
        self.gauge_view = pg.GraphicsLayoutWidget()
        self.gauge_view.setMinimumHeight(200)  # Make gauge bigger
        self.gauge_view.setMinimumWidth(200)  # Make gauge bigger
        self.gauge = pg.PlotItem()
        self.gauge_view.addItem(self.gauge)
        self.gauge.setAspectLocked(True)

        # Create colored background arcs - make them bigger
        bg_green = QGraphicsEllipseItem(-4.5, -4.5, 9.0, 9.0)
        bg_green.setStartAngle(225 * 16)
        bg_green.setSpanAngle(180 * 16)
        bg_green.setPen(pg.mkPen(200, 0, 0, 150, width=12))  # Wider pen
        bg_green.setBrush(pg.mkBrush(None))
        self.gauge.addItem(bg_green)

        bg_red = QGraphicsEllipseItem(-4.5, -4.5, 9.0, 9.0)
        bg_red.setStartAngle(45 * 16)
        bg_red.setSpanAngle(180 * 16)
        bg_red.setPen(pg.mkPen(0, 200, 0, 150, width=12))  # Wider pen
        bg_red.setBrush(pg.mkBrush(None))
        self.gauge.addItem(bg_red)

        # Create needle - make it wider and longer
        self.needle = QGraphicsLineItem(0, 0, 9, 0)  # Longer needle
        self.needle.setPen(pg.mkPen(255, 255, 255, 200, width=3))  # Wider needle
        self.gauge.addItem(self.needle)

        # Create value text - make it bigger
        self.lof_text = pg.TextItem(text="0.0", anchor=(0.5, 0.65))
        self.lof_text.setFont(
            QtGui.QFont("Arial", 24, QtGui.QFont.Weight.Bold)
        )  # Larger font
        self.gauge.addItem(self.lof_text)

        # Add title
        title = QtWidgets.QLabel(label)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")  # Bigger title

        # Hide axes
        self.gauge.hideAxis("left")
        self.gauge.hideAxis("bottom")

        gauge_layout.addWidget(self.gauge_view)
        gauge_layout.addWidget(title)

        return gauge_widget

    def update_lof_score(self, score):
        if score is None:
            return
        score_val = float(score)
        if score_val > 5:
            score_angel = 5
        else:
            score_angel = score_val

        angle = (score_angel / 5) * 270
        # counter clockwise from 270 degrees to 0
        angle = 270 - angle

        # Update needle position with angle
        rad = angle * 3.14159 / 180
        length = 9
        self.needle.setLine(0, 0, length * math.cos(rad), length * math.sin(rad))

        # Update text
        self.lof_text.setText(f"{score_val:.2f}")

        # Set color based on threshold
        color = "green" if score_val < 2.5 else "red"
        self.lof_text.setColor(color)

    def update_feature_vector(self, vector):
        if vector is None:
            return

        # Parse the feature vector string and update text labels
        try:
            # Extract just the first 12 features
            # values = [float(x) for x in vector.strip("[]").split(",")[:12]]
            values = vector

            # Update each feature value label
            for i, val in enumerate(values):
                if i < len(self.feature_values):
                    # Format with fixed precision to keep alignment
                    self.feature_values[i].setText(f"{val:.3f}")

                    # Color-code by magnitude (bright for larger values)
                    magnitude = abs(val)
                    if magnitude > 0.5:
                        self.feature_values[i].setStyleSheet(
                            "font-family: monospace; font-weight: bold; color: #00ffff;"
                        )
                    elif magnitude > 0.2:
                        self.feature_values[i].setStyleSheet(
                            "font-family: monospace; font-weight: bold; color: #00cccc;"
                        )
                    else:
                        self.feature_values[i].setStyleSheet(
                            "font-family: monospace; font-weight: bold; color: #009999;"
                        )
        except Exception as e:
            print(f"Error updating feature vector: {e}")
