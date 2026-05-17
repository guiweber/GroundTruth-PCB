import math
import uuid
from typing import List, Optional, Tuple

from PyQt6 import QtWidgets
from PyQt6.QtGui import QPen, QPolygonF, QColor
from PyQt6.QtCore import Qt, QPointF
import pyqtgraph as pg

class Annotation:

    def __init__(self, annotation_type: str, subtype: str, thickness: int, series_id: Optional[str] = None):
        self.uid = str(uuid.uuid4())
        self.annotation_type = annotation_type
        self.subtype = subtype
        self.thickness = thickness
        self.series_id = series_id or str(uuid.uuid4())
        self.selected = False

    def cycle_subtype(self, available_subtypes: List[str]):
        if self.subtype not in available_subtypes:
            self.subtype = available_subtypes[0]
            return
        index = available_subtypes.index(self.subtype)
        index = (index + 1) % len(available_subtypes)
        self.subtype = available_subtypes[index]

    def draw(self, side: int, qcolor: QColor):
        raise NotImplementedError

    def move_by(self, dx: float, dy: float):
        raise NotImplementedError

    def move_endpoint(self, endpoint_index: int, dx: float, dy: float):
        raise NotImplementedError


class LineAnnotation(Annotation):

    def __init__(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        sides: List[int],
        thickness: int,
        subtype: str = "line",
        series_id: Optional[str] = None,
        side_styles: Optional[dict] = None,
    ):
        super().__init__("line", subtype, thickness, series_id)
        self.start = start
        self.end = end
        self.sides = sides
        # side_styles maps side index (0 or 1) to 'solid' or 'dashed'
        if side_styles is None:
            # default: solid on all specified sides
            self.side_styles = {s: "solid" for s in self.sides}
        else:
            # ensure keys present for sides
            self.side_styles = {s: side_styles.get(s, "solid") for s in self.sides}

    def draw(self, side, qcolor):

        # Determine whether this side should be dashed (selection no longer uses dashes)
        side_style = getattr(self, "side_styles", {}).get(side, "solid")
        is_dashed = (side_style == "dashed")

        qp = QPen(qcolor)
        qp.setWidth(max(self.thickness, 1))
        if is_dashed:
            qp.setStyle(Qt.PenStyle.CustomDashLine)
            qp.setDashPattern([10.0, 6.0])
        else:
            qp.setStyle(Qt.PenStyle.SolidLine)

        start, end = self.start, self.end
        items = [pg.PlotDataItem([start[0], end[0]], [start[1], end[1]], pen=qp)]

        # Arrows
        if self.subtype != "line":
            # place arrowhead in the middle of the segment and orient along the segment
            mid_x = (start[0] + end[0]) / 2.0
            mid_y = (start[1] + end[1]) / 2.0

            # desired head length in pixels relative to thickness
            head_len_pixels = int(self.thickness * 6)
            width_pixels = int(head_len_pixels * 0.8)

            # direction unit vector
            vx = end[0] - start[0]
            vy = end[1] - start[1]
            norm = math.hypot(vx, vy)
            if norm == 0:
                dirx, diry = 1.0, 0.0
            else:
                dirx, diry = vx / norm, vy / norm
            perpx, perpy = -diry, dirx

            half_len = head_len_pixels / 2.0
            half_w = width_pixels / 2.0

            tip = (mid_x + dirx * half_len, mid_y + diry * half_len)
            base_center = (mid_x - dirx * half_len, mid_y - diry * half_len)
            base1 = (base_center[0] + perpx * half_w, base_center[1] + perpy * half_w)
            base2 = (base_center[0] - perpx * half_w, base_center[1] - perpy * half_w)

            # Convert data (view) coords to scene coords for polygon vertices
            # Create polygon in view/data coordinates so it scales with the viewbox transform
            poly = QPolygonF()
            poly.append(QPointF(tip[0], tip[1]))
            poly.append(QPointF(base1[0], base1[1]))
            poly.append(QPointF(base2[0], base2[1]))
            gitem = QtWidgets.QGraphicsPolygonItem(poly)
            gitem.setBrush(qcolor)
            pen_for_arrow = QPen(qcolor)
            pen_for_arrow.setWidth(0)
            gitem.setPen(pen_for_arrow)
            items.append(gitem)

        return items

    def move_by(self, dx: float, dy: float):
        self.start = (self.start[0] + dx, self.start[1] + dy)
        self.end = (self.end[0] + dx, self.end[1] + dy)

    def move_endpoint(self, endpoint_index: int, dx: float, dy: float):
        if endpoint_index == 0:
            self.start = (self.start[0] + dx, self.start[1] + dy)
        else:
            self.end = (self.end[0] + dx, self.end[1] + dy)

    def points(self):
        return self.start, self.end
