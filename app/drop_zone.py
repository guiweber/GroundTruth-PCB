from PyQt6 import QtWidgets, QtGui, QtCore
import numpy as np

LABELS = ["Drop two images\nor a .gtd document here",
          "One image loaded\nDrop another image to continue",
          "⚠️ Ensure the RED and BLUE sides correspond to the same physical side of the PCB ⚠️",]

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
            preview.update_image(highlight_sides=False)

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
        self.image_label = QtWidgets.QLabel()
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

    def update_image(self, highlight_sides=False):
        image_array = self.doc.images[self.preview_index]
        h, w, _ = image_array.shape
        img_data = bytearray(np.flipud(image_array).tobytes())
        if highlight_sides:
            self.highlight_sides(img_data, w, h)
        qimg = QtGui.QImage(img_data, w, h, 3 * w, QtGui.QImage.Format.Format_RGB888,)
        pix = QtGui.QPixmap.fromImage(qimg)
        pix = pix.scaled(
            self.image_label.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(pix)

    def highlight_sides(self, img_data, w, h):

        thickness = max(1, int(0.02 * min(w, h)))
        stride = 3 * w
        for y in range(h):
            for x in range(thickness):
                i = y * stride + x * 3
                img_data[i + 0] = 50  # R
                img_data[i + 1] = 50  # G
                img_data[i + 2] = 255  # B

        for y in range(thickness):
            row_start = y * stride
            for x in range(w):
                i = row_start + x * 3
                img_data[i + 0] = 255  # R
                img_data[i + 1] = 0
                img_data[i + 2] = 0

    def resizeEvent(self, event):
        super().resizeEvent(event)

        m = 6
        self.clear_btn.move(
            self.width() - self.clear_btn.width() - m,
            m
        )

    def flip(self, axis):
        self.doc.flip(self.preview_index, axis)
        highlight = True if len(self.doc.images) > 1 else False
        self.update_image(highlight_sides=highlight)
