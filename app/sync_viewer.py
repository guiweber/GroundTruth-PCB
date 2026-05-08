from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
import pyqtgraph as pg

from core.document import Document


class SyncViewer(QtWidgets.QWidget):
    def __init__(self, cli_arguments):
        super().__init__()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.doc = Document(cli_arguments)

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

        self.img_items = [pg.ImageItem(self.doc.images[0], axisOrder="row-major"),
                          pg.ImageItem(self.doc.images[1], axisOrder="row-major")]

        self.vb1.addItem(self.img_items[0])
        self.vb2.addItem(self.img_items[1])

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

        self.glw.scene().sigMouseMoved.connect(self.mouse_moved)

        # ---------- Layout ----------
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.glw)
        self.setLayout(layout)

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
        elif event.key() == Qt.Key.Key_Q:
            self.vb1.autoRange()
            return

        if dx or dy:
            self.vb1.translateBy(x=dx, y=dy)

    # ---------- Operations ----------
    def flip(self, which, axis):
        self.doc.flip(which, axis)
        self.img_items[which].setImage(self.doc.images[which], autoLevels=False)
        self.vb1.autoRange()

    def rotate(self):
        self.doc.rotate()
        self.img_items[0].setImage(self.doc.images[0], autoLevels=False)
        self.img_items[1].setImage(self.doc.images[1], autoLevels=False)
        self.vb1.autoRange()

    def save(self):
        self.doc.save_gtd()
