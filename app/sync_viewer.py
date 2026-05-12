from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
import pyqtgraph as pg

class SyncViewer(QtWidgets.QWidget):
    def __init__(self, document):
        super().__init__()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.doc = document

        # ---------- Views ----------
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground("black")

        self.vb1 = self.glw.addViewBox(row=0, col=0)
        self.vb2 = self.glw.addViewBox(row=0, col=1)

        self.vb1.setDefaultPadding(0)
        self.vb2.setDefaultPadding(0)

        self.vb1.setAspectLocked(True)
        self.vb2.setAspectLocked(True)

        # Disable the right click menu
        self.vb1.setMenuEnabled(False)
        self.vb2.setMenuEnabled(False)

        self.vb2.setXLink(self.vb1)
        self.vb2.setYLink(self.vb1)

        self.img_items = [pg.ImageItem(axisOrder="row-major"), pg.ImageItem(axisOrder="row-major")]

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
        """ Flip the image """
        self.doc.flip(which, axis)
        self.img_items[which].setImage(self.doc.images[which], autoLevels=False)
        self.vb1.autoRange()

    def get_state(self):
        """ Get the current view range/state of the first viewbox """
        return self.vb1.viewRange(), self.vb1.getState()

    def invert(self, which, axis):
        """ Invert the viewbox axis"""
        viewboxes = [self.vb1, self.vb2]
        if axis == "x":
            viewboxes[which].invertX(not viewboxes[which].xInverted())
            self.doc.config["axis_inverted"][which][axis] = viewboxes[which].xInverted()
        elif axis == "y":
            viewboxes[which].invertY(not viewboxes[which].yInverted())
            self.doc.config["axis_inverted"][which][axis] = viewboxes[which].yInverted()

    def rotate(self):
        """ Rotate the image """
        self.doc.rotate()
        self.update_images()

    def set_state(self, range, state):
        """ Set the viewboxes range/state """
        self.vb1.setRange(xRange=range[0], yRange=range[1], padding=0)
        self.vb1.setState(state)
        self.vb1.update()

    def update_images(self):
        """ Update the images in the UI from the document """
        self.img_items[0].setImage(self.doc.images[0], autoLevels=False)
        self.img_items[1].setImage(self.doc.images[1], autoLevels=False)
        self.vb1.autoRange()

    def update_axes(self):
        """ Update the axes from the document """
        self.vb1.invertX(self.doc.config["axis_inverted"][0]["x"])
        self.vb1.invertY(self.doc.config["axis_inverted"][0]["y"])
        self.vb2.invertX(self.doc.config["axis_inverted"][1]["x"])
        self.vb2.invertY(self.doc.config["axis_inverted"][1]["y"])
