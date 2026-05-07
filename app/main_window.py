from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QToolBar,
)

from app.sync_viewer import SyncViewer


class MainWindow(QMainWindow):
    def __init__(self, cli_images):
        super().__init__()

        self.setWindowTitle("GroundTruth - PCB Analysis")

        self.viewer = SyncViewer(*cli_images)
        self.setCentralWidget(self.viewer)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.make_toolbar()

    def make_toolbar(self):
        tb = QToolBar("Adjustments")
        self.addToolBar(tb)

        tb.addAction("Flip L ↔", lambda: self.viewer.flip(0, "h"))
        tb.addAction("Flip L ↕", lambda: self.viewer.flip(0, "v"))

        tb.addSeparator()

        tb.addAction("Flip R ↔", lambda: self.viewer.flip(1, "h"))
        tb.addAction("Flip R ↕", lambda: self.viewer.flip(1, "v"))

        tb.addSeparator()

        tb.addAction("Rotate 90°", self.viewer.rotate)

    def keyPressEvent(self, event):
        self.viewer.handle_key_press(event)
