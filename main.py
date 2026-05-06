import sys
import os
import numpy as np
from PIL import Image

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
import pyqtgraph as pg


class SyncViewer(QtWidgets.QWidget):
    def __init__(self, img1, img2):
        super().__init__()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.img1 = img1
        self.img2 = img2

        # ---------- Views ----------
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground("black")

        self.vb1 = self.glw.addViewBox(row=0, col=0)
        self.vb2 = self.glw.addViewBox(row=0, col=1)

        self.vb1.setDefaultPadding(0)
        self.vb2.setDefaultPadding(0)

        self.vb1.setAspectLocked(True)
        self.vb2.setAspectLocked(True)

        self.vb2.setXLink(self.vb1)
        self.vb2.setYLink(self.vb1)

        self.img_item1 = pg.ImageItem(self.img1, axisOrder="row-major")
        self.img_item2 = pg.ImageItem(self.img2, axisOrder="row-major")

        self.vb1.addItem(self.img_item1)
        self.vb2.addItem(self.img_item2)

        self.vb1.enableAutoRange()
        self.vb2.disableAutoRange()
        self.vb1.autoRange()

        # ---------- Crosshairs ----------
        pen = pg.mkPen("r", width=1)

        self.vLine1 = pg.InfiniteLine(angle=90, pen=pen)
        self.hLine1 = pg.InfiniteLine(angle=0, pen=pen)
        self.vLine2 = pg.InfiniteLine(angle=90, pen=pen)
        self.hLine2 = pg.InfiniteLine(angle=0, pen=pen)

        for item in (self.vLine1, self.hLine1):
            self.vb1.addItem(item, ignoreBounds=True)
        for item in (self.vLine2, self.hLine2):
            self.vb2.addItem(item, ignoreBounds=True)

        # ---------- Mouse tracking ----------
        self.glw.scene().sigMouseMoved.connect(self.mouse_moved)

        # ---------- Buttons ----------
        btn_flip1_h = QtWidgets.QPushButton("Flip L ↔")
        btn_flip1_v = QtWidgets.QPushButton("Flip L ↕")
        btn_flip2_h = QtWidgets.QPushButton("Flip R ↔")
        btn_flip2_v = QtWidgets.QPushButton("Flip R ↕")
        btn_rot = QtWidgets.QPushButton("Rotate 90°")

        btn_flip1_h.clicked.connect(lambda: self.flip(1, "h"))
        btn_flip1_v.clicked.connect(lambda: self.flip(1, "v"))
        btn_flip2_h.clicked.connect(lambda: self.flip(2, "h"))
        btn_flip2_v.clicked.connect(lambda: self.flip(2, "v"))
        btn_rot.clicked.connect(self.rotate)

        btn_row = QtWidgets.QHBoxLayout()
        for b in (btn_flip1_h, btn_flip1_v, btn_flip2_h, btn_flip2_v, btn_rot):
            btn_row.addWidget(b)

        # ---------- Layout ----------
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.glw)
        layout.addLayout(btn_row)
        self.setLayout(layout)

        self.setWindowTitle("GroundTruth - PCB Analysis")

    # ---------- Mouse & Keyboard ----------
    def mouse_moved(self, pos):
        # Determine which viewbox the mouse is in
        if self.vb1.sceneBoundingRect().contains(pos):
            source_vb = self.vb1
        elif self.vb2.sceneBoundingRect().contains(pos):
            source_vb = self.vb2
        else:
            return

        # Map from the active viewbox
        p = source_vb.mapSceneToView(pos)
        x, y = p.x(), p.y()

        # Apply to images
        self.vLine1.setPos(x)
        self.hLine1.setPos(y)
        self.vLine2.setPos(x)
        self.hLine2.setPos(y)

    def keyPressEvent(self, event):

        # Pan by a fraction of the visible Y span
        frac = 0.05

        # Get current view ranges
        (_, _), (y0, y1) = self.vb1.viewRange()
        step = (y1 - y0) * frac

        dx = dy = 0

        if event.key() in (Qt.Key.Key_A, Qt.Key.Key_Left):
            dx = -step
        elif event.key() in (Qt.Key.Key_D, Qt.Key.Key_Right):
            dx = step
        elif event.key() in (Qt.Key.Key_W, Qt.Key.Key_Up):
            dy = step
        elif event.key() in (Qt.Key.Key_S, Qt.Key.Key_Down):
            dy = -step
        elif event.key() == Qt.Key.Key_Escape:
            self.vb1.autoRange()
            return

        if dx or dy:
            self.vb1.translateBy(x=dx, y=dy)

    # ---------- Operations ----------
    def flip(self, which, axis):
        if which == 1:
            self.img1 = np.fliplr(self.img1) if axis == "h" else np.flipud(self.img1)
            self.img_item1.setImage(self.img1, autoLevels=False)
        else:
            self.img2 = np.fliplr(self.img2) if axis == "h" else np.flipud(self.img2)
            self.img_item2.setImage(self.img2, autoLevels=False)

        self.vb1.autoRange()

    def rotate(self):
        self.img1 = np.rot90(self.img1, -1)
        self.img2 = np.rot90(self.img2, -1)
        self.img_item1.setImage(self.img1, autoLevels=False)
        self.img_item2.setImage(self.img2, autoLevels=False)
        self.vb1.autoRange()


# ---------- Entry ----------
if __name__ == "__main__":
    if len(sys.argv) == 3:
        img1 = np.array(Image.open(sys.argv[1]))
        img2 = np.array(Image.open(sys.argv[2]))
    else:
        img1 = np.array(Image.open(os.path.expanduser(r'~/Downloads/front.jpg')))
        img2 = np.array(Image.open(os.path.expanduser(r'~/Downloads/back.jpg')))


    app = QtWidgets.QApplication(sys.argv)
    w = SyncViewer(img1, img2)
    w.show()
    sys.exit(app.exec())