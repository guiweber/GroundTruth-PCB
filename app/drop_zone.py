from PyQt6 import QtWidgets, QtGui, QtCore


class DropZone(QtWidgets.QWidget):
    filesDropped = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)

        self.label = QtWidgets.QLabel(
            "Drop two images\nor a .gtd document here"
        )
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 18px;
            }
        """)

        self.preview = QtWidgets.QLabel()
        self.preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedSize(512, 512)
        self.preview.setStyleSheet("""
            QLabel {
                border: 1px solid #444;
                background-color: #111;
            }
        """)
        self.preview.hide()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.preview, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self.setStyleSheet("""
            QWidget {
                border: 2px dashed #555;
                border-radius: 16px;
                background-color: #181818;
                padding: 28px;
            }
        """)

    def set_preview_image(self, image_array):
        h, w, _ = image_array.shape
        qimg = QtGui.QImage(image_array.data, w, h, 3 * w, QtGui.QImage.Format.Format_RGB888,)
        pix = QtGui.QPixmap.fromImage(qimg)
        pix = pix.scaled(
            self.preview.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.preview.setPixmap(pix)
        self.preview.show()

        self.label.setText(
            "One image loaded\nDrop another image to continue"
        )

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
