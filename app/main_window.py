from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QStackedWidget,
    QFileDialog,
)

from app.sync_viewer import SyncViewer
from app.drop_zone import DropZone
from core.document import Document
from utils.errors import error_info


class MainWindow(QMainWindow):
    def __init__(self, cli_arguments):
        super().__init__()

        self.setWindowTitle("GroundTruth - PCB Analysis")

        self.doc = Document(cli_arguments)

        self.viewer = SyncViewer(self.doc)
        self.drop_zone = DropZone()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.drop_zone)
        self.stack.addWidget(self.viewer)
        self.setCentralWidget(self.stack)

        self.drop_zone.filesDropped.connect(self.on_files_dropped)
        self.drop_zone.clear_requested.connect(self.on_clear_requested)

        self.make_toolbar()
        self.update_ui_state()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def make_toolbar(self):
        self.toolbar = QToolBar("Adjustments")
        self.addToolBar(self.toolbar)

        self.toolbar.addAction("Save", lambda: self.save())

        self.toolbar.addAction("Flip L ↔", lambda: self.viewer.flip(0, "h"))
        self.toolbar.addAction("Flip L ↕", lambda: self.viewer.flip(0, "v"))

        self.toolbar.addSeparator()

        self.toolbar.addAction("Flip R ↔", lambda: self.viewer.flip(1, "h"))
        self.toolbar.addAction("Flip R ↕", lambda: self.viewer.flip(1, "v"))

        self.toolbar.addSeparator()

        self.toolbar.addAction("Rotate 90°", self.viewer.rotate)

        self.toolbar.addSeparator()

        self.toolbar.addAction("Invert X L", lambda: self.viewer.invert(0, "x"))
        self.toolbar.addAction("Invert Y L", lambda: self.viewer.invert(0, "y"))

        self.toolbar.addSeparator()

        self.toolbar.addAction("Invert X R", lambda: self.viewer.invert(1, "x"))
        self.toolbar.addAction("Invert Y R", lambda: self.viewer.invert(1, "y"))

    def on_clear_requested(self):
        if len(self.doc.images) == 1:
            self.doc.clear()
            self.drop_zone.clear_preview()
            self.update_ui_state()

    def on_files_dropped(self, paths):
        load_errors = self.doc.load_files(paths)

        if len(self.doc.images) == 1:
            self.drop_zone.set_preview_image(self.doc.images[0])

        self.update_ui_state()

        # Only display errors after UI update in case some files were successful
        if len(load_errors) > 3:
            load_errors = load_errors[:3]
        for e in load_errors:
            error_info("File loading error", e)

    def save(self):
        if self.doc.saved_gtd:
            self.doc.save()
        else:
            self.save_as()

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save document", "", "GroundTruth Document (*.gtd)")

        if not path:
            return

        self.doc.save(path)

    def update_ui_state(self):
        if self.doc.is_loaded():
            self.viewer.update_images()
            self.viewer.update_axes()
            self.stack.setCurrentWidget(self.viewer)
            self.toolbar.setEnabled(True)
        else:
            self.stack.setCurrentWidget(self.drop_zone)
            self.toolbar.setEnabled(False)

    def keyPressEvent(self, event):
        """ Ensure events are processed if the window and not the viewer is in focus"""
        if self.doc.is_loaded():
            self.viewer.keyPressEvent(event)
