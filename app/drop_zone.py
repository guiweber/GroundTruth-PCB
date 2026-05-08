from PyQt6 import QtWidgets, QtGui, QtCore

LABEL_NO_IMG_TXT = "Drop two images\nor a .gtd document here"
LABEL_ONE_IMG_TXT = "One image loaded\nDrop another image to continue"

class DropZone(QtWidgets.QWidget):
    filesDropped = QtCore.pyqtSignal(list)
    clear_requested = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)

        # ------------ Drop Area --------------
        self.label = QtWidgets.QLabel(LABEL_NO_IMG_TXT)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 18px;
            }
        """)

        # ------------ Image Preview --------------
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

        self.clear_btn = QtWidgets.QPushButton("X", self.preview)
        self.clear_btn.setFixedSize(26, 26)
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #222;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 13px;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }
            QPushButton:hover {
                background: #333;
            }
        """)
        self.clear_btn.hide()

        # ------------ Layout --------------
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

        self.label.setText(LABEL_ONE_IMG_TXT)

        m = 6  # margin inside preview
        self.clear_btn.move(self.preview.width() - self.clear_btn.width() - m,m)

        self._has_image = True
        self.clear_btn.show()
        self.update()

    def clear_preview(self):
        self._has_image = False
        self.clear_btn.hide()
        self.label.setText(LABEL_NO_IMG_TXT)
        self.preview.clear()
        self.preview.hide()
        self.update()

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
