from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QStackedWidget,
    QFileDialog,
    QWidget,
    QHBoxLayout,
    QSplitter,
)

from app.sync_viewer import SyncViewer
from app.drop_zone import DropZone, ImgPreview
from app.layer_panel import LayerPanel
from core.document import Document
from utils.errors import error_info


class MainWindow(QMainWindow):
    def __init__(self, cli_arguments):
        super().__init__()

        self.setWindowTitle("GroundTruth - PCB Analysis")

        self.doc = Document(cli_arguments)

        self.viewer = SyncViewer(self.doc)
        self.layer_panel = LayerPanel(self.doc, self.viewer)
        self.drop_zone = DropZone(self.doc)

        self.stack = QStackedWidget()

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.layer_panel)
        self.splitter.addWidget(self.viewer)
        self.splitter.setHandleWidth(5)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([220, 1800])

        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addWidget(self.splitter)
        self.content_widget.setLayout(self.content_layout)

        self.stack.addWidget(self.drop_zone)
        self.stack.addWidget(self.content_widget)
        self.setCentralWidget(self.stack)

        self.drop_zone.filesDropped.connect(self.on_files_dropped)
        self.drop_zone.imagesAccepted.connect(self.on_images_accepted)
        self.layer_panel.panelMinimized.connect(self.on_layer_panel_minimized)
        self.layer_panel.layerChanged.connect(lambda _: self.viewer.update_annotations())

        self.make_toolbar()
        self.update_ui_state()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def make_toolbar(self):
        self.toolbar = QToolBar("Adjustments")
        self.addToolBar(self.toolbar)

        self.toolbar.addAction("Save", lambda: self.save())

        self.toolbar.addSeparator()

        self.toolbar.addAction("Rotate 90°", self.viewer.rotate)

        self.toolbar.addSeparator()

        self.toolbar.addAction("Invert X L", lambda: self.viewer.invert(0, "x"))
        self.toolbar.addAction("Invert Y L", lambda: self.viewer.invert(0, "y"))

        self.toolbar.addSeparator()

        self.toolbar.addAction("Invert X R", lambda: self.viewer.invert(1, "x"))
        self.toolbar.addAction("Invert Y R", lambda: self.viewer.invert(1, "y"))

    def on_layer_panel_minimized(self, minimized):
            # Preserve the viewboxes range
            range, state = self.viewer.get_state()

            # Updates the splitter to match the panel's size
            sizes = self.splitter.sizes()
            sizes[0] = 0
            self.splitter.setSizes(sizes)

            # Restore the viewboxes range
            self.viewer.set_state(range, state)

    def on_files_dropped(self, paths):
        if len(self.drop_zone.previews) >= 2:
            return

        load_errors = self.doc.load_files(paths)

        if not self.doc.is_loaded():
            n_load =  len(self.doc.images)-len(self.drop_zone.previews)
            for i in range(n_load):
                self.drop_zone.set_preview_image()

            if len(self.drop_zone.previews) > 1:
                self.drop_zone.continue_btn.setVisible(True)
                self.drop_zone.previews[0].update_image(highlight_sides=True)
                self.drop_zone.previews[1].update_image(highlight_sides=True)

        self.update_ui_state()

        # Only display errors after UI update in case some files were successful
        if len(load_errors) > 3:
            load_errors = load_errors[:3]
        for e in load_errors:
            error_info("File loading error", e)

    def on_images_accepted(self):
        self.doc.loaded = True
        self.update_ui_state()

    def clear(self, index:int):
        self.doc.clear()
        self.drop_zone.clear_preview()
        self.update_ui_state()

    def save(self):
        if self.doc.saved_gtd:
            self.doc.save()
        else:
            self.save_as()

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save document", "", "GroundTruth Document (*.gtd)")
        if path:
            self.doc.save(path)

    def update_ui_state(self):
        if self.doc.is_loaded():
            self.viewer.update_images()
            self.viewer.update_axes()
            self.layer_panel.select_layer(0)
            self.stack.setCurrentWidget(self.content_widget)
            self.toolbar.setEnabled(True)
        else:
            self.stack.setCurrentWidget(self.drop_zone)
            self.toolbar.setEnabled(False)

    def keyReleaseEvent(self, event):
        if self.doc.is_loaded():

            # --------------- Annotation Two-Side Mode Deactivation
            if event.key() == Qt.Key.Key_Shift:
                self.viewer._update_rubberband(shift_pressed=False)

    def keyPressEvent(self, event):
        if self.doc.is_loaded():

        # --------------- CTRL + KEY COMBOS ---------------
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:

                # --------------- Undo
                if event.key() == Qt.Key.Key_Z:
                    self.viewer.undo()
                    return

                # --------------- Save
                if event.key() == Qt.Key.Key_S:
                    self.save()
                    return


        # --------------- SINGLE KEYS ---------------

            # --------------- Annotation Two-Side Mode Activation
            if event.key() == Qt.Key.Key_Shift and not event.isAutoRepeat():
                self.viewer._update_rubberband(shift_pressed=True)
                return

            # --------------- Annotation Mode & Tool Cycling
            if event.key() == Qt.Key.Key_R:
                self.viewer.select_mode = False
                if self.viewer.annotation_mode:
                    self.viewer.current_tool_index = (self.viewer.current_tool_index + 1) % len(self.viewer.annotation_tools)
                else:
                    self.viewer.annotation_mode = True
                    self.viewer.current_tool_index = 0
                self.viewer.pending_line = None
                self.viewer.clear_selection()
                return

            # --------------- Annotation Subtype Cycling
            if event.key() == Qt.Key.Key_C:
                if self.viewer.select_mode and self.viewer.selected_annotations:
                    self.viewer.push_undo_state()
                    self.viewer._cycle_selected_subtype()
                elif self.viewer.annotation_mode:
                    self.viewer.current_subtype_index = (self.viewer.current_subtype_index + 1) % len(
                        self.viewer.annotation_subtypes[self.viewer._current_tool()])
                return

            # --------------- Annotation Thickness
            if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.viewer.adjust_annotation_thickness(increase=True)
                return
            if event.key() == Qt.Key.Key_Minus:
                self.viewer.adjust_annotation_thickness(increase=False)
                return

            # --------------- Select Mode
            if event.key() == Qt.Key.Key_X:
                self.viewer.annotation_mode = False
                self.viewer.select_mode = not self.viewer.select_mode
                self.viewer.pending_line = None
                self.viewer.clear_selection()
                return

            # --------------- Clear Current Mode/Selection
            if event.key() == Qt.Key.Key_Escape:
                if self.viewer.annotation_mode:
                    if self.viewer.pending_line is not None:
                        self.viewer.pending_line = None
                        self.viewer._clear_rubberband()
                        self.viewer.current_series_id = self.viewer._new_series_id()
                        self.viewer.update_annotations()
                    else:
                        self.viewer.annotation_mode = False
                elif self.viewer.select_mode:
                    if self.viewer.selected_annotations:
                        self.viewer.clear_selection()
                    else:
                        self.viewer.select_mode = False
                return

            # --------------- Delete
            if event.key() == Qt.Key.Key_Delete:
                if self.viewer.select_mode and self.viewer.selected_annotations:
                    self.viewer.push_undo_state()
                    layer = self.viewer._get_layer()
                    removal_ids = {ann.uid for ann in self.viewer.selected_annotations}
                    for ann in list(layer.get_annotations()):
                        if ann.uid in removal_ids:
                            layer.remove_annotation(ann)
                    self.viewer.selected_annotations = []
                    self.viewer.update_annotations()
                return

            # --------------- Reset View Range
            if event.key() == Qt.Key.Key_Q:
                self.viewer.vb1.autoRange()
                return

            # --------------- Panning
            if event.key() in (Qt.Key.Key_A, Qt.Key.Key_Left):
                self.viewer.pan(dx=-1)
                return
            if event.key() in (Qt.Key.Key_D, Qt.Key.Key_Right):
                self.viewer.pan(dx=1)
                return
            if event.key() in (Qt.Key.Key_W, Qt.Key.Key_Up):
                self.viewer.pan(dy=1)
                return
            if event.key() in (Qt.Key.Key_S, Qt.Key.Key_Down):
                self.viewer.pan(dy=-1)
                return

            # --------------- Layer Selection
            if event.key() == Qt.Key.Key_0:
                self.layer_panel.select_layer(10)
                return
            if Qt.Key.Key_1 <= event.key() <= Qt.Key.Key_9:
                self.layer_panel.select_layer(event.key() - Qt.Key.Key_1)
                return
