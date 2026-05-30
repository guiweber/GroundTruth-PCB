from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtGui import QPainter, QColor, QLinearGradient
from PyQt6.QtCore import (
    pyqtProperty,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QEasingCurve,
    QRect,
    QPointF
)

import numpy as np

LABELS = ["Drop two images\nor a .gtd document here",
          "One image loaded\nDrop another image to continue",
          "⚠️ Ensure the <span style='color: orange;'>ORANGE</span> and <span style='color:#87CEFA;'>BLUE</span> "
          "sides correspond to the same physical side of the PCB ⚠️",]

class DropZone(QtWidgets.QWidget):
    filesDropped = QtCore.pyqtSignal(list)
    imagesAccepted = QtCore.pyqtSignal()

    def __init__(self, doc):
        super().__init__()

        self.doc = doc
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QPushButton {
                font-size: 17px;
                padding: 10px;
                background-color: #282828;
                color: #bbb;
                border: 2px solid #555;
                border-radius: 10px;
            }

            QPushButton:hover {
                background-color: #383838;
            }
        """)

        # ------------ Drop Area --------------
        self.label = QtWidgets.QLabel(LABELS[0])
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 18px;
                border: 2px dashed #555;
                border-radius: 16px;
                background-color: #181818;
                padding: 28px;
            }
        """)

        # ------------ Continue button --------------
        self.continue_btn = QtWidgets.QPushButton("The sides are aligned, Continue")
        self.continue_btn.clicked.connect(lambda: self.imagesAccepted.emit())
        self.continue_btn.setVisible(False)

        # ------------ Image Preview Layout --------------
        self.previews: list[ImgPreview] = []
        self.preview_layout = QtWidgets.QHBoxLayout()
        self.preview_layout.addStretch()
        self.preview_layout.addStretch()


        # ------------ Drop Zone Layout --------------
        layout = QtWidgets.QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addLayout(self.preview_layout)
        layout.addStretch()

    def set_preview_image(self):
        index = len(self.previews)
        preview = ImgPreview(index, self.doc.images[index], self.doc)
        preview.clear_requested.connect(self.clear_preview)
        self.previews.append(preview)
        layout_index = self.preview_layout.count() - 1  # before last stretch
        self.preview_layout.insertWidget(layout_index, preview)
        self.label.setText(LABELS[len(self.previews)])

        if len(self.previews) > 1:
            self.continue_btn.setVisible(True)
            self.enable_glow()

        self.update()

    def clear_preview(self, index: int):
        self.doc.images.pop(index)
        self.continue_btn.setVisible(False)
        preview_widget = self.previews[index]
        self.preview_layout.removeWidget(preview_widget)
        preview_widget.deleteLater()
        self.previews.pop(index)
        self.label.setText(LABELS[len(self.previews)])
        self.update()
        for i, preview in enumerate(self.previews):
            preview.preview_index = i
            preview.enable_glow(False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if paths:
            self.filesDropped.emit(paths)

    def enable_glow(self):
        for p in self.previews:
            p.enable_glow(True)


class ImgPreview(QtWidgets.QFrame):
    clear_requested = QtCore.pyqtSignal(int)

    def __init__(self, preview_index: int, image_array, doc):
        super().__init__()
        self.preview_index = preview_index
        self.doc = doc

        # -------- Main Layout
        self.setObjectName("imgPreviewFrame")
        self.setStyleSheet("""
            QFrame#imgPreviewFrame {
                border: 1px solid #444;
                border-radius: 16px;
                background-color: #181818;
                padding: 28px;
            }
        """)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # -------- Button row
        btn_row = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(6, 6, 6, 6)

        self.flip_x_btn = QtWidgets.QPushButton("Flip X axis")
        self.flip_y_btn = QtWidgets.QPushButton("Flip Y axis")
        self.flip_x_btn.clicked.connect(lambda: self.flip("h"))
        self.flip_y_btn.clicked.connect(lambda: self.flip("v"))

        btn_layout.addStretch()
        btn_layout.addWidget(self.flip_x_btn)
        btn_layout.addWidget(self.flip_y_btn)
        btn_layout.addStretch()

        self.layout.addWidget(btn_row)

        # -------- Image
        self.image_label = GlowLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(512, 512)

        self.layout.addWidget(self.image_label)

        # -------- Clear button
        self.clear_btn = QtWidgets.QPushButton("X", self)
        self.clear_btn.setFixedSize(26, 26)
        self.clear_btn.clicked.connect(lambda: self.clear_requested.emit(self.preview_index))
        self.clear_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 13px;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }
        """)
        m = 6  # margin inside preview
        self.clear_btn.move(self.width() - self.clear_btn.width() - m, m)
        self.update_image()

    def update_image(self):
        image_array = self.doc.images[self.preview_index]
        h, w, _ = image_array.shape
        img_data = np.flipud(image_array).tobytes()
        qimg = QtGui.QImage(img_data, w, h, 3 * w, QtGui.QImage.Format.Format_RGB888,)
        pix = QtGui.QPixmap.fromImage(qimg)
        pix = pix.scaled(
            self.image_label.content_size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(pix)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        m = 6
        self.clear_btn.move(
            self.width() - self.clear_btn.width() - m,
            m
        )

    def flip(self, axis):
        self.doc.flip(self.preview_index, axis)
        self.update_image()

    def enable_glow(self, enable=True):
        self.image_label.glow_enabled = enable


class GlowLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._glow_size = 16 # Size of the glow in pixels
        self._glow = 0.3 # Pulse strength animation variable
        self.glow_enabled = False

        # Breathing pulse effect
        self._grow = QPropertyAnimation(self, b"glow")
        self._grow.setStartValue(0.2)
        self._grow.setEndValue(1.0)
        self._grow.setDuration(900)
        self._grow.setEasingCurve(QEasingCurve.Type.InOutSine)

        self._shrink = QPropertyAnimation(self, b"glow")
        self._shrink.setStartValue(1.0)
        self._shrink.setEndValue(0.2)
        self._shrink.setDuration(900)
        self._shrink.setEasingCurve(QEasingCurve.Type.InOutSine)

        self._pulse = QSequentialAnimationGroup(self)
        self._pulse.addAnimation(self._grow)
        self._pulse.addAnimation(self._shrink)
        self._pulse.setLoopCount(-1)
        self._pulse.start()

    def get_glow(self):
        return self._glow

    def set_glow(self, value):
        self._glow = value
        self.update()

    glow = pyqtProperty(float, get_glow, set_glow)

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.glow_enabled:
            return

        pm = self.pixmap()
        if pm is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.contentsRect()
        x = rect.x() + (rect.width() - pm.width()) // 2
        y = rect.y() + (rect.height() - pm.height()) // 2

        alpha = int(40 + 180 * self._glow)

        # Left blue glow
        left_rect = QRect(x - self._glow_size, y, self._glow_size, pm.height())

        blue = QLinearGradient(QPointF(left_rect.topLeft()), QPointF(left_rect.topRight()))
        blue.setColorAt(0.0, QColor(80, 170, 255, 0)) # Near pixmap
        blue.setColorAt(1.0, QColor(80, 170, 255, alpha))

        painter.fillRect(left_rect, blue)

        # Top orange glow
        top_rect = QRect(x, y - self._glow_size, pm.width(), self._glow_size)

        orange = QLinearGradient(QPointF(top_rect.topLeft()), QPointF(top_rect.bottomLeft()))
        orange.setColorAt(0.0, QColor(255, 140, 60, 0)) # Near pixmap
        orange.setColorAt(1.0, QColor(255, 140, 60, alpha))

        painter.fillRect(top_rect, orange)

    def content_size(self):
        # Returns the size images should be scaled to for accommodating the glow effect
        # We need to reserve twice the glow size since the image is centered
        return self.size() - QtCore.QSize(int(self._glow_size * 2), int(self._glow_size * 2),)
