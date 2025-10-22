from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QTabWidget,
)
import PyQt6.QtWidgets as QtWidgets

from serial_com import SerialReader


from views.motion3d import Motion3DView
from views.time_series_view import TimeSeriesView
from views.overview import OverView

# from views.motion3d import Motion3DView

import sys

from PyQt6.QtGui import QPalette, QColor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FogML Visualization")
        self.setGeometry(0, 0, 800, 480)

        # Apply dark theme to entire application
        self.load_styles()

        self.over_view = OverView()
        self.time_series_view = TimeSeriesView()
        self.motion_3d_view = Motion3DView()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.over_view, "Overall information")
        self.tabs.addTab(self.time_series_view, "Time Series")

        self.tabs.addTab(self.motion_3d_view, "3D Motion")

        self.setCentralWidget(self.tabs)

        # start the serial reader
        self.serial_reader = SerialReader("COM4")
        self.serial_reader.start()
        self.timer = self.startTimer(50)  # 50ms

    def load_styles(self):
        # load Dark theme stylesheet
        with open("./styles.qss", "r") as f:
            qss = f.read()
            self.setStyleSheet(qss)

        QApplication.instance().setStyle(
            "Fusion"
        )  # Use Fusion style for better dark theme compatibility

    def timerEvent(self, event):
        if self.serial_reader.has_data():
            latest = self.serial_reader.get_latest_acc()
            self.time_series_view.update_curves(latest)
            self.motion_3d_view.update_motion(latest)  # Add this line

        if self.serial_reader.sample_rate is not None:
            # format sample rate to 2 decimal places, force 2 decimal places

            rate_formatted = "{:.2f}".format(self.serial_reader.sample_rate)

            self.over_view.sample_rate_label.setText(
                f"Sample Rate = {rate_formatted} Hz"
            )

        # ...existing code...
        if self.serial_reader.lof_score is not None:
            self.over_view.update_lof_score(self.serial_reader.lof_score)

        if self.serial_reader.detected_class is not None:
            self.over_view.detected_class_label.setText(
                str(self.serial_reader.detected_class)
            )

            # Update icon based on class or LOF score
            is_anomaly = (
                self.serial_reader.lof_score > 2.5
                if self.serial_reader.lof_score
                else False
            )
            icon = (
                QtWidgets.QStyle.StandardPixmap.SP_DialogCancelButton
                if is_anomaly
                else QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton
            )
            self.over_view.class_icon.setPixmap(
                QtWidgets.QApplication.style().standardIcon(icon).pixmap(32, 32)
            )

        if self.serial_reader.feature_vector is not None:
            self.over_view.update_feature_vector(self.serial_reader.feature_vector)


# start the application
if __name__ == "__main__":

    app = QApplication(sys.argv)

    # Set application-wide dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

    app.setPalette(dark_palette)

    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
