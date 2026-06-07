from uuid import uuid4

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QSlider,
    QColorDialog,
    QMessageBox,
    QFrame,
    QStackedLayout,
    QSizePolicy,
)

from utils.errors import error_info


class LayerItemWidget(QWidget):
    eyeClicked = pyqtSignal(str)

    def __init__(self, uid: str, index: int, layer: dict):
        super().__init__()
        self.uid = uid
        self.index = index
        self.layer = layer

        layout = QHBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        self.number_label = QLabel(str(index + 1))
        self.number_label.setFixedWidth(18)
        layout.addWidget(self.number_label)

        self.eye_button = QPushButton("👁")
        self.eye_button.setFixedSize(24, 24)
        self.eye_button.setCheckable(True)
        self.eye_button.clicked.connect(self.on_eye_clicked)
        layout.addWidget(self.eye_button)

        self.color_dot = QFrame()
        self.color_dot.setFixedSize(14, 14)
        self.color_dot.setStyleSheet("background-color: #fff; border-radius: 7px; border: 1px solid #222;")
        layout.addWidget(self.color_dot)

        self.name_label = QLabel(layer.name)
        self.name_label.setMinimumWidth(60)
        layout.addWidget(self.name_label)

        self.setLayout(layout)
        self.update_widget(index, layer)

    def update_widget(self, index: int, layer: dict, selected: bool = False):
        self.index = index
        self.layer = layer
        self.number_label.setText(str(index + 1))
        self.name_label.setText(layer.name)
        self.eye_button.setChecked(layer.visible)
        self.eye_button.setText("👁" if layer.visible else "🚫")

        color = QtGui.QColor(layer.color)
        self.color_dot.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #222; border-radius: 7px;"
        )
        self.setStyleSheet(
            "border: 1px solid #4a4a4a; border-radius: 3px;"
            if selected else "border: none;"
        )

    def on_eye_clicked(self):
        self.eyeClicked.emit(self.uid)


class LayerListWidget(QListWidget):
    orderChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setAcceptDrops(True)
        self.setSpacing(2)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.orderChanged.emit()


class LayerPanel(QWidget):
    layerChanged = pyqtSignal(int)
    panelMinimized = pyqtSignal(bool)

    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.doc = document
        self.selected_index = max(0, min(self.doc.current_layer_index, len(self.doc.layers) - 1))
        self.minimized = False
        self.expanded_min_width = 220
        self.collapsed_width = 50

        self.setMinimumWidth(self.expanded_min_width)

        self._build_ui()
        self.refresh_layers()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)

        self.minimize_button = QPushButton("⇤")
        self.minimize_button.setFixedSize(28, 28)
        self.minimize_button.clicked.connect(self.toggle_minimized)
        header_layout.addWidget(self.minimize_button)

        self.add_button = QPushButton("+ Layer")
        self.add_button.clicked.connect(self.add_layer)
        header_layout.addWidget(self.add_button)

        self.toggle_all_button = QPushButton("Toggle all")
        self.toggle_all_button.setFixedSize(90, 28)
        self.toggle_all_button.clicked.connect(self.toggle_all_layers)
        header_layout.addWidget(self.toggle_all_button)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.stack = QStackedLayout()

        self.expanded_widget = QWidget()
        expanded_layout = QVBoxLayout()
        expanded_layout.setContentsMargins(0, 0, 0, 0)
        expanded_layout.setSpacing(6)

        self.layer_list = LayerListWidget()
        self.layer_list.currentRowChanged.connect(self.select_layer)
        self.layer_list.orderChanged.connect(self.reorder_layers)
        expanded_layout.addWidget(self.layer_list)

        self.properties_panel = QWidget()
        properties_layout = QVBoxLayout()
        properties_layout.setContentsMargins(2, 2, 2, 2)
        properties_layout.setSpacing(8)

        self.rename_edit = QLineEdit()
        self.rename_edit.setPlaceholderText("Layer name")
        self.rename_edit.editingFinished.connect(self.rename_layer)
        properties_layout.addWidget(QLabel("Rename"))
        properties_layout.addWidget(self.rename_edit)

        self.color_button = QPushButton("Pick color")
        self.color_button.clicked.connect(self.open_color_picker)
        properties_layout.addWidget(self.color_button)

        self.hex_edit = QLineEdit()
        self.hex_edit.setPlaceholderText("HEX color")
        self.hex_edit.editingFinished.connect(self.change_color_hex)
        properties_layout.addWidget(self.hex_edit)

        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(25, 100)
        self.alpha_slider.valueChanged.connect(self.change_alpha)
        properties_layout.addWidget(QLabel("Opacity"))
        properties_layout.addWidget(self.alpha_slider)

        self.delete_button = QPushButton("Delete layer")
        self.delete_button.clicked.connect(self.delete_layer)
        properties_layout.addWidget(self.delete_button)

        self.properties_panel.setLayout(properties_layout)
        expanded_layout.addWidget(self.properties_panel)

        self.expanded_widget.setLayout(expanded_layout)
        self.stack.addWidget(self.expanded_widget)

        self.collapsed_widget = QWidget()
        collapsed_layout = QVBoxLayout()
        collapsed_layout.setContentsMargins(0, 0, 0, 0)
        collapsed_layout.setSpacing(4)
        collapsed_layout.addStretch()
        self.collapsed_buttons_container = QWidget()
        self.collapsed_buttons_layout = QVBoxLayout()
        self.collapsed_buttons_layout.setContentsMargins(2, 2, 2, 2)
        self.collapsed_buttons_layout.setSpacing(4)
        self.collapsed_buttons_container.setLayout(self.collapsed_buttons_layout)
        collapsed_layout.addWidget(self.collapsed_buttons_container)
        collapsed_layout.addStretch()
        self.collapsed_widget.setLayout(collapsed_layout)
        self.stack.addWidget(self.collapsed_widget)

        layout.addLayout(self.stack)
        self.setLayout(layout)
        self.stack.setCurrentWidget(self.expanded_widget)

    def toggle_minimized(self):
        self.minimized = not self.minimized
        self.stack.setCurrentWidget(self.collapsed_widget if self.minimized else self.expanded_widget)
        self.minimize_button.setText("⇥" if self.minimized else "⇤")
        if self.minimized:
            self.setMinimumWidth(self.collapsed_width)
            self.setMaximumWidth(self.collapsed_width)
            self.toggle_all_button.setVisible(False)
            self.add_button.setVisible(False)
            self.panelMinimized.emit(True)

        else:
            self.setMinimumWidth(self.expanded_min_width)
            self.setMaximumWidth(16777215)
            self.toggle_all_button.setVisible(True)
            self.add_button.setVisible(True)
            self.refresh_layers()
            self.panelMinimized.emit(False)

    def refresh_layers(self):
        self.layer_list.clear()
        while self.collapsed_buttons_layout.count():
            item = self.collapsed_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, layer in enumerate(self.doc.layers):
            item = QListWidgetItem()
            widget = LayerItemWidget(layer.uid, index, layer)
            widget.eyeClicked.connect(self.toggle_visibility)
            item.setSizeHint(widget.sizeHint())
            self.layer_list.addItem(item)
            self.layer_list.setItemWidget(item, widget)

            button = QPushButton(str(index + 1))
            button.setFixedSize(28, 28)
            button.setCheckable(True)
            button.setChecked(index == self.selected_index)
            color = QtGui.QColor(layer.color)
            button.setStyleSheet(
                f"background-color: {color.name()}; color: white; border: {'2px solid white' if index == self.selected_index else '1px solid #444'};"
            )
            button.clicked.connect(lambda checked, i=index: self.select_layer(i))
            self.collapsed_buttons_layout.addWidget(button)

        if self.selected_index < self.layer_list.count():
            self.layer_list.setCurrentRow(self.selected_index)
        self.update_property_panel()

    def select_layer(self, index: int):
        """ Select layer by index, used by collapsed buttons """
        # This event fires twice per list click, once with -1. Ignore the -1.
        # Out of bound values can also be received via 0-9 keypresses, so filter them out.
        if index < 0 or index == self.selected_index or index >= len(self.doc.layers):
            return
        self.selected_index = index
        self.doc.current_layer_index = index
        self.doc.layers[index].visible = True
        self.layerChanged.emit(index)
        if not self.minimized:
            self.layer_list.setCurrentRow(index)
        self.refresh_layers()

    def toggle_visibility(self, uid: str):
        layer_index = self._find_layer_index(uid)
        if layer_index is None:
            return
        self.doc.layers[layer_index].visible = not self.doc.layers[layer_index].visible
        if self.layer_list.currentRow() < 0:
            self.selected_index = layer_index
            self.doc.current_layer_index = layer_index
        self.refresh_layers()
        self.layerChanged.emit(layer_index)

    def toggle_all_layers(self):
        if not self.doc.layers:
            return
        any_hidden = any(not layer.visible for layer in self.doc.layers)
        new_state = True if any_hidden else False
        for layer in self.doc.layers:
            layer.visible = new_state
        self.refresh_layers()
        self.layerChanged.emit(-1)

    def rename_layer(self):
        if self.selected_index < 0:
            return
        text = self.rename_edit.text().strip()
        if not text:
            return
        self.doc.layers[self.selected_index].name = text
        self.refresh_layers()
        self.layerChanged.emit(self.selected_index)

    def open_color_picker(self):
        if self.selected_index < 0 or self.selected_index >= len(self.doc.layers):
            return
        current = QtGui.QColor(self.doc.layers[self.selected_index].color)
        dialog = QColorDialog(current, self)
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        dialog.setWindowTitle("Pick layer color")
        origin = self.color_button.mapToGlobal(self.color_button.rect().bottomLeft())
        dialog.move(origin)
        if dialog.exec() == QColorDialog.DialogCode.Accepted:
            color = dialog.selectedColor().name()
            self._set_color(color)

    def change_color_hex(self):
        hex_color = self.hex_edit.text().strip()
        if not hex_color.startswith("#"):
            hex_color = f"#{hex_color}"
        color = QtGui.QColor(hex_color)
        if not color.isValid():
            return
        self._set_color(color.name())

    def _set_color(self, color: str):
        self.doc.layers[self.selected_index].color = color
        self.refresh_layers()
        self.layerChanged.emit(self.selected_index)

    def change_alpha(self, value: int):
        if self.selected_index < 0:
            return
        alpha = max(0.0, min(1.0, value / 100.0))
        self.doc.layers[self.selected_index].alpha = alpha
        self.layerChanged.emit(self.selected_index)

    def delete_layer(self):
        # Delete the selected layer, but ensure at least one layer exists
        if len(self.doc.layers) <= 1:
            return
        if not self.doc.layers[self.selected_index].is_empty():
            confirm = QMessageBox.question(
                self,
                "Delete layer",
                "Layer contains annotations. Delete anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm == QMessageBox.StandardButton.No:
                return

        self.doc.layers.pop(self.selected_index)
        self.selected_index = min(self.selected_index, len(self.doc.layers) - 1)
        self.doc.current_layer_index = self.selected_index
        self.refresh_layers()
        if len(self.doc.layers) <= 1:
            self.delete_button.setEnabled(False)
        self.layerChanged.emit(-1)

    def add_layer(self):

        index = len(self.doc.layers)
        self.doc.add_layer()

        self.selected_index = index
        self.doc.current_layer_index = index
        self.refresh_layers()
        self.layerChanged.emit(index)
        self.delete_button.setEnabled(True)

    def reorder_layers(self):
        if self.layer_list.count() == 0:
            return
        order = []
        for row in range(self.layer_list.count()):
            widget = self.layer_list.itemWidget(self.layer_list.item(row))
            if widget is not None:
                order.append(widget.uid)

        layer_map = {layer.uid: layer for layer in self.doc.layers}
        self.doc.layers = [layer_map[uid] for uid in order if uid in layer_map]
        self.selected_index = max(0, min(self.selected_index, len(self.doc.layers) - 1))
        self.doc.current_layer_index = self.selected_index
        self.refresh_layers()
        self.layerChanged.emit(-1)

    def update_property_panel(self):
        if self.selected_index < 0 or self.selected_index >= len(self.doc.layers):
            self.rename_edit.setText("")
            self.hex_edit.setText("")
            self.alpha_slider.setValue(100)
            return
        layer = self.doc.layers[self.selected_index]
        self.rename_edit.setText(layer.name)
        self.hex_edit.setText(layer.color)
        self.alpha_slider.setValue(int(layer.alpha * 100))

    def _find_layer_index(self, uid: str):
        for index, layer in enumerate(self.doc.layers):
            if layer.uid == uid:
                return index
        return None
