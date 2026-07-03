from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QEvent, QPointF
from PyQt6.QtGui import QPen, QColor
import pyqtgraph as pg

from core.annotations import Annotation, LineAnnotation, TextAnnotation, TYPE_LINE, TYPE_ARROW_F, TYPE_TEXT

import copy
import math
import uuid

# Tools
TOOL_LINE = "Line"
TOOL_TEXT = "Text"

class SyncViewer(QtWidgets.QWidget):
    def __init__(self, document):
        super().__init__()

        self.init_variables()
        self.doc = document

        # ----  Annotation Tools ----
        self.annotation_tools = [TOOL_LINE, TOOL_TEXT]
        self.annotation_subtypes = {TOOL_LINE: [TYPE_LINE, TYPE_ARROW_F], TOOL_TEXT: [TYPE_TEXT]}

        # ---------- Views ----------
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground("black")

        self.vb1 = self.glw.addViewBox(row=0, col=0)
        self.vb2 = self.glw.addViewBox(row=0, col=1)

        self.glw.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.vb1.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.vb2.setFocusPolicy(Qt.FocusPolicy.NoFocus)

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
        self.glw.scene().installEventFilter(self)

        # ---------- Layout ----------
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.glw)
        self.setLayout(layout)

    def init_variables(self):
        # This should contain all the variables that may need to be reinitialized when the document is cleared
        self.current_tool_index = 0
        self.current_subtype_index = 0
        self.annotation_thickness = 16
        self.annotation_font_size = 16
        self.annotation_mode = False
        self.select_mode = False
        self.pending_line = None
        self.current_series_id = self.new_series_id()
        self.selected_annotations = []
        self.drag_action = None
        self.drag_anchor = None
        self.annotation_graphics = {}
        self.preview_items = []
        self.preview_previous_pos = None
        self.undo_stack = []

    def current_tool(self):
        return self.annotation_tools[self.current_tool_index]

    def current_subtype(self):
        subtypes = self.annotation_subtypes.get(self.current_tool(), [])
        if not subtypes:
            return ""
        return subtypes[self.current_subtype_index]

    def _distance(self, a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _distance_to_segment(self, point, start, end):
        px, py = point
        x1, y1 = start
        x2, y2 = end
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return self._distance(point, start)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        closest = (x1 + t * dx, y1 + t * dy)
        return self._distance(point, closest)

    def new_series_id(self):
        return str(uuid.uuid4())

    def _edit_selected_text_annotation(self, annotation: Annotation | None = None):
        if annotation is None:
            annotation = next((ann for ann in self.selected_annotations if isinstance(ann, TextAnnotation)),None)
            if not annotation:
                return False

        if not isinstance(annotation, TextAnnotation):
            return False

        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Edit text annotation",
            "Text:",
            text=annotation.text,
        )
        if ok:
            self.push_undo_state()
            annotation.text = text
            self.update_annotations(self.doc.current_layer_index)
            return True
        return False

    def _create_text_annotation(self, sides: list[int], position: tuple[float, float]):
        annotation = TextAnnotation(
            position=position,
            text=TOOL_TEXT,
            sides=sides,
            thickness=self.annotation_font_size,
            subtype=self.current_subtype() or TOOL_TEXT,
            series_id=self.new_series_id(),
        )

        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "New text annotation",
            "Text:",
            text=annotation.text,
        )
        if not ok or not text:
            return None

        self.push_undo_state()
        annotation.text = text
        self.doc.get_current_layer().add_annotation(annotation)
        self.update_annotations(self.doc.current_layer_index)
        return annotation

    def _viewbox_at(self, pos: QPointF):
        if self.vb1.sceneBoundingRect().contains(pos):
            return 0
        if self.vb2.sceneBoundingRect().contains(pos):
            return 1
        return None

    def _scene_to_view(self, pos: QPointF, view_index: int):
        viewbox = self.vb1 if view_index == 0 else self.vb2
        point = viewbox.mapSceneToView(pos)
        return (point.x(), point.y())

    def clear_graphics(self, layer_index=None):
        # Removes the annotations of one or all layers from view
        items = []
        if layer_index is None:
            for side_map in self.annotation_graphics.values():
                items.append(side_map)
            self.annotation_graphics.clear()
        else:
            for ann in self.doc.layers[layer_index].get_annotations():
                # Pop safely in case the annotations were already invisible
                side_map = self.annotation_graphics.pop(ann.uid, None)
                if side_map is not None:
                    items.append(side_map)

        for side_map in items:
            for side, items in side_map.items():
                target_vb = self.vb1 if side == 0 else self.vb2
                for item in items:
                    try:
                        target_vb.removeItem(item)
                        continue
                    except Exception:
                        pass
                    try:
                        self.glw.scene().removeItem(item)
                    except Exception:
                        pass

    def clear_preview(self):
        for item, side in self.preview_items:
            target_vb = self.vb1 if side == 0 else self.vb2
            try:
                target_vb.removeItem(item)
            except Exception:
                pass
        self.preview_items = []

    def _scene_to_world(self, pos: QPointF):
        view_index = self._viewbox_at(pos)
        return self._scene_to_view(pos, view_index)

    def _draw_annotation(self, annotation: Annotation, side: int, color: str, alpha: float = 1.0, selected: bool = False):
        qcolor = QColor(color)
        qcolor.setAlphaF(alpha)

        if selected:
            # Use inverted color for selected annotations (solid)
            qcolor = QColor(255 - qcolor.red(), 255 - qcolor.green(), 255 - qcolor.blue(), qcolor.alpha())

        target_vb = self.vb1 if side == 0 else self.vb2
        items = annotation.draw(side, qcolor, target_vb)

        if items:
            for item in items:
                target_vb.addItem(item)

        self.annotation_graphics.setdefault(annotation.uid, {})[side] = items

    def push_undo_state(self):
        self.undo_stack.append(copy.deepcopy(self.doc.layers))
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return
        self.doc.layers = self.undo_stack.pop()
        self.clear_selection()
        self.pending_line = None
        self.update_annotations()

    def update_annotations(self, layer_index=None):
        if layer_index is None or layer_index == -1:
            self.clear_graphics()
            layers_to_draw = [l for l in self.doc.layers if l is not self.doc.get_current_layer()] + [self.doc.get_current_layer()]
        else:
            self.clear_graphics(layer_index)
            layers_to_draw = [self.doc.layers[layer_index]]

        for layer in layers_to_draw:
            if not layer.visible:
                continue
            for annotation in layer.get_annotations():
                for side in getattr(annotation, "sides", []):
                    self._draw_annotation(annotation, side, layer.color, layer.alpha, selected=annotation.selected)

        self.update_preview()

    def update_preview(self, cursor_scene_pos: QPointF | None = None, shift_pressed=None):
        self.clear_preview()
        vbs = [self.vb1, self.vb2]

        if shift_pressed is None:
            shift_pressed = bool(QtWidgets.QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)

        # Make sure we have a position to work with
        if cursor_scene_pos is not None:
            self.preview_previous_pos = cursor_scene_pos
        else:
            if self.preview_previous_pos is not None:
                cursor_scene_pos = self.preview_previous_pos
            else:
                return
        current_pos = self._scene_to_world(cursor_scene_pos)

        # Use the current layer color and apply its alpha
        layer = self.doc.get_current_layer()
        qcolor = QColor(layer.color)
        qcolor.setAlphaF(layer.alpha)

        if self.current_tool() == TOOL_TEXT:
            text = TextAnnotation(position=current_pos, text="Text", sides=[0,1], thickness=self.annotation_font_size)
            self.preview_items.append((text.draw(0, qcolor, self.vb1)[0], 0))
            self.preview_items.append((text.draw(1, qcolor, self.vb2)[0], 1))

        elif self.current_tool() == TOOL_LINE and self.pending_line is not None:
            sides = [0, 1] if shift_pressed else [self.pending_line["start_side"]]
            line = self._get_pending_line_annotation(current_pos, sides)

            if line is not None:
                for side in sides:
                    self.preview_items.extend([(i, side) for i in line.draw(side, qcolor)])

        for item, side in self.preview_items:
            vbs[side].addItem(item)

    def _find_annotation_hit(self, view_index: int, position: tuple[float, float]):
        layer = self.doc.get_current_layer()
        best = None
        best_distance = 1e6
        best_hit = None
        threshold = 30
        for annotation in layer.get_annotations():
            if view_index not in getattr(annotation, "sides", []):
                continue
            if isinstance(annotation, TextAnnotation):
                hit_distance = self._distance(position, annotation.position)
                if hit_distance < threshold and hit_distance < best_distance:
                    best = annotation
                    best_distance = hit_distance
                    best_hit = "move"
                continue

            start, end = annotation.start, annotation.end
            start_dist = self._distance(position, start)
            end_dist = self._distance(position, end)
            if start_dist < threshold and start_dist < best_distance:
                best = annotation
                best_distance = start_dist
                best_hit = "start"
            if end_dist < threshold and end_dist < best_distance:
                best = annotation
                best_distance = end_dist
                best_hit = "end"
            segment_dist = self._distance_to_segment(position, start, end)
            if segment_dist < threshold/2 and segment_dist < best_distance:
                best = annotation
                best_distance = segment_dist
                best_hit = "move"
        return best, best_hit

    def _select_annotation(self, annotation: Annotation):
        if not annotation:
            return
        layer = self.doc.get_current_layer()
        group_id = annotation.series_id
        self.selected_annotations = [ann for ann in layer.get_annotations() if getattr(ann, "series_id", None) == group_id]
        for ann in layer.get_annotations():
            ann.selected = ann in self.selected_annotations
        self.update_annotations(self.doc.current_layer_index)

    def clear_selection(self):
        for ann in self.selected_annotations:
            ann.selected = False
        self.selected_annotations = []
        self.update_annotations()

    def cycle_selected_subtype(self):
        if not self.selected_annotations:
            return
        available = self.annotation_subtypes.get(TOOL_LINE, [])
        for annotation in self.selected_annotations:
            annotation.cycle_subtype(available)
        self.update_annotations(self.doc.current_layer_index)

    def _apply_drag_to_selected(self, dx: float, dy: float, endpoint: str | None = None):
        if not self.selected_annotations:
            return
        if endpoint is None:
            for ann in self.selected_annotations:
                ann.move_by(dx, dy)
            return
        if endpoint == "start":
            anchor_point = self.drag_action["annotation"].start
        else:
            anchor_point = self.drag_action["annotation"].end
        for ann in self.selected_annotations:
            if self._distance(ann.start, anchor_point) < 1e-6:
                ann.move_endpoint(0, dx, dy)
            if self._distance(ann.end, anchor_point) < 1e-6:
                ann.move_endpoint(1, dx, dy)

    def _create_line_segment(self, end_point: tuple[float, float], current_sides: list[int], next_side: int, end_button: Qt.MouseButton):
        line = self._get_pending_line_annotation(end_point, current_sides)
        if line is not None:
            self.push_undo_state()
            self.doc.get_current_layer().add_annotation(line)
            self.update_annotations(self.doc.current_layer_index)

            # next pending segment should remember which button originated it
            self.pending_line = {
                "start": end_point,
                "start_side": next_side,
                "view_index": end_button,
                "start_button": end_button,
            }
            self.update_preview()

    def _get_pending_line_annotation(self, end: tuple[float, float], sides: list[int]):
        #Return a LineAnnotation based on the pending line
        if self.pending_line is None:
            return None

        # determine per-side styles. If both sides are present and the pending_line
        # recorded an origin side (the mouse button used when starting), make that
        # origin side solid and the opposite dashed. Single-side annotations are solid.
        # The style is determined by the button used to finish the segment
        side_styles = {}
        if set(sides) == {0, 1}:
            # if the finishing mouse button was left, make left view solid
            if self.pending_line["start_button"] == Qt.MouseButton.LeftButton:
                side_styles = {0: "solid", 1: "dashed"}
            else:
                side_styles = {0: "dashed", 1: "solid"}
        else:
            for s in sides:
                side_styles[s] = "solid"

        return LineAnnotation(
            start=self.pending_line["start"],
            end=end,
            sides=sides,
            thickness=self.annotation_thickness,
            subtype=self.current_subtype(),
            series_id=self.current_series_id,
            side_styles=side_styles,
        )

    def _cancel_line_entry(self, keep_tool: bool = True):
        self.pending_line = None
        if not keep_tool:
            self.annotation_mode = False
        self.current_series_id = self.new_series_id()
        self.clear_preview()
        self.update_annotations()

    def eventFilter(self, obj, event):
        if obj != self.glw.scene():
            return False

        if event.type() == QEvent.Type.GraphicsSceneMouseDoubleClick:
            if self.annotation_mode and self.current_tool() == TOOL_LINE:
                self._cancel_line_entry(keep_tool=True)
                return True
            if self.select_mode:
                view_index = self._viewbox_at(event.scenePos())
                if view_index is not None:
                    view_point = self._scene_to_view(event.scenePos(), view_index)
                    annotation, _ = self._find_annotation_hit(view_index, view_point)
                    if isinstance(annotation, TextAnnotation):
                        self._edit_selected_text_annotation(annotation)
                        return True
            return False

        if event.type() == QEvent.Type.GraphicsSceneMousePress:
            return self._handle_scene_mouse_press(event)

        if event.type() == QEvent.Type.GraphicsSceneMouseMove:
            return self._handle_scene_mouse_move(event)

        if event.type() == QEvent.Type.GraphicsSceneMouseRelease:
            return self._handle_scene_mouse_release(event)

        return False

    def _handle_scene_mouse_press(self, event):
        view_index = self._viewbox_at(event.scenePos())
        if view_index is None:
            return False

        button = event.button()
        if button not in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            return False

        next_side = 0 if button == Qt.MouseButton.LeftButton else 1
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        view_point = self._scene_to_view(event.scenePos(), view_index)

        # Sides for non chained annotations
        sides = [0, 1] if shift else [next_side]

        if self.select_mode:
            annotation, hit_type = self._find_annotation_hit(next_side, view_point)
            if annotation:
                self.push_undo_state()
                self._select_annotation(annotation)
                self.drag_action = {
                    "type": "resize" if hit_type in ("start", "end") else "move",
                    "annotation": annotation,
                    "handle": hit_type,
                }
                self.drag_anchor = view_point
                return True
            else:
                self.clear_selection()
                return False

        if self.annotation_mode and self.current_tool() == TOOL_TEXT:
            self._create_text_annotation(sides, view_point)
            return True

        if self.annotation_mode and self.current_tool() == TOOL_LINE:
            if self.pending_line is None:
                self.pending_line = {
                    "start": view_point,
                    "start_side": next_side,
                    "view_index": view_index,
                    "start_button": event.button(),
                }
                self.update_preview(event.scenePos(), shift)
            else:
                current_sides = [0, 1] if shift else [self.pending_line["start_side"]]
                self._create_line_segment(view_point, current_sides, next_side, event.button())
                self.update_preview(event.scenePos(), shift)
            return True

        return False

    def _handle_scene_mouse_move(self, event):
        if self.drag_action is not None and self.drag_anchor is not None:
            view_index = self._viewbox_at(event.scenePos())
            if view_index is None:
                return False
            current = self._scene_to_view(event.scenePos(), view_index)
            dx = current[0] - self.drag_anchor[0]
            dy = current[1] - self.drag_anchor[1]
            if abs(dx) < 1e-8 and abs(dy) < 1e-8:
                return False
            if self.drag_action["type"] == "move":
                self._apply_drag_to_selected(dx, dy)
            else:
                self._apply_drag_to_selected(dx, dy, endpoint=self.drag_action["handle"])
            self.drag_anchor = current
            self.update_annotations(self.doc.current_layer_index)
            return True

        if self.annotation_mode:
            self.update_preview(event.scenePos())
            return False

        return False

    def _handle_scene_mouse_release(self, event):
        if self.drag_action is not None:
            self.drag_action = None
            self.drag_anchor = None
            return True
        return False

    def mouse_moved(self, pos):
        if self.vb1.sceneBoundingRect().contains(pos):
            source_vb = self.vb1
        elif self.vb2.sceneBoundingRect().contains(pos):
            source_vb = self.vb2
        else:
            return

        p = source_vb.mapSceneToView(pos)
        x, y = p.x(), p.y()

        self.vLine1.setPos(x)
        self.hLine1.setPos(y)
        self.vLine2.setPos(x)
        self.hLine2.setPos(y)

    def get_state(self):
        return self.vb1.viewRange(), self.vb1.getState()

    def invert(self, which, axis):
        viewboxes = [self.vb1, self.vb2]
        if axis == "x":
            viewboxes[which].invertX(not viewboxes[which].xInverted())
            self.doc.config["axis_inverted"][which][axis] = viewboxes[which].xInverted()
        elif axis == "y":
            viewboxes[which].invertY(not viewboxes[which].yInverted())
            self.doc.config["axis_inverted"][which][axis] = viewboxes[which].yInverted()

        self.update_annotations()  # Only needed for text annotations, could optimize if needed

    def pan(self, dx=0, dy=0, frac = 0.05):
        (_, _), (y0, y1) = self.vb1.viewRange()
        step = (y1 - y0) * frac
        self.vb1.translateBy(x=dx*step, y=dy*step)

    def rotate(self):
        self.doc.rotate()
        self.update_images()

    def set_state(self, range, state):
        self.vb1.setRange(xRange=range[0], yRange=range[1], padding=0)
        self.vb1.setState(state)
        self.vb1.update()

    def update_images(self):
        self.img_items[0].setImage(self.doc.images[0], autoLevels=False)
        self.img_items[1].setImage(self.doc.images[1], autoLevels=False)
        self.vb1.autoRange()
        self.update_annotations()

    def update_axes(self):
        self.vb1.invertX(self.doc.config["axis_inverted"][0]["x"])
        self.vb1.invertY(self.doc.config["axis_inverted"][0]["y"])
        self.vb2.invertX(self.doc.config["axis_inverted"][1]["x"])
        self.vb2.invertY(self.doc.config["axis_inverted"][1]["y"])
        
    def adjust_annotation_thickness(self, increase:bool):
        # Changes the thickness/font size of the annotations tools or of the selected annotation.
        if self.select_mode and self.selected_annotations:
            self.push_undo_state()
            for annotation in self.selected_annotations:
                annotation.thickness = self._compute_annotation_thickness(annotation.thickness, increase)
            self.update_annotations(self.doc.current_layer_index)
        elif self.annotation_mode:
            if self.current_tool() == TOOL_TEXT:
                self.annotation_font_size = self._compute_annotation_thickness(self.annotation_font_size, increase)
            else:
                self.annotation_thickness = self._compute_annotation_thickness(self.annotation_thickness, increase)
            self.update_preview()

    def _compute_annotation_thickness(self, base_thickness, increase:bool):
        # Computes the change in annotation thickness in pixels based on the current thickness
        change_ratio = 1.1
        if increase:
            return max(base_thickness + 1, int(base_thickness * change_ratio))
        else:
            return max(1, min(base_thickness - 1, int(base_thickness / change_ratio)))
