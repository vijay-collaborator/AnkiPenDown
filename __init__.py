# -*- coding: utf-8 -*-
# Copyright: Vijay <http://t.me/Viiijay1>
# Copyright: Rytis Petronis (Rytisgit)
# Copyright: Michal Krassowski
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
AnkiPenDown - A feature-rich drawing addon for Anki.

This add-on is a fork and enhancement of Anki-StylusDraw by Rytis Petronis (Rytisgit).
It adds a full drawing toolkit: two customizable pens, a highlighter, and a 
stroke-based eraser with full undo/redo support.

Developed by Vijay to provide a more complete and customizable annotation
experience for all types of students.

Original Add-on: https://ankiweb.net/shared/info/1868980340
Source Code: https://github.com/vijay-collaborator/AnkiPenDown
"""
__addon_name__ = "AnkiPenDown"
__version__ = "1.5.1" # Bugfix for reviewer refresh method

from aqt import mw
from aqt.utils import showWarning
from anki.lang import _
from anki.hooks import addHook
from aqt.qt import QAction, QMenu, QColorDialog, QMessageBox, QInputDialog, QLabel,\
   QPushButton, QDialog, QVBoxLayout, QComboBox, QHBoxLayout, QSpinBox, QCheckBox
from aqt.qt import QKeySequence,QColor
from aqt.qt import pyqtSlot as slot

# This declarations are there only to be sure that in case of troubles
# with "profileLoaded" hook everything will work.
ts_state_on = False
ts_profile_loaded = False
ts_auto_hide = True
ts_auto_hide_pointer = True
ts_default_small_canvas = False
ts_zen_mode = False
ts_follow = False
ts_pen1_color = "#000000" # Default for Pen 1
ts_pen2_color = "#ff0000" # Default for Pen 2
ts_line_width = 4
ts_opacity = 0.7 # This is legacy, opacity is now per-stroke
ts_location = 1
ts_x_offset = 2
ts_y_offset = 2
ts_small_width = 500
ts_small_height = 500
ts_background_color = "#FFFFFF00"
ts_orient_vertical = True
ts_default_review_html = mw.reviewer.revHtml
ts_default_VISIBILITY = "true"

@slot()
def ts_change_pen1_color():
    """
    Open color picker and set chosen color for Pen 1.
    """
    global ts_pen1_color
    qcolor_old = QColor(ts_pen1_color)
    qcolor = QColorDialog.getColor(qcolor_old)
    if qcolor.isValid():
        ts_pen1_color = qcolor.name()
        # Reload the reviewer to apply the new color
        ts_switch()
        ts_switch()

@slot()
def ts_change_pen2_color():
    """
    Open color picker and set chosen color for Pen 2.
    """
    global ts_pen2_color
    qcolor_old = QColor(ts_pen2_color)
    qcolor = QColorDialog.getColor(qcolor_old)
    if qcolor.isValid():
        ts_pen2_color = qcolor.name()
        # Reload the reviewer to apply the new color
        ts_switch()
        ts_switch()

@slot()
def ts_change_width():
    global ts_line_width
    value, accepted = QInputDialog.getDouble(mw, "AnkiPenDown", "Enter the width:", ts_line_width)
    if accepted:
        ts_line_width = value
        execute_js("line_width = '" + str(ts_line_width) + "';")
        execute_js("if (typeof update_pen_settings === 'function') { update_pen_settings(); }")

class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AnkiPenDown Toolbar And Canvas")
        self.combo_box = QComboBox()
        self.combo_box.addItem("Top-Left")
        self.combo_box.addItem("Top-Right")
        self.combo_box.addItem("Bottom-Left")
        self.combo_box.addItem("Bottom-Right")
        combo_label = QLabel("Location:")
        range_label = QLabel("Offset:")
        start_range_label = QLabel("X Offset:")
        self.start_spin_box = QSpinBox()
        self.start_spin_box.setRange(0, 1000)
        small_width_label = QLabel("Non-Fullscreen Canvas Width:")
        self.small_width_spin_box = QSpinBox()
        self.small_width_spin_box.setRange(0, 9999)
        small_height_label = QLabel("Non-Fullscreen Canvas Height:")
        self.small_height_spin_box = QSpinBox()
        self.small_height_spin_box.setRange(0, 9999)
        end_range_label = QLabel("Y Offset:")
        self.end_spin_box = QSpinBox()
        self.end_spin_box.setRange(0, 1000)
        range_layout = QVBoxLayout()
        small_height_layout = QHBoxLayout()
        small_height_layout.addWidget(small_height_label)
        small_height_layout.addWidget(self.small_height_spin_box)
        small_width_layout = QHBoxLayout()
        small_width_layout.addWidget(small_width_label)
        small_width_layout.addWidget(self.small_width_spin_box)
        color_layout = QHBoxLayout()
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self.select_color)
        self.color_label = QLabel("Background color: #FFFFFF00")  # Initial color label
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_button)
        start_layout = QHBoxLayout()
        start_layout.addWidget(start_range_label)
        start_layout.addWidget(self.start_spin_box)
        end_layout = QHBoxLayout()
        end_layout.addWidget(end_range_label)
        end_layout.addWidget(self.end_spin_box)
        range_layout.addLayout(start_layout)
        range_layout.addLayout(end_layout)
        range_layout.addLayout(small_width_layout)
        range_layout.addLayout(small_height_layout)
        checkbox_label2 = QLabel("Orient vertically:")
        self.checkbox2 = QCheckBox()
        checkbox_layout2 = QHBoxLayout()
        checkbox_layout2.addWidget(checkbox_label2)
        checkbox_layout2.addWidget(self.checkbox2)
        accept_button = QPushButton("Accept")
        cancel_button = QPushButton("Cancel")
        reset_button = QPushButton("Default")
        accept_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        reset_button.clicked.connect(self.reset_to_default)
        button_layout = QHBoxLayout()
        button_layout.addWidget(accept_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(cancel_button)
        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(combo_label)
        dialog_layout.addWidget(self.combo_box)
        dialog_layout.addWidget(range_label)
        dialog_layout.addLayout(range_layout)
        dialog_layout.addLayout(checkbox_layout2)
        dialog_layout.addLayout(color_layout)
        dialog_layout.addLayout(button_layout)
        self.setLayout(dialog_layout)
    def set_values(self, combo_index, start_value, end_value, checkbox_state2, width, height, background_color):
        self.combo_box.setCurrentIndex(combo_index)
        self.start_spin_box.setValue(start_value)
        self.small_height_spin_box.setValue(height)
        self.small_width_spin_box.setValue(width)
        self.end_spin_box.setValue(end_value)
        self.checkbox2.setChecked(checkbox_state2)
        self.color_label.setText(f"Background color: {background_color}")
    def reset_to_default(self):
        self.combo_box.setCurrentIndex(1)
        self.start_spin_box.setValue(2)
        self.end_spin_box.setValue(2)
        self.small_height_spin_box.setValue(500)
        self.small_width_spin_box.setValue(500)
        self.checkbox2.setChecked(True)
        self.color_label.setText("Background color: #FFFFFF00")  # Reset color label
    def select_color(self):
        color_dialog = QColorDialog()
        qcolor_old = QColor(self.color_label.text()[-9:-2])
        color = color_dialog.getColor(qcolor_old, options=QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self.color_label.setText(f"Background color: {(color.name()+color.name(QColor.NameFormat.HexArgb)[1:3]).upper()}")

def get_css_for_toolbar_location(location, x_offset, y_offset, orient_column, canvas_width, canvas_height, background_color):
    orient = "column" if orient_column else "row"
    switch = {
        0: f"""
                        --button-bar-pt: {y_offset}px;
                        --button-bar-pr: unset;
                        --button-bar-pb: unset;
                        --button-bar-pl: {x_offset}px;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
        1: f"""
                        --button-bar-pt: {y_offset}px;
                        --button-bar-pr: {x_offset}px;
                        --button-bar-pb: unset;
                        --button-bar-pl: unset;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
        2: f"""
                        --button-bar-pt: unset;
                        --button-bar-pr: unset;
                        --button-bar-pb: {y_offset}px;
                        --button-bar-pl: {x_offset}px;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
        3: f"""
                        --button-bar-pt: unset;
                        --button-bar-pr: {x_offset}px;
                        --button-bar-pb: {y_offset}px;
                        --button-bar-pl: unset;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
    }
    return switch.get(location, """
                        --button-bar-pt: 2px;
                        --button-bar-pr: 2px;
                        --button-bar-pb: unset;
                        --button-bar-pl: unset;
                        --button-bar-orientation: column;
                        --small-canvas-height: 500;
                        --small-canvas-width: 500;
                        --background-color: #FFFFFF00;
                    """)

def get_css_for_auto_hide(auto_hide, zen):
    return "none" if auto_hide or zen else "flex"

def get_css_for_zen_mode(hide):
    return "none" if hide else "flex"

def get_css_for_auto_hide_pointer(auto_hide):
    return "none" if auto_hide else "default"

@slot()
def ts_change_toolbar_settings():
    global ts_orient_vertical, ts_y_offset, ts_x_offset, ts_location, ts_small_width, ts_small_height, ts_background_color
    dialog = CustomDialog()
    dialog.set_values(ts_location, ts_x_offset, ts_y_offset, ts_orient_vertical, ts_small_width, ts_small_height, ts_background_color)
    result = dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        ts_location = dialog.combo_box.currentIndex()
        ts_x_offset = dialog.start_spin_box.value()
        ts_y_offset = dialog.end_spin_box.value()
        ts_small_height = dialog.small_height_spin_box.value()
        ts_background_color = dialog.color_label.text()[-9:]
        ts_small_width = dialog.small_width_spin_box.value()
        ts_orient_vertical = dialog.checkbox2.isChecked()
        ts_switch()
        ts_switch()

def ts_save():
    """
    Saves configurable variables into profile, so they can
    be used to restore previous state after Anki restart.
    """
    mw.pm.profile['ts_state_on'] = ts_state_on
    mw.pm.profile['ts_pen1_color'] = ts_pen1_color
    mw.pm.profile['ts_pen2_color'] = ts_pen2_color
    mw.pm.profile['ts_line_width'] = ts_line_width
    mw.pm.profile['ts_auto_hide'] = ts_auto_hide
    mw.pm.profile['ts_auto_hide_pointer'] = ts_auto_hide_pointer
    mw.pm.profile['ts_default_small_canvas'] = ts_default_small_canvas
    mw.pm.profile['ts_zen_mode'] = ts_zen_mode
    mw.pm.profile['ts_follow'] = ts_follow
    mw.pm.profile['ts_location'] = ts_location
    mw.pm.profile['ts_x_offset'] = ts_x_offset
    mw.pm.profile['ts_y_offset'] = ts_y_offset
    mw.pm.profile['ts_small_height'] = ts_small_height
    mw.pm.profile['ts_background_color'] = ts_background_color
    mw.pm.profile['ts_small_width'] = ts_small_width
    mw.pm.profile['ts_orient_vertical'] = ts_orient_vertical

def ts_load():
    """
    Load configuration from profile, set states of checkable menu objects
    and turn on night mode if it were enabled on previous session.
    """
    global ts_state_on, ts_pen1_color, ts_pen2_color, ts_profile_loaded, ts_line_width, ts_auto_hide, ts_auto_hide_pointer, ts_default_small_canvas, ts_zen_mode, ts_follow, ts_orient_vertical, ts_y_offset, ts_x_offset, ts_location, ts_small_width, ts_small_height, ts_background_color
    try:
        ts_state_on = mw.pm.profile['ts_state_on']
        ts_pen1_color = mw.pm.profile['ts_pen1_color']
        ts_pen2_color = mw.pm.profile['ts_pen2_color']
        ts_line_width = mw.pm.profile['ts_line_width']
        ts_auto_hide = mw.pm.profile['ts_auto_hide']
        ts_auto_hide_pointer = mw.pm.profile['ts_auto_hide_pointer']
        ts_default_small_canvas = mw.pm.profile['ts_default_small_canvas']
        ts_zen_mode = mw.pm.profile['ts_zen_mode']
        ts_follow = mw.pm.profile['ts_follow']
        ts_orient_vertical = mw.pm.profile['ts_orient_vertical']
        ts_y_offset = mw.pm.profile['ts_y_offset']
        ts_small_width = mw.pm.profile['ts_small_width']
        ts_small_height = mw.pm.profile['ts_small_height']
        ts_background_color = mw.pm.profile['ts_background_color']
        ts_x_offset = mw.pm.profile['ts_x_offset']
        ts_location = mw.pm.profile['ts_location']
    except KeyError:
        ts_state_on = False
        ts_pen1_color = "#000000"
        ts_pen2_color = "#ff0000"
        ts_line_width = 4
        ts_auto_hide = True
        ts_auto_hide_pointer = True
        ts_default_small_canvas = False
        ts_zen_mode = False
        ts_follow = False
        ts_orient_vertical = True
        ts_y_offset = 2
        ts_small_width = 500
        ts_small_height = 500
        ts_background_color = "#FFFFFF00"
        ts_x_offset = 2
        ts_location = 1
    ts_profile_loaded = True
    ts_menu_auto_hide.setChecked(ts_auto_hide)
    ts_menu_auto_hide_pointer.setChecked(ts_auto_hide_pointer)
    ts_menu_small_default.setChecked(ts_default_small_canvas)
    ts_menu_zen_mode.setChecked(ts_zen_mode)
    ts_menu_follow.setChecked(ts_follow)
    if ts_state_on:
        ts_on()
    assure_plugged_in()

def execute_js(code):
    web_object = mw.reviewer.web
    web_object.eval(code)

def assure_plugged_in():
    global ts_default_review_html
    if not mw.reviewer.revHtml == custom:
        ts_default_review_html = mw.reviewer.revHtml
        mw.reviewer.revHtml = custom

def resize_js():
    execute_js("if (typeof resize === 'function') { setTimeout(resize, 101); }");

def clear_blackboard():
    assure_plugged_in()
    if ts_state_on:
        execute_js("if (typeof clear_canvas === 'function') { clear_canvas(); }")
        execute_js("if (typeof resize === 'function') { setTimeout(resize, 101); }");

def ts_onload():
    """
    Add hooks and initialize menu.
    Call to this function is placed on the end of this file.
    """
    addHook("unloadProfile", ts_save)
    addHook("profileLoaded", ts_load)
    addHook("showQuestion", clear_blackboard)
    addHook("showAnswer", resize_js)
    ts_setup_menu()

def blackboard():
    part1 = u"""
<div id="canvas_wrapper">
    <canvas id="highlighter_canvas" width="100" height="100"></canvas>
    <canvas id="pen_canvas" width="100" height="100"></canvas>
    <div id="pencil_button_bar">
        <button id="ts_visibility_button" class="active" title="Toggle visiblity (, comma)"
              onclick="switch_visibility();" >
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="m1 1 22 22" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        </button>
"""
    pen1_button = f"""
        <button id="ts_pen1_button" class="color-button active" title="Pen 1"
              onclick="set_pen_color('{ts_pen1_color}', this);" style="color: {ts_pen1_color};">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
            <path d="m15 5 4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
        </button>
"""
    pen2_button = f"""
        <button id="ts_pen2_button" class="color-button" title="Pen 2"
              onclick="set_pen_color('{ts_pen2_color}', this);" style="color: {ts_pen2_color};">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" stroke="{ts_pen2_color}" stroke-width="1.8" stroke-linejoin="round"/>
            <path d="m15 5 4 4" stroke="{ts_pen2_color}" stroke-width="1.8" stroke-linecap="round"/>
            <circle cx="18" cy="7" r="2" fill="{ts_pen2_color}" opacity="0.3"/>
        </svg>
        </button>
"""
    rest_of_blackboard = u"""
        <button id="ts_highlighter_button" class="color-button" title="Highlighter"
              onclick="set_highlighter_tool(this);" style="color: #FFD700;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 375 374.999991" preserveAspectRatio="xMidYMid meet" version="1.0"><defs><clipPath id="d487fbffe2"><path d="M 1 302.066406 L 337 302.066406 L 337 355 L 1 355 Z M 1 302.066406 " clip-rule="nonzero"/></clipPath><clipPath id="5297257e9c"><path d="M 24.71875 281 L 91.804688 281 L 91.804688 337.292969 L 24.71875 337.292969 Z M 24.71875 281 " clip-rule="nonzero"/></clipPath></defs><g clip-path="url(#d487fbffe2)"><path fill="#ffe746" d="M 75.542969 307.003906 C 103.488281 305.234375 131.191406 305.160156 159.296875 304.839844 C 188.367188 304.507812 217.523438 303.550781 246.597656 302.980469 C 266.847656 302.582031 287.039062 302.023438 307.242188 303.257812 C 313.714844 303.652344 320.195312 303.964844 326.671875 304.324219 C 328.8125 304.441406 330.9375 304.582031 333.070312 304.738281 C 334.273438 304.824219 337.109375 304.410156 336.65625 305.082031 C 333.714844 309.472656 331.59375 311.253906 322.925781 312.691406 C 320.585938 313.082031 318.222656 313.378906 315.835938 313.640625 C 314.570312 313.78125 310.875 313.753906 312.042969 314.078125 C 316.09375 315.210938 322.015625 314.449219 326.355469 314.34375 C 326.5625 314.335938 330.777344 314.132812 330.84375 314.304688 C 331.503906 316.015625 327.738281 319.214844 326.523438 320.609375 C 325.828125 321.40625 329.949219 323 330.304688 323.695312 C 330.621094 324.300781 329.296875 325.136719 328.984375 325.679688 C 328.097656 327.238281 330.550781 328.230469 328.542969 329.730469 C 326.839844 331.003906 316.144531 334.148438 315.902344 334.535156 C 314.601562 336.589844 325.832031 336.488281 326.96875 336.402344 C 327.378906 336.371094 331.734375 335.945312 331.746094 336.050781 C 331.871094 337.136719 331.101562 344.335938 330.648438 345.066406 C 329.945312 346.191406 326.773438 346.789062 326.371094 347.757812 C 326.054688 348.523438 328.917969 349.515625 329.066406 350.242188 C 329.328125 351.507812 323.792969 352.417969 322.4375 352.582031 C 294.40625 356.007812 257.105469 353.867188 228.898438 353.316406 C 177.347656 352.300781 125.871094 350.542969 74.320312 349.746094 C 55.832031 349.460938 36.445312 348.011719 18.027344 349.023438 C 13.691406 349.265625 9.359375 349.421875 5.003906 349.46875 C 4.691406 349.472656 1.457031 349.617188 1.289062 349.25 C 0.5 347.539062 6.460938 346.136719 8.101562 345.554688 C 13.804688 343.53125 18.375 342.34375 25.117188 343.179688 C 27.972656 343.535156 36.273438 345.585938 38.972656 344.09375 C 38.988281 344.085938 30.277344 341.789062 29.5 341.679688 C 24.710938 341.007812 19.207031 339.988281 14.285156 340.035156 C 12.75 340.050781 8.128906 340.660156 6.894531 339.886719 C 3.027344 337.460938 12.921875 335.925781 15.15625 335.917969 C 16.507812 335.917969 17.867188 335.957031 19.214844 335.972656 C 19.90625 335.976562 21.847656 336.160156 21.289062 335.917969 C 16.820312 333.976562 4.980469 334.503906 12.371094 329.902344 C 13.421875 329.25 14.835938 328.796875 15.855469 328.144531 C 17.097656 327.355469 13.300781 326.574219 12.375 325.640625 C 11.003906 324.257812 8.085938 320.515625 8.320312 318.859375 C 8.578125 317 13.148438 316.867188 13.949219 315.628906 C 15.085938 313.871094 9.558594 311.453125 11.570312 309.632812 C 14.804688 306.703125 23.355469 306.648438 28.523438 306.371094 C 41.371094 305.675781 62.757812 307.722656 75.542969 307.003906 Z M 75.542969 307.003906 " fill-opacity="1" fill-rule="evenodd"/></g><g clip-path="url(#5297257e9c)"><path fill="#fbcb2e" d="M 62.921875 281.160156 L 24.71875 319.382812 L 63.921875 337.292969 L 91.488281 309.738281 L 62.921875 281.160156 " fill-opacity="1" fill-rule="nonzero"/></g><path fill="#214060" d="M 78.515625 210.230469 C 78.515625 210.230469 77.949219 253.609375 48.679688 282.882812 C 45.855469 285.710938 47.9375 288.75 47.9375 288.75 L 83.902344 324.722656 C 83.902344 324.722656 86.941406 326.804688 89.765625 323.980469 C 119.03125 294.703125 162.402344 294.136719 162.402344 294.136719 L 143.027344 229.609375 L 78.515625 210.230469 " fill-opacity="1" fill-rule="nonzero"/><path fill="#fbcb2e" d="M 356.753906 75.300781 L 347.695312 66.242188 L 310.101562 62.5 L 306.359375 24.894531 L 297.300781 15.835938 C 290.722656 9.625 282.667969 9.910156 276.597656 14.667969 C 210.167969 69.339844 71.730469 203.445312 71.730469 203.445312 L 169.1875 300.921875 C 169.1875 300.921875 303.261719 162.453125 357.921875 96.007812 C 362.675781 89.941406 362.964844 81.878906 356.753906 75.300781 " fill-opacity="1" fill-rule="nonzero"/><path fill="#fbe278" d="M 306.359375 24.894531 L 155.277344 176.011719 C 149.28125 182.007812 149.28125 191.734375 155.277344 197.726562 L 174.902344 217.355469 C 180.898438 223.355469 190.621094 223.355469 196.613281 217.355469 L 347.695312 66.242188 L 306.359375 24.894531 " fill-opacity="1" fill-rule="nonzero"/></svg>
        </button>
        <button id="ts_eraser_button" class="color-button" title="Eraser"
              onclick="set_eraser_tool(this);" style="color: grey;">
        <svg viewBox="0 0 375 374.999991" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs><clipPath id="4c75e5e233"><path d="M 16.746094 37.5 L 357.996094 37.5 L 357.996094 326 L 16.746094 326 Z M 16.746094 37.5 " clip-rule="nonzero"/></clipPath></defs><g clip-path="url(#4c75e5e233)"><path fill="#bc3fde" d="M 273.546875 37.566406 C 267.605469 37.589844 261.613281 39.605469 256.671875 43.753906 L 60.019531 208.769531 C 47.769531 219.046875 45.03125 237.246094 53.570312 250.804688 L 97.9375 321.265625 C 99.171875 324.070312 101.949219 325.886719 105.015625 325.882812 C 105.050781 325.886719 105.082031 325.886719 105.117188 325.886719 L 350.429688 325.820312 C 353.214844 325.855469 355.804688 324.390625 357.207031 321.984375 C 358.609375 319.578125 358.609375 316.601562 357.207031 314.195312 C 355.800781 311.789062 353.210938 310.328125 350.425781 310.363281 L 194.96875 310.40625 L 346.828125 182.980469 C 359.078125 172.699219 361.820312 154.5 353.277344 140.941406 L 296.054688 50.070312 C 295.523438 49.230469 294.933594 48.449219 294.332031 47.679688 C 294.195312 47.46875 294.046875 47.261719 293.890625 47.0625 C 293.726562 46.867188 293.546875 46.695312 293.378906 46.503906 L 293.382812 46.503906 C 293.375 46.5 293.371094 46.496094 293.367188 46.492188 C 288.238281 40.613281 280.9375 37.535156 273.546875 37.566406 Z M 161.503906 143.785156 L 233.574219 257.839844 L 170.917969 310.414062 L 116.660156 310.429688 L 109.378906 310.429688 L 66.648438 242.570312 C 62.445312 235.898438 64.058594 225.554688 69.953125 220.605469 Z M 24.617188 241.5 C 21.753906 241.449219 19.09375 242.984375 17.710938 245.496094 C 16.328125 248.003906 16.445312 251.074219 18.019531 253.46875 L 25.636719 265.4375 C 27.097656 267.8125 29.726562 269.21875 32.511719 269.113281 C 35.300781 269.007812 37.816406 267.40625 39.09375 264.925781 C 40.367188 262.445312 40.207031 259.46875 38.675781 257.140625 L 31.058594 245.167969 C 29.675781 242.929688 27.25 241.546875 24.617188 241.5 Z M 45.066406 273.929688 C 42.199219 273.867188 39.539062 275.398438 38.144531 277.902344 C 36.753906 280.40625 36.863281 283.476562 38.425781 285.875 L 53.914062 310.386719 L 24.84375 310.433594 C 22.058594 310.398438 19.472656 311.871094 18.074219 314.277344 C 16.671875 316.6875 16.679688 319.660156 18.085938 322.066406 C 19.492188 324.46875 22.085938 325.929688 24.871094 325.886719 L 66.894531 325.820312 C 69.550781 326.195312 72.210938 325.164062 73.921875 323.097656 C 75.632812 321.035156 76.152344 318.226562 75.289062 315.6875 C 75.277344 315.652344 75.261719 315.613281 75.25 315.578125 C 75.1875 315.402344 75.121094 315.230469 75.046875 315.058594 C 74.824219 314.535156 74.542969 314.035156 74.210938 313.574219 L 51.492188 277.621094 C 50.117188 275.375 47.695312 273.984375 45.066406 273.929688 Z M 45.066406 273.929688 " fill-opacity="1" fill-rule="nonzero"/></g>
        </svg>
        </button>
        <button id="ts_undo_button" title="Undo the last stroke (Alt + z)"
              onclick="ts_undo();" >
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 3v5h5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        </button>
        <button id="ts_redo_button" title="Redo the last stroke (Alt + Y)"
              onclick="ts_redo();" >
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 12a9 9 0 1 1-9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 3v5h-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        </button>
        <button class="active" title="Clean canvas (. dot)"
              onclick="clear_canvas();" >
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 6h18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M10 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M14 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
        </button>
        <button id="ts_switch_fullscreen_button" class="active" title="Toggle fullscreen canvas(Alt + b)"
              onclick="switch_small_canvas();" >
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 3H5a2 2 0 0 0-2 2v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 8V5a2 2 0 0 0-2-2h-3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 16v3a2 2 0 0 0 2 2h3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M16 21h3a2 2 0 0 0 2-2v-3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        </button>
    </div>
</div>
<style>
:root {
  """ + get_css_for_toolbar_location( ts_location, ts_x_offset, ts_y_offset, ts_orient_vertical, ts_small_width, ts_small_height, ts_background_color) + """
}
body {
  overflow-x: hidden; /* Hide horizontal scrollbar */
}
#canvas_wrapper, #pen_canvas, #highlighter_canvas {
  touch-action: none;
  position:var(--canvas-bar-position);
  top: var(--canvas-bar-pt);
  right: var(--canvas-bar-pr);
  bottom: var(--canvas-bar-pb);
  left: var(--canvas-bar-pl);
}
#highlighter_canvas {
    z-index: 998;
    background: var(--background-color);
}
#pen_canvas {
    z-index: 999;
    background: transparent;
}
#pen_canvas, #highlighter_canvas {
  opacity: 1.0;
  border-style: none;
  border-width: 1px;
}
#pencil_button_bar {
  position: fixed;
  display: """+get_css_for_zen_mode(ts_zen_mode)+""";
  flex-direction: var(--button-bar-orientation);
  opacity: .5;
  top: var(--button-bar-pt);
  right: var(--button-bar-pr);
  bottom: var(--button-bar-pb);
  left: var(--button-bar-pl);
  z-index: 8000;
  transition: .5s;
} #pencil_button_bar:hover {
  opacity: 1;
} #pencil_button_bar > button {
  margin: 2px;
} #pencil_button_bar > button > svg {
  width: 2em;
} #pencil_button_bar > button:hover > svg {
  filter: drop-shadow(0 0 4px #000);
}
#pencil_button_bar > button.active:not(.color-button) > svg {
  stroke: #000;
}
.night_mode #pencil_button_bar > button.active:not(.color-button) > svg {
  stroke: #eee;
}
#pencil_button_bar > button.color-button.active > svg {
    filter: drop-shadow(0 0 3px #000);
}
#pencil_button_bar > button:not(.color-button) > svg > path {
  stroke: #888;
}
.nopointer {
  cursor: """+get_css_for_auto_hide_pointer(ts_auto_hide_pointer)+""" !important;
}
.touch_disable > button:not(:first-child){
    display: none;
}
.nopointer #pencil_button_bar
{
  display: """+get_css_for_auto_hide(ts_auto_hide, ts_zen_mode)+""";
}
</style>
<script>
var visible = """ + ts_default_VISIBILITY + """;
var wrapper = document.getElementById('canvas_wrapper');
var pen_canvas = document.getElementById('pen_canvas');
var highlighter_canvas = document.getElementById('highlighter_canvas');
var optionBar = document.getElementById('pencil_button_bar');
var ts_undo_button = document.getElementById('ts_undo_button');
var ts_redo_button = document.getElementById('ts_redo_button');
var pen_ctx = pen_canvas.getContext('2d');
var highlighter_ctx = highlighter_canvas.getContext('2d');
var ts_visibility_button = document.getElementById('ts_visibility_button');
var ts_switch_fullscreen_button = document.getElementById('ts_switch_fullscreen_button');
var strokes_data = [ ];
var redo_stack = [ ];
var color = '#000000';
var line_width = 4;
var current_tool = 'pen'; // 'pen', 'highlighter', or 'eraser'
var small_canvas = """ +  str(ts_default_small_canvas).lower() + """;
var fullscreen_follow = """ + str(ts_follow).lower() + """;
pen_canvas.onselectstart = function() { return false; };
highlighter_canvas.onselectstart = function() { return false; };
wrapper.onselectstart = function() { return false; };
function manage_active_button(clicked_button) {
    var color_buttons = document.getElementsByClassName('color-button');
    for (var i = 0; i < color_buttons.length; i++) {
        color_buttons[i].classList.remove('active');
    }
    clicked_button.classList.add('active');
}
function set_pen_color(new_color, clicked_button) {
    current_tool = 'pen';
    color = new_color;
    manage_active_button(clicked_button);
}
function set_highlighter_tool(clicked_button) {
    current_tool = 'highlighter';
    manage_active_button(clicked_button);
}
function set_eraser_tool(clicked_button) {
    current_tool = 'eraser';
    manage_active_button(clicked_button);
}
function switch_small_canvas()
{
    stop_drawing();
    small_canvas = !small_canvas;
    if(!small_canvas)
    {
        ts_switch_fullscreen_button.className = 'active';
    }
    else{
        ts_switch_fullscreen_button.className = '';
    }
    resize();
}
function switch_visibility()
{
	stop_drawing();
    if (visible)
    {
        pen_canvas.style.display='none';
        highlighter_canvas.style.display='none';
        ts_visibility_button.className = '';
        optionBar.className = 'touch_disable';
    }
    else
    {
        pen_canvas.style.display='block';
        highlighter_canvas.style.display='block';
        ts_visibility_button.className = 'active';
        optionBar.className = '';
    }
    visible = !visible;
}
pen_canvas.addEventListener("pointerdown", pointerDownLine);
pen_canvas.addEventListener("pointermove", pointerMoveLine);
window.addEventListener("pointerup", pointerUpLine);
function resize() {
    var card = document.getElementsByClassName('card')[0]
    if (!card){
        window.setTimeout(resize, 100)
        return;
    }
    canvas_wrapper.style.display='none';
    pen_canvas.style["border-style"] = "none";
    highlighter_canvas.style["border-style"] = "none";
    document.documentElement.style.setProperty('--canvas-bar-pt', '0px');
    document.documentElement.style.setProperty('--canvas-bar-pr', '0px');
    document.documentElement.style.setProperty('--canvas-bar-pb', 'unset');
    document.documentElement.style.setProperty('--canvas-bar-pl', 'unset');
    document.documentElement.style.setProperty('--canvas-bar-position', 'absolute');
    var target_width, target_height;
    if(!small_canvas && !fullscreen_follow){
        target_width = Math.max(card.scrollWidth, document.documentElement.clientWidth);
        target_height = Math.max(document.documentElement.scrollHeight, document.documentElement.clientHeight);
    }
    else if(small_canvas){
        target_width = Math.min(document.documentElement.clientWidth,
        getComputedStyle(document.documentElement).getPropertyValue('--small-canvas-width'));
        target_height = Math.min(document.documentElement.clientHeight,
        getComputedStyle(document.documentElement).getPropertyValue('--small-canvas-height'));
        pen_canvas.style["border-style"] = "dashed";
        highlighter_canvas.style["border-style"] = "dashed";
        document.documentElement.style.setProperty('--canvas-bar-pt',
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pt'));
        document.documentElement.style.setProperty('--canvas-bar-pr',
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pr'));
        document.documentElement.style.setProperty('--canvas-bar-pb',
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pb'));
        document.documentElement.style.setProperty('--canvas-bar-pl',
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pl'));
        document.documentElement.style.setProperty('--canvas-bar-position', 'fixed');
    }
    else{
        document.documentElement.style.setProperty('--canvas-bar-position', 'fixed');
        target_width = document.documentElement.clientWidth-1;
        target_height = document.documentElement.clientHeight-1;
    }
    [pen_ctx, highlighter_ctx].forEach(function(ctx) {
        ctx.canvas.width = target_width;
        ctx.canvas.height = target_height;
    });
    canvas_wrapper.style.display='block';
    var dpr = window.devicePixelRatio || 1;
    pen_canvas.style.width = target_width + 'px';
    pen_canvas.style.height = target_height + 'px';
    highlighter_canvas.style.width = target_width + 'px';
    highlighter_canvas.style.height = target_height + 'px';
    [pen_ctx, highlighter_ctx].forEach(function(ctx) {
        ctx.canvas.width *= dpr;
        ctx.canvas.height *= dpr;
        ctx.scale(dpr, dpr);
        ctx.lineJoin = 'round';
    });
    ts_redraw();
}
window.addEventListener('resize', resize);
window.addEventListener('load', resize);
window.requestAnimationFrame(draw_last_line_segment);
var isPointerDown = false;
function ts_undo(){
    stop_drawing();
    if (strokes_data.length < 1) return;
    
    var undone_stroke = strokes_data.pop();
    redo_stack.push(undone_stroke);

    if (undone_stroke.tool === 'eraser' && undone_stroke.erasedIndices) {
        undone_stroke.erasedIndices.forEach(function(index) {
            if (strokes_data[index]) {
                strokes_data[index].visible = true;
            }
        });
    }

    ts_redo_button.className = "active";
    ts_redraw();
    if (strokes_data.length === 0) {
        ts_undo_button.className = "";
    }
}
function ts_redo() {
    stop_drawing();
    if (redo_stack.length < 1) return;
    
    var redone_stroke = redo_stack.pop();
    strokes_data.push(redone_stroke);

    if (redone_stroke.tool === 'eraser' && redone_stroke.erasedIndices) {
        redone_stroke.erasedIndices.forEach(function(index) {
            if (strokes_data[index]) {
                strokes_data[index].visible = false;
            }
        });
    }

    ts_undo_button.className = "active";
    ts_redraw();
    if (redo_stack.length === 0) {
        ts_redo_button.className = "";
    }
}
function ts_redraw() {
	pleaseRedrawEverything = true;
}
function clear_canvas()
{
	stop_drawing();
    strokes_data = [];
    redo_stack = [];
    ts_redo_button.className = "";
    ts_undo_button.className = "";
	ts_redraw();
}
function stop_drawing() {
	isPointerDown = false;
	drawingWithPressurePenOnly = false;
}
function start_drawing() {
    ts_undo_button.className = "active"
    isPointerDown = true;
}
function draw_last_line_segment() {
    window.requestAnimationFrame(draw_last_line_segment);
    draw_upto_latest_point_async(nextLine, nextPoint);
}
var nextLine = 0;
var nextPoint = 0;
var p1,p2,p3;
function all_drawing_finished(i){
    return (!isPointerDown && strokes_data.length-1 == i)
}
async function draw_path_at_some_point_async(active_ctx, startX, startY, midX, midY, endX, endY, lineWidth) {
		active_ctx.beginPath();
		active_ctx.moveTo((startX + (midX - startX) / 2), (startY + (midY - startY)/ 2));
		active_ctx.quadraticCurveTo(midX, midY, (midX + (endX - midX) / 2), (midY + (endY - midY)/ 2));
		active_ctx.lineWidth = lineWidth;
		active_ctx.stroke();
};
var pleaseRedrawEverything = false;
async function draw_upto_latest_point_async(startLine, startPoint){
	var fullRedraw = false;
	if (pleaseRedrawEverything) {
	    fullRedraw = true;
	    startLine = 0;
	    startPoint = 0;
	    pen_ctx.clearRect(0, 0, pen_ctx.canvas.width, pen_ctx.canvas.height);
        highlighter_ctx.clearRect(0, 0, highlighter_ctx.canvas.width, highlighter_ctx.canvas.height);
	}
	for(var i = startLine; i < strokes_data.length; i++){
        var stroke = strokes_data[i];

        if (stroke.visible === false) { continue; }

        var current_points = stroke.points;
        function drawTheStroke(active_ctx) {
            p2 = current_points[startPoint > 1 ? startPoint-2 : 0];
            p3 = current_points[startPoint > 0 ? startPoint-1 : 0];
            for(var j = startPoint; j < current_points.length; j++){
                nextPoint = j + 1;
                p1 = p2;
                p2 = p3;
                p3 = current_points[j];
                draw_path_at_some_point_async(active_ctx, p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],p3[3]);
            }
        }
        if (stroke.tool === 'eraser') {
            continue;
        } else {
            var active_ctx = (stroke.tool === 'pen') ? pen_ctx : highlighter_ctx;
            active_ctx.save();
            active_ctx.globalCompositeOperation = 'source-over';
            active_ctx.strokeStyle = stroke.color;
            active_ctx.globalAlpha = stroke.opacity;
            if (stroke.tool === 'highlighter') {
                active_ctx.lineCap = 'butt';
            } else {
                active_ctx.lineCap = 'round';
            }
            drawTheStroke(active_ctx);
            active_ctx.restore();
        }
		nextLine = i;
		p2 = current_points[startPoint > 1 ? startPoint-2 : 0];
		p3 = current_points[startPoint > 0 ? startPoint-1 : 0];
        for(var j = startPoint; j < current_points.length; j++){
			nextPoint = j + 1;
			p1 = p2;
			p2 = p3;
			p3 = current_points[j];
        }
        if(all_drawing_finished(i)){
            nextLine++;
            nextPoint = 0;
        }
        startPoint = 0;
    }
	if (fullRedraw) {
        pleaseRedrawEverything = false;
	    fullRedraw = false;
        nextPoint = 0;
	}
}
function doLineSegmentsIntersect(p0, p1, p2, p3) {
    var s1_x = p1[0] - p0[0];
    var s1_y = p1[1] - p0[1];
    var s2_x = p3[0] - p2[0];
    var s2_y = p3[1] - p2[1];
    var s = (-s1_y * (p0[0] - p2[0]) + s1_x * (p0[1] - p2[1])) / (-s2_x * s1_y + s1_x * s2_y);
    var t = ( s2_x * (p0[1] - p2[1]) - s2_y * (p0[0] - p2[0])) / (-s2_x * s1_y + s1_x * s2_y);
    if (s >= 0 && s <= 1 && t >= 0 && t <= 1) {
        return true;
    }
    return false;
}
function doesStrokeIntersectEraser(targetStroke, eraserStroke) {
    for (var i = 0; i < targetStroke.points.length - 1; i++) {
        for (var j = 0; j < eraserStroke.points.length - 1; j++) {
            if (doLineSegmentsIntersect(
                targetStroke.points[i], targetStroke.points[i + 1],
                eraserStroke.points[j], eraserStroke.points[j + 1]
            )) {
                return true;
            }
        }
    }
    return false;
}
function eraseIntersectingStrokes() {
    if (strokes_data.length < 2) return; 

    var eraserStroke = strokes_data[strokes_data.length - 1];
    eraserStroke.erasedIndices = []; 

    for (var i = 0; i < strokes_data.length - 1; i++) {
        var currentStroke = strokes_data[i];
        
        if ((currentStroke.tool === 'pen' || currentStroke.tool === 'highlighter') && currentStroke.visible !== false) {
            if (doesStrokeIntersectEraser(currentStroke, eraserStroke)) {
                currentStroke.visible = false;
                eraserStroke.erasedIndices.push(i);
            }
        }
    }
    ts_redraw();
}
var drawingWithPressurePenOnly = false;
function pointerDownLine(e) {
    wrapper.classList.add('nopointer');
	if (!e.isPrimary) { return; }
	if (e.pointerType[0] == 'p') { drawingWithPressurePenOnly = true }
	else if ( drawingWithPressurePenOnly) { return; }
    if(!isPointerDown){
        event.preventDefault();
        redo_stack = [];
        ts_redo_button.className = "";
        let stroke_color, stroke_width, stroke_opacity;
        let point_width = line_width;
        if (current_tool === 'pen') {
            stroke_color = color;
            stroke_width = line_width;
            stroke_opacity = 1.0;
            point_width = e.pointerType[0] == 'p' ? (1.0 + e.pressure * line_width * 2) : line_width
        } else if (current_tool === 'highlighter') {
            stroke_color = '#FFFF00';
            stroke_width = 20;
            stroke_opacity = 0.4;
            point_width = stroke_width;
        } else { // eraser
            stroke_color = 'rgba(0,0,0,1)';
            stroke_width = 20;
            stroke_opacity = 1.0;
            point_width = stroke_width;
        }
        strokes_data.push({
            tool: current_tool,
            color: stroke_color,
            width: stroke_width,
            opacity: stroke_opacity,
            visible: true,
            points: [[
			    e.offsetX,
			    e.offsetY,
                e.pointerType[0] == 'p' ? e.pressure : 2,
			    point_width
            ]]
        });
        start_drawing();
    }
}
function pointerMoveLine(e) {
	if (!e.isPrimary) { return; }
	if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
    if (isPointerDown) {
        let last_stroke = strokes_data[strokes_data.length-1];
        let point_width = (last_stroke.tool === 'pen')
            ? (e.pointerType[0] == 'p' ? (1.0 + e.pressure * line_width * 2) : line_width)
            : last_stroke.width;
        last_stroke.points.push([
			e.offsetX,
			e.offsetY,
            e.pointerType[0] == 'p' ? e.pressure : 2,
			point_width]);
    }
}
function pointerUpLine(e) {
    wrapper.classList.remove('nopointer');
	if (!e.isPrimary) { return; }
	if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
    if (isPointerDown) {
        let last_stroke = strokes_data[strokes_data.length-1];
        let point_width = (last_stroke.tool === 'pen')
            ? (e.pointerType[0] == 'p' ? (1.0 + e.pressure * line_width * 2) : line_width)
            : last_stroke.width;
        last_stroke.points.push([
			e.offsetX,
			e.offsetY,
            e.pointerType[0] == 'p' ? e.pressure : 2,
			point_width]);

        if (current_tool === 'eraser') {
            eraseIntersectingStrokes();
        }
    }
	stop_drawing();
}
document.addEventListener('keyup', function(e) {
    if ((e.keyCode == 90 || e.keyCode == 122) && e.altKey) {
		e.preventDefault();
        ts_undo();
    }
    if ((e.keyCode == 89 || e.keyCode == 121) && e.altKey) {
        e.preventDefault();
        ts_redo();
    }
    if (e.key === ".") {
        clear_canvas();
    }
	if (e.key === ",") {
        switch_visibility();
    }
    if ((e.key === "b" || e.key === "B") && e.altKey) {
        e.preventDefault();
        switch_small_canvas();
    }
})
</script>
"""
    return part1 + pen1_button + pen2_button + rest_of_blackboard

def custom(*args, **kwargs):
    global ts_state_on
    default = ts_default_review_html(*args, **kwargs)
    if not ts_state_on:
        return default
    output = (
        default +
        blackboard() +
        "<script>line_width = '" + str(ts_line_width) + "'</script>"
    )
    return output
mw.reviewer.revHtml = custom

def checkProfile():
    if not ts_profile_loaded:
        showWarning("No profile loaded. AnkiPenDown may not work correctly.")
        return False
    return True

def ts_on():
    """
    Turn on
    """
    if not checkProfile(): return
    global ts_state_on
    ts_state_on = True
    ts_menu_switch.setChecked(True)

def ts_off():
    """
    Turn off
    """
    if not checkProfile(): return
    global ts_state_on
    ts_state_on = False
    ts_menu_switch.setChecked(False)

@slot()
def ts_change_auto_hide_settings():
    """
    Switch auto hide toolbar setting.
    """
    global ts_auto_hide
    ts_auto_hide = not ts_auto_hide
    ts_switch()
    ts_switch()

@slot()
def ts_change_follow_settings():
    """
    Switch whiteboard follow screen.
    """
    global ts_follow
    ts_follow = not ts_follow
    execute_js("fullscreen_follow = " + str(ts_follow).lower() + ";")
    execute_js("if (typeof resize === 'function') { resize(); }")

@slot()
def ts_change_small_default_settings():
    """
    Switch default small canvas mode setting.
    """
    global ts_default_small_canvas
    ts_default_small_canvas = not ts_default_small_canvas
    ts_switch()
    ts_switch()

@slot()
def ts_change_zen_mode_settings():
    """
    Switch default zen mode setting.
    """
    global ts_zen_mode
    ts_zen_mode = not ts_zen_mode
    ts_switch()
    ts_switch()

@slot()
def ts_change_auto_hide_pointer_settings():
    """
    Switch auto hide pointer setting.
    """
    global ts_auto_hide_pointer
    ts_auto_hide_pointer = not ts_auto_hide_pointer
    ts_switch()
    ts_switch()

@slot()
def ts_switch():
    """
    Switch AnkiPenDown.
    """
    if ts_state_on:
        ts_off()
    else:
        ts_on()
    # Reload current screen.
    if mw.state == "review":
        mw.moveToState("review")
    elif mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    elif mw.state == "overview":
        mw.overview.refresh()

def ts_setup_menu():
    """
    Initialize menu.
    """
    global ts_menu_switch, ts_menu_auto_hide, ts_menu_auto_hide_pointer, ts_menu_small_default, ts_menu_zen_mode, ts_menu_follow
    try:
        mw.addon_view_menu
    except AttributeError:
        mw.addon_view_menu = QMenu("""&AnkiPenDown""", mw)
        mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(), mw.addon_view_menu)
        
    ts_menu_switch = QAction("""&Enable AnkiPenDown""", mw, checkable=True)
    ts_menu_auto_hide = QAction("""Auto &hide toolbar when drawing""", mw, checkable=True)
    ts_menu_auto_hide_pointer = QAction("""Auto &hide pointer when drawing""", mw, checkable=True)
    ts_menu_follow = QAction("""&Follow when scrolling (faster on big cards)""", mw, checkable=True)
    ts_menu_small_default = QAction("""&Small Canvas by default""", mw, checkable=True)
    ts_menu_zen_mode = QAction("""Enable Zen Mode (hide toolbar until disabled)""", mw, checkable=True)
    
    ts_pen_color_menu = QMenu("Set &pen color", mw)
    ts_menu_pen1_color = QAction("Set Pen 1 Color", mw)
    ts_menu_pen2_color = QAction("Set Pen 2 Color", mw)
    ts_pen_color_menu.addAction(ts_menu_pen1_color)
    ts_pen_color_menu.addAction(ts_menu_pen2_color)

    ts_menu_width = QAction("""Set pen &width""", mw)
    ts_toolbar_settings = QAction("""&Toolbar and canvas location settings""", mw)
    ts_toggle_seq = QKeySequence("Ctrl+r")
    ts_menu_switch.setShortcut(ts_toggle_seq)
    
    mw.addon_view_menu.addAction(ts_menu_switch)
    mw.addon_view_menu.addAction(ts_menu_auto_hide)
    mw.addon_view_menu.addAction(ts_menu_auto_hide_pointer)
    mw.addon_view_menu.addAction(ts_menu_follow)
    mw.addon_view_menu.addAction(ts_menu_small_default)
    mw.addon_view_menu.addAction(ts_menu_zen_mode)
    mw.addon_view_menu.addMenu(ts_pen_color_menu)
    mw.addon_view_menu.addAction(ts_menu_width)
    mw.addon_view_menu.addAction(ts_toolbar_settings)
    
    ts_menu_switch.triggered.connect(ts_switch)
    ts_menu_auto_hide.triggered.connect(ts_change_auto_hide_settings)
    ts_menu_auto_hide_pointer.triggered.connect(ts_change_auto_hide_pointer_settings)
    ts_menu_follow.triggered.connect(ts_change_follow_settings)
    ts_menu_small_default.triggered.connect(ts_change_small_default_settings)
    ts_menu_zen_mode.triggered.connect(ts_change_zen_mode_settings)
    ts_menu_pen1_color.triggered.connect(ts_change_pen1_color)
    ts_menu_pen2_color.triggered.connect(ts_change_pen2_color)
    ts_menu_width.triggered.connect(ts_change_width)
    ts_toolbar_settings.triggered.connect(ts_change_toolbar_settings)

#
# ONLOAD SECTION
#
ts_onload()
