import sys
import os
import time
import math
import traceback
import json
import random
from collections import deque

# =====================================================================
#             ПЕРЕХВАТ ОШИБОК (ТОЛЬКО ДЛЯ СБОЕВ ЗАПУСКА)
# =====================================================================
def gui_exception_handler(exctype, value, tb):
    err_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(err_msg, file=sys.stderr)
    try:
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Ошибка в Motion Suite:\n\n{err_msg}", "Motion Suite — Ошибка", 0x10)
    except Exception:
        pass
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = gui_exception_handler

# =====================================================================
#                 WIN32 API И 64-БИТНЫЕ СТРУКТУРЫ
# =====================================================================
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    kernel32 = ctypes.windll.kernel32
    oleacc = ctypes.windll.oleacc

    # Привязка собственного ID приложения для отображения Icon.ico на панели задач Windows
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MotionSuite.FlowCursor.FlowText.1.0")
    except Exception:
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness.argtypes = [ctypes.c_int]
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    try:
        ctypes.windll.ole32.CoInitialize(None)
    except Exception:
        pass

    try:
        winmm = ctypes.windll.winmm
        winmm.timeBeginPeriod.argtypes = [ctypes.c_uint]
        winmm.timeBeginPeriod(1)
    except Exception:
        pass

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_int32), ("y", ctypes.c_int32)]

    class CURSORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_uint32),
            ("flags", ctypes.c_uint32),
            ("hCursor", ctypes.c_void_p),
            ("ptScreenPos", POINT)
        ]

    class ICONINFO(ctypes.Structure):
        _fields_ = [
            ("fIcon", ctypes.c_int32),
            ("xHotspot", ctypes.c_uint32),
            ("yHotspot", ctypes.c_uint32),
            ("hbmMask", ctypes.c_void_p),
            ("hbmColor", ctypes.c_void_p),
        ]

    class BITMAP(ctypes.Structure):
        _fields_ = [
            ("bmType", ctypes.c_int32),
            ("bmWidth", ctypes.c_int32),
            ("bmHeight", ctypes.c_int32),
            ("bmWidthBytes", ctypes.c_int32),
            ("bmPlanes", ctypes.c_uint16),
            ("bmBitsPixel", ctypes.c_uint16),
            ("bmBits", ctypes.c_void_p),
        ]

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32),
            ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32),
            ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16),
            ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32),
            ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32),
            ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BITMAPINFOHEADER),
            ("bmiColors", ctypes.c_uint32 * 3),
        ]

    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_uint32),
            ("flags", ctypes.c_uint32),
            ("hwndActive", ctypes.c_void_p),
            ("hwndFocus", ctypes.c_void_p),
            ("hwndCapture", ctypes.c_void_p),
            ("hwndMenuOwner", ctypes.c_void_p),
            ("hwndMoveSize", ctypes.c_void_p),
            ("hwndCaret", ctypes.c_void_p),
            ("rcCaret", wintypes.RECT)
        ]

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_uint32),
            ("Data2", ctypes.c_uint16),
            ("Data3", ctypes.c_uint16),
            ("Data4", ctypes.c_uint8 * 8)
        ]

    IID_IAccessible = GUID(
        0x618736E0, 0x3C3D, 0x11CF,
        (ctypes.c_uint8 * 8)(0x81, 0x0C, 0x00, 0xAA, 0x00, 0x38, 0x9B, 0x71)
    )

    OBJID_CARET = 0xFFFFFFF8
    CHILDID_SELF = 0
    VT_I4 = 3

    if ctypes.sizeof(ctypes.c_void_p) == 8:
        class VARIANT(ctypes.Structure):
            _fields_ = [
                ("vt", ctypes.c_uint16),
                ("wReserved1", ctypes.c_uint16),
                ("wReserved2", ctypes.c_uint16),
                ("wReserved3", ctypes.c_uint16),
                ("lVal", ctypes.c_int64),
                ("padding", ctypes.c_int64)
            ]
    else:
        class VARIANT(ctypes.Structure):
            _fields_ = [
                ("vt", ctypes.c_uint16),
                ("wReserved1", ctypes.c_uint16),
                ("wReserved2", ctypes.c_uint16),
                ("wReserved3", ctypes.c_uint16),
                ("lVal", ctypes.c_int32),
                ("padding", ctypes.c_int32)
            ]

    ACC_LOC_PROTO = ctypes.WINFUNCTYPE(
        ctypes.c_long,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_long),
        ctypes.POINTER(ctypes.c_long),
        ctypes.POINTER(ctypes.c_long),
        ctypes.POINTER(ctypes.c_long),
        VARIANT
    )
    RELEASE_PROTO = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)

    user32.GetCursorInfo.argtypes = [ctypes.c_void_p]
    user32.GetCursorInfo.restype = wintypes.BOOL

    user32.GetIconInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.GetIconInfo.restype = wintypes.BOOL

    user32.GetDC.argtypes = [ctypes.c_void_p]
    user32.GetDC.restype = ctypes.c_void_p

    user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.ReleaseDC.restype = ctypes.c_int

    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = ctypes.c_void_p

    user32.GetDesktopWindow.argtypes = []
    user32.GetDesktopWindow.restype = ctypes.c_void_p

    user32.GetShellWindow.argtypes = []
    user32.GetShellWindow.restype = ctypes.c_void_p

    user32.GetClassNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int

    user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.GetWindowRect.restype = wintypes.BOOL

    try:
        GetWindowLong = user32.GetWindowLongPtrW
    except AttributeError:
        GetWindowLong = user32.GetWindowLongW
    GetWindowLong.argtypes = [ctypes.c_void_p, ctypes.c_int]
    GetWindowLong.restype = ctypes.c_ssize_t

    try:
        SetWindowLong = user32.SetWindowLongPtrW
    except AttributeError:
        SetWindowLong = user32.SetWindowLongW
    SetWindowLong.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
    SetWindowLong.restype = ctypes.c_ssize_t

    user32.SetWindowPos.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.BringWindowToTop.argtypes = [ctypes.c_void_p]
    user32.BringWindowToTop.restype = wintypes.BOOL

    user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.c_void_p]
    user32.GetGUIThreadInfo.restype = wintypes.BOOL

    user32.ClientToScreen.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.ClientToScreen.restype = wintypes.BOOL

    user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL

    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int

    gdi32.GetObjectW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    gdi32.GetObjectW.restype = ctypes.c_int

    gdi32.GetDIBits.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint
    ]
    gdi32.GetDIBits.restype = ctypes.c_int

    gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
    gdi32.DeleteObject.restype = wintypes.BOOL

    kernel32.GetConsoleWindow.argtypes = []
    kernel32.GetConsoleWindow.restype = ctypes.c_void_p

    oleacc.AccessibleObjectFromWindow.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_void_p
    ]
    oleacc.AccessibleObjectFromWindow.restype = ctypes.c_long

from PyQt6.QtCore import Qt, QTimer, QPointF, QRect, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QCursor, QPolygonF, QPixmap, QImage, QIcon, QFont
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu,
    QVBoxLayout, QHBoxLayout, QLabel, QSlider, QComboBox,
    QPushButton, QCheckBox, QColorDialog, QGroupBox, QRadioButton,
    QTabWidget, QFileDialog
)

try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False

if HAS_OPENGL:
    from PyQt6.QtGui import QSurfaceFormat
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    fmt.setDepthBufferSize(0)
    fmt.setStencilBufferSize(0)
    fmt.setSamples(0)
    fmt.setSwapInterval(0)
    QSurfaceFormat.setDefaultFormat(fmt)

NUM_CPU_CORES = os.cpu_count() or 8

# =====================================================================
#                 КОНФИГУРАЦИЯ ПО УМОЛЧАНИЮ
# =====================================================================
DEFAULT_CONFIG = {
    "RENDER_BACKEND": "CPU",
    "DIRTY_RECT_OPT": True,
    "AUTO_LOAD_SCALING": True,
    "CPU_LIMIT_ENABLED": True,
    "CPU_MAX_BUDGET": 0.8,

    "ENABLED": True,
    "HIDE_IN_GAMES": False,
    "SHOW_IN_GAMES": True,             # Принудительный показ в играх (Geometry Dash и др.)
    "BLUR_DURATION": 0.040,
    "BLUR_INTENSITY": 85,
    "FALLOFF_EXP": 2.2,
    "STEP_PIXELS": 1.5,

    "CUSTOM_CURSORS": True,
    "CURSOR_MODE": "System",           # "System", "Vector", "Custom File"
    "CUSTOM_CURSOR_PATH": "",          # Путь к файлу курсора PNG / CUR / ICO
    "HOTSPOT_MODE": "TopLeft",         # "TopLeft", "Center"
    "CURSOR_SCALE": 1.0,
    "OUTLINE_WIDTH": 0.4,
    "OUTLINE_OPACITY": 25,
    "CURSOR_COLOR": (255, 255, 255),
    "OUTLINE_COLOR": (0, 0, 0),

    "MAX_COPIES": 40,
    "DEADZONE_PX": 2.5,
    "MIN_SPEED": 1.0,
    "TARGET_FPS": 144,

    # FlowText (Каретка)
    "FT_ENABLED": True,
    "FT_EFFECT": "Fluid Elastic",      # "Fluid Elastic", "Cyberpunk Glitch", "Sparkler Particles", "Snappy Glide"
    "FT_SMOOTH_SPEED": 0.38,           # Базовая скорость скольжения
    "FT_ELASTICITY": 1.2,              # Коэффициент эластичности капсулы
    "FT_WIDTH": 2.5,                   # Базовая толщина каретки
    "FT_COLOR": (88, 166, 255),        # Цвет каретки
    "FT_GLOW_RADIUS": 6,               # Радиус свечения
    "FT_GLOW_OPACITY": 50,             # Прозрачность свечения (%)
    "FT_PULSE_IDLE": True,             # Мягкое дыхание в покое
    "FT_HIDE_IN_GAMES": False,         # Сон каретки в полноэкранных 3D играх
    "FT_GAME_SHIELD": True,            # Аппаратный обход хуков
}

CONFIG = dict(DEFAULT_CONFIG)

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "config.json")

def load_config():
    path = get_config_path()
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    if k in DEFAULT_CONFIG:
                        if isinstance(DEFAULT_CONFIG[k], tuple) and isinstance(v, list):
                            CONFIG[k] = tuple(v)
                        else:
                            CONFIG[k] = v
        except Exception:
            pass

def save_config():
    path = get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(CONFIG, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

load_config()

# =====================================================================
#      ЗАГРУЗКА ИКОНКИ Icon.ico С ПОЛНОЙ ПРОЗРАЧНОСТЬЮ
# =====================================================================
def get_app_icon():
    """
    Ищет Icon.ico рядом с запускаемым файлом (в том числе при сборке в .exe).
    Сохраняет альфа-канал и прозрачность фона.
    Если файл отсутствует, генерирует аккуратную векторную стрелку.
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    candidate_names = ["Icon.ico", "icon.ico", "Icon.png", "icon.png"]
    for name in candidate_names:
        icon_path = os.path.join(base_dir, name)
        if os.path.isfile(icon_path):
            ico = QIcon(icon_path)
            if not ico.isNull():
                return ico

    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(QColor(88, 166, 255))
    p.setPen(QPen(QColor(240, 246, 252), 1.5))
    arrow = QPolygonF([
        QPointF(4, 4), QPointF(4, 24),
        QPointF(10, 18), QPointF(15, 27),
        QPointF(18, 25), QPointF(13, 16),
        QPointF(20, 16)
    ])
    p.drawPolygon(arrow)
    p.end()
    return QIcon(pix)

# =====================================================================
#        БЕЗОПАСНЫЙ ЗАХВАТ КУРСОРА WINDOWS (БЕЗ OVERFLOW И ШУМА)
# =====================================================================
def extract_cursor_pixmap(hCursor, scale=1.0):
    if not hCursor or sys.platform != "win32":
        return None, QPointF(0, 0)

    hbmMask = None
    hbmColor = None

    try:
        ii = ICONINFO()
        if not user32.GetIconInfo(hCursor, ctypes.byref(ii)):
            return None, QPointF(0, 0)

        hbmMask = ii.hbmMask
        hbmColor = ii.hbmColor
        hx = float(ii.xHotspot)
        hy = float(ii.yHotspot)

        hdc = user32.GetDC(None)
        if not hdc:
            return None, QPointF(hx, hy)

        try:
            if hbmColor:
                bm = BITMAP()
                if gdi32.GetObjectW(hbmColor, ctypes.sizeof(bm), ctypes.byref(bm)) == 0:
                    return None, QPointF(hx, hy)

                w, h = bm.bmWidth, bm.bmHeight
                if w <= 0 or h <= 0 or w > 256 or h > 256:
                    return None, QPointF(hx, hy)

                bmi = BITMAPINFO()
                bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
                bmi.bmiHeader.biWidth = w
                bmi.bmiHeader.biHeight = -h
                bmi.bmiHeader.biPlanes = 1
                bmi.bmiHeader.biBitCount = 32
                bmi.bmiHeader.biCompression = 0

                buf = (ctypes.c_uint8 * (w * h * 4))()
                gdi32.GetDIBits(hdc, hbmColor, 0, h, ctypes.byref(buf), ctypes.byref(bmi), 0)

                raw_bytes = bytearray(buf)
                has_alpha = any(raw_bytes[i] > 0 for i in range(3, len(raw_bytes), 4))

                if not has_alpha and hbmMask:
                    mask_buf = (ctypes.c_uint8 * (w * h * 4))()
                    gdi32.GetDIBits(hdc, hbmMask, 0, h, ctypes.byref(mask_buf), ctypes.byref(bmi), 0)
                    for i in range(0, len(raw_bytes), 4):
                        raw_bytes[i + 3] = 0 if mask_buf[i] > 128 else 255
                elif not has_alpha:
                    for i in range(0, len(raw_bytes), 4):
                        if raw_bytes[i] or raw_bytes[i+1] or raw_bytes[i+2]:
                            raw_bytes[i + 3] = 255

                img = QImage(bytes(raw_bytes), w, h, w * 4, QImage.Format.Format_ARGB32_Premultiplied).copy()

            elif hbmMask:
                bm = BITMAP()
                if gdi32.GetObjectW(hbmMask, ctypes.sizeof(bm), ctypes.byref(bm)) == 0:
                    return None, QPointF(hx, hy)

                w = bm.bmWidth
                total_h = bm.bmHeight
                h = total_h // 2
                if w <= 0 or h <= 0 or w > 256 or h > 256:
                    return None, QPointF(hx, hy)

                bmi = BITMAPINFO()
                bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
                bmi.bmiHeader.biWidth = w
                bmi.bmiHeader.biHeight = -total_h
                bmi.bmiHeader.biPlanes = 1
                bmi.bmiHeader.biBitCount = 32
                bmi.bmiHeader.biCompression = 0

                mask_buf = (ctypes.c_uint8 * (w * total_h * 4))()
                gdi32.GetDIBits(hdc, hbmMask, 0, total_h, ctypes.byref(mask_buf), ctypes.byref(bmi), 0)

                out_bytes = bytearray(w * h * 4)
                for y in range(h):
                    for x in range(w):
                        and_idx = (y * w + x) * 4
                        xor_idx = ((y + h) * w + x) * 4
                        out_idx = (y * w + x) * 4

                        and_bit = 1 if mask_buf[and_idx] > 128 else 0
                        xor_bit = 1 if mask_buf[xor_idx] > 128 else 0

                        if and_bit == 0 and xor_bit == 0:
                            out_bytes[out_idx] = 0
                            out_bytes[out_idx + 1] = 0
                            out_bytes[out_idx + 2] = 0
                            out_bytes[out_idx + 3] = 255
                        elif and_bit == 0 and xor_bit == 1:
                            out_bytes[out_idx] = 255
                            out_bytes[out_idx + 1] = 255
                            out_bytes[out_idx + 2] = 255
                            out_bytes[out_idx + 3] = 255
                        elif and_bit == 1 and xor_bit == 0:
                            out_bytes[out_idx] = 0
                            out_bytes[out_idx + 1] = 0
                            out_bytes[out_idx + 2] = 0
                            out_bytes[out_idx + 3] = 0
                        else:
                            out_bytes[out_idx] = 240
                            out_bytes[out_idx + 1] = 240
                            out_bytes[out_idx + 2] = 240
                            out_bytes[out_idx + 3] = 255

                img = QImage(bytes(out_bytes), w, h, w * 4, QImage.Format.Format_ARGB32_Premultiplied).copy()
            else:
                return None, QPointF(hx, hy)

            pix = QPixmap.fromImage(img)
            if abs(scale - 1.0) > 0.05:
                nw = max(1, int(pix.width() * scale))
                nh = max(1, int(pix.height() * scale))
                pix = pix.scaled(nw, nh, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                hx *= scale
                hy *= scale

            return pix, QPointF(hx, hy)

        finally:
            user32.ReleaseDC(None, hdc)

    except Exception:
        return None, QPointF(0, 0)
    finally:
        if hbmMask:
            try:
                gdi32.DeleteObject(hbmMask)
            except Exception:
                pass
        if hbmColor:
            try:
                gdi32.DeleteObject(hbmColor)
            except Exception:
                pass

# =====================================================================
#             СИСТЕМНЫЕ ФУНКЦИИ ПРОВЕРКИ И КАРЕТКИ
# =====================================================================
def load_user_cursor_pixmap(path, scale=1.0, hotspot_mode="TopLeft"):
    if not path or not os.path.isfile(path):
        return None, QPointF(0, 0)
    try:
        pix = QPixmap(path)
        if pix.isNull():
            return None, QPointF(0, 0)
        if abs(scale - 1.0) > 0.05:
            nw = max(1, int(pix.width() * scale))
            nh = max(1, int(pix.height() * scale))
            pix = pix.scaled(nw, nh, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if hotspot_mode == "Center":
            hs = QPointF(pix.width() / 2.0, pix.height() / 2.0)
        else:
            hs = QPointF(0.0, 0.0)
        return pix, hs
    except Exception:
        return None, QPointF(0, 0)

DESKTOP_APP_CLASSES = {
    "Chrome_WidgetWin_1", "Notepad", "Notepad++", "WordPadClass", "OpusApp",
    "XLMAIN", "CabinetWClass", "ExploreWClass", "ConsoleWindowClass",
    "CASCADIA_HOSTING_WINDOW_CLASS", "ApplicationFrameWindow", "MozillaWindowClass"
}

def is_foreground_game_or_fullscreen():
    if sys.platform != "win32":
        return False
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd or hwnd == user32.GetDesktopWindow() or hwnd == user32.GetShellWindow():
            return False

        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        cls_name = buf.value

        if cls_name in DESKTOP_APP_CLASSES or cls_name.startswith("Qt5") or cls_name.startswith("Qt6"):
            return False

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        scr_w = user32.GetSystemMetrics(0)
        scr_h = user32.GetSystemMetrics(1)

        is_full = (rect.left <= 0 and rect.top <= 0 and
                   rect.right >= scr_w and rect.bottom >= scr_h)

        if is_full:
            style = GetWindowLong(hwnd, -16)
            WS_CAPTION = 0x00C00000
            if not (style & WS_CAPTION):
                return True
    except Exception:
        pass
    return False

def get_active_caret_info():
    if sys.platform != "win32":
        return None

    try:
        gui = GUITHREADINFO()
        gui.cbSize = ctypes.sizeof(GUITHREADINFO)

        if user32.GetGUIThreadInfo(0, ctypes.byref(gui)):
            if gui.hwndCaret:
                rc = gui.rcCaret
                pt = POINT(rc.left, rc.top)
                user32.ClientToScreen(gui.hwndCaret, ctypes.byref(pt))
                w = min(5, max(2, rc.right - rc.left))
                h = max(14, min(90, rc.bottom - rc.top))
                if pt.x > -5000 and pt.y > -5000:
                    return pt.x, pt.y, w, h

            target_hwnd = gui.hwndFocus or user32.GetForegroundWindow()
            if target_hwnd:
                p_acc = ctypes.c_void_p()
                hr = oleacc.AccessibleObjectFromWindow(
                    target_hwnd,
                    ctypes.c_uint32(OBJID_CARET),
                    ctypes.byref(IID_IAccessible),
                    ctypes.byref(p_acc)
                )
                if hr == 0 and p_acc.value:
                    try:
                        vtbl = ctypes.cast(p_acc, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
                        acc_loc = ACC_LOC_PROTO(vtbl[22])

                        left = ctypes.c_long(0)
                        top = ctypes.c_long(0)
                        width = ctypes.c_long(0)
                        height = ctypes.c_long(0)

                        var = VARIANT()
                        var.vt = VT_I4
                        var.lVal = CHILDID_SELF

                        res = acc_loc(
                            p_acc,
                            ctypes.byref(left), ctypes.byref(top),
                            ctypes.byref(width), ctypes.byref(height),
                            var
                        )
                        if res == 0 and (width.value > 0 or height.value > 0):
                            w_real = min(5, max(2, width.value))
                            h_real = max(14, min(90, height.value))
                            if left.value > -5000 and top.value > -5000:
                                return left.value, top.value, w_real, h_real
                    finally:
                        try:
                            vtbl = ctypes.cast(p_acc, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
                            rel_func = RELEASE_PROTO(vtbl[2])
                            rel_func(p_acc)
                        except Exception:
                            pass
    except Exception:
        pass
    return None

def generate_catmull_rom_spline(pts, step_px=1.5, max_pts=40):
    n = len(pts)
    if n < 2:
        return []
    if n == 2:
        p0, p1 = pts[0], pts[1]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        dist = (dx * dx + dy * dy) ** 0.5
        steps = min(max_pts, max(1, int(dist / step_px)))
        res = []
        inv_steps = 1.0 / steps
        for s in range(steps):
            u = s * inv_steps
            res.append((p0[0] + u * dx, p0[1] + u * dy, p0[2] + u * (p1[2] - p0[2])))
        res.append(p1)
        return res

    total_dist = 0
    for i in range(n - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        total_dist += (dx * dx + dy * dy) ** 0.5

    step_px = max(step_px, total_dist / max(1, max_pts))
    res = []

    for i in range(n - 1):
        p1 = pts[i]
        p2 = pts[i + 1]
        p0 = pts[i - 1] if i > 0 else (2 * p1[0] - p2[0], 2 * p1[1] - p2[1], 2 * p1[2] - p2[2])
        p3 = pts[i + 2] if i + 2 < n else (2 * p2[0] - p1[0], 2 * p2[1] - p1[1], 2 * p2[2] - p1[2])

        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        dist = (dx * dx + dy * dy) ** 0.5
        steps = max(1, int(dist / step_px))
        inv_steps = 1.0 / steps

        ax = -p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]
        bx = 2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]
        cx = -p0[0] + p2[0]
        dx_c = 2 * p1[0]

        ay = -p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]
        by = 2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]
        cy = -p0[1] + p2[1]
        dy_c = 2 * p1[1]

        t_diff = p2[2] - p1[2]

        for s in range(steps):
            u = s * inv_steps
            u2 = u * u
            u3 = u2 * u
            x = 0.5 * (ax * u3 + bx * u2 + cx * u + dx_c)
            y = 0.5 * (ay * u3 + by * u2 + cy * u + dy_c)
            t = p1[2] + u * t_diff
            res.append((x, y, t))

    res.append(pts[-1])
    return res

# =====================================================================
#                         ХОЛСТЫ РЕНДЕРА
# =====================================================================
class CPUCanvas(QWidget):
    def __init__(self, overlay):
        super().__init__(overlay)
        self.overlay = overlay
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

    def paintEvent(self, event):
        self.overlay.render_scene(self, event.rect())

if HAS_OPENGL:
    class GPUCanvas(QOpenGLWidget):
        def __init__(self, overlay):
            super().__init__(overlay)
            self.overlay = overlay
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)

        def paintGL(self):
            self.overlay.render_scene(self, self.rect())
else:
    GPUCanvas = CPUCanvas

# =====================================================================
#             ПРОЗРАЧНЫЙ ОВЕРЛЕЙ (КУРСОР + КАРЕТКА)
# =====================================================================
class GlitchBlock:
    __slots__ = ('x', 'y', 'w', 'h', 'fill_rgb', 'border_rgb', 'life', 'max_life')
    def __init__(self, x, y, w, h, fill_rgb, border_rgb, life):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.fill_rgb = fill_rgb
        self.border_rgb = border_rgb
        self.life = life
        self.max_life = life

class SparkParticle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'size', 'color')
    def __init__(self, x, y, vx, vy, life, size, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color

class TrueMotionBlurOverlay(QWidget):
    def __init__(self):
        super().__init__()

        # Без Qt.WindowType.Tool, чтобы Windows DWM не прятал окно под играми!
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(geo)

        self.history = deque(maxlen=25)
        self.last_pos = None
        self.last_move_time = time.time()
        self.has_active_draw = False
        self.prev_dirty_rect = QRect()

        self.load_multiplier = 1.0
        self.last_tick_perf = time.perf_counter()
        self.current_frame_ms = 0.0
        self.estimated_cpu_percent = 0.0

        self.last_hcursor = None
        self.cursor_pixmap = None
        self.hotspot_offset = QPointF(0, 0)
        self.default_cursor_pixmap = None
        self.default_hotspot = QPointF(0, 0)

        # Кастомный спрайт из файла
        self.user_cursor_pixmap = None
        self.user_cursor_hotspot = QPointF(0, 0)

        self.update_default_cursor_sprite()
        self.reload_user_cursor()

        # Состояние каретки (FlowText)
        self.caret_active = False
        self.last_caret_seen_time = 0.0
        self.cur_cx = 0.0
        self.cur_cy = 0.0
        self.cur_ch = 18.0

        self.tgt_cx = 0.0
        self.tgt_cy = 0.0
        self.tgt_ch = 18.0

        self.caret_vel_x = 0.0
        self.last_caret_move_time = time.time()
        self.particles = []
        self.glitch_blocks = []
        self.last_topmost_check = 0.0

        # Холст
        self.cpu_canvas = CPUCanvas(self)
        self.cpu_canvas.setGeometry(self.rect())
        self.gpu_canvas = None
        self.active_canvas = self.cpu_canvas

        if CONFIG["RENDER_BACKEND"] == "GPU" and HAS_OPENGL:
            self.switch_backend("GPU")

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_inputs)
        self.poll_timer.start(5)

        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.render_tick)
        self.apply_fps(CONFIG["TARGET_FPS"])

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_win32_overlay_styles()

    def apply_win32_overlay_styles(self):
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                WS_EX_TOPMOST = 0x00000008
                WS_EX_TRANSPARENT = 0x00000020
                WS_EX_LAYERED = 0x00080000
                WS_EX_NOACTIVATE = 0x08000000
                cur_ex = GetWindowLong(hwnd, -20)
                SetWindowLong(hwnd, -20, cur_ex | WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_NOACTIVATE)

                # SWP_FRAMECHANGED заставляет Windows зафиксировать новые стили
                user32.SetWindowPos(
                    ctypes.c_void_p(hwnd),
                    ctypes.c_void_p(-1),
                    0, 0, 0, 0,
                    0x0001 | 0x0002 | 0x0010 | 0x0020 | 0x0040
                )
                user32.BringWindowToTop(ctypes.c_void_p(hwnd))
            except Exception:
                pass

    def reload_user_cursor(self):
        pix, hs = load_user_cursor_pixmap(
            CONFIG.get("CUSTOM_CURSOR_PATH", ""),
            CONFIG.get("CURSOR_SCALE", 1.0),
            CONFIG.get("HOTSPOT_MODE", "TopLeft")
        )
        self.user_cursor_pixmap = pix
        self.user_cursor_hotspot = hs
        if CONFIG.get("CURSOR_MODE") == "Custom File" and pix:
            self.cursor_pixmap = pix
            self.hotspot_offset = hs

    def switch_backend(self, backend_name):
        CONFIG["RENDER_BACKEND"] = backend_name
        if backend_name == "GPU" and HAS_OPENGL:
            if self.gpu_canvas is None:
                self.gpu_canvas = GPUCanvas(self)
                self.gpu_canvas.setGeometry(self.rect())
            self.cpu_canvas.hide()
            self.gpu_canvas.show()
            self.active_canvas = self.gpu_canvas
        else:
            if self.gpu_canvas:
                self.gpu_canvas.hide()
            self.cpu_canvas.show()
            self.active_canvas = self.cpu_canvas
        self.active_canvas.update()

    def apply_fps(self, fps):
        CONFIG["TARGET_FPS"] = fps
        interval = max(1, int(1000 / fps))
        self.render_timer.setInterval(interval)
        if not self.render_timer.isActive():
            self.render_timer.start()

    def update_default_cursor_sprite(self):
        s = CONFIG["CURSOR_SCALE"]
        size = int(32 * s) + 8
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)

        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        ox, oy = 2.0, 2.0
        arrow = QPolygonF([
            QPointF(ox + 0.0 * s, oy + 0.0 * s),
            QPointF(ox + 0.0 * s, oy + 16.5 * s),
            QPointF(ox + 4.5 * s, oy + 12.5 * s),
            QPointF(ox + 7.5 * s, oy + 19.5 * s),
            QPointF(ox + 10.0 * s, oy + 18.5 * s),
            QPointF(ox + 7.0 * s, oy + 11.5 * s),
            QPointF(ox + 12.0 * s, oy + 11.5 * s)
        ])

        r_c, g_c, b_c = CONFIG["CURSOR_COLOR"]
        r_o, g_o, b_o = CONFIG["OUTLINE_COLOR"]
        outline_w = CONFIG["OUTLINE_WIDTH"]
        outline_alpha = int(255 * (CONFIG["OUTLINE_OPACITY"] / 100.0))

        if outline_w > 0.05 and outline_alpha > 0:
            pen = QPen(QColor(r_o, g_o, b_o, outline_alpha), outline_w * s)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            p.setPen(pen)
        else:
            p.setPen(Qt.PenStyle.NoPen)

        p.setBrush(QColor(r_c, g_c, b_c))
        p.drawPolygon(arrow)
        p.end()

        self.default_cursor_pixmap = pix
        self.default_hotspot = QPointF(ox, oy)
        if CONFIG.get("CURSOR_MODE") == "Vector" or not self.cursor_pixmap:
            self.cursor_pixmap = pix
            self.hotspot_offset = self.default_hotspot

    def poll_inputs(self):
        try:
            now = time.time()
            in_game = is_foreground_game_or_fullscreen()

            # 1. FlowCursor
            if CONFIG["ENABLED"]:
                is_visible = True
                hCursor = None

                if sys.platform == "win32":
                    ci = CURSORINFO()
                    ci.cbSize = ctypes.sizeof(CURSORINFO)
                    if user32.GetCursorInfo(ctypes.byref(ci)):
                        is_visible = bool(ci.flags & 1) and bool(ci.hCursor)
                        hCursor = ci.hCursor

                # Скрываем только если явно включено "Скрывать в играх" и выключен "Показ в играх"
                should_hide = CONFIG["HIDE_IN_GAMES"] and not CONFIG["SHOW_IN_GAMES"] and in_game

                if should_hide:
                    if self.history or self.has_active_draw:
                        self.history.clear()
                        self.has_active_draw = False
                        self.update_dirty_region(force_clear=True)
                    self.last_pos = None
                else:
                    # Если включен показ в играх, трекаем ВСЕГДА! Даже если игра вызвала ShowCursor(FALSE)
                    can_track = is_visible or CONFIG.get("SHOW_IN_GAMES", True)
                    if can_track:
                        mode = CONFIG.get("CURSOR_MODE", "System")
                        if mode == "Custom File" and self.user_cursor_pixmap:
                            self.cursor_pixmap = self.user_cursor_pixmap
                            self.hotspot_offset = self.user_cursor_hotspot
                        elif mode == "System":
                            if is_visible and hCursor:
                                if hCursor != self.last_hcursor:
                                    pix, hs = extract_cursor_pixmap(hCursor, CONFIG["CURSOR_SCALE"])
                                    if pix and not pix.isNull():
                                        self.cursor_pixmap = pix
                                        self.hotspot_offset = hs
                                        self.last_hcursor = hCursor
                                    else:
                                        self.cursor_pixmap = self.default_cursor_pixmap
                                        self.hotspot_offset = self.default_hotspot
                            else:
                                # В играх со скрытым курсором используем дефолтный спрайт
                                self.cursor_pixmap = self.default_cursor_pixmap
                                self.hotspot_offset = self.default_hotspot
                        else:  # Vector
                            self.cursor_pixmap = self.default_cursor_pixmap
                            self.hotspot_offset = self.default_hotspot

                        pos = self.mapFromGlobal(QCursor.pos())
                        if self.last_pos is not None:
                            dx = pos.x() - self.last_pos.x()
                            dy = pos.y() - self.last_pos.y()
                            dist_sq = dx * dx + dy * dy
                            min_sq = max(CONFIG["DEADZONE_PX"], CONFIG["MIN_SPEED"]) ** 2
                            if dist_sq >= min_sq:
                                self.history.append((pos.x(), pos.y(), now))
                                self.last_move_time = now
                        else:
                            self.history.append((pos.x(), pos.y(), now))
                            self.last_move_time = now

                        self.last_pos = pos

                        duration = CONFIG["BLUR_DURATION"]
                        while self.history and (now - self.history[0][2] > duration):
                            self.history.popleft()

                        if now - self.last_move_time > duration * 1.1:
                            if self.history:
                                self.history.clear()

            # 2. FlowText
            ft_game_sleep = CONFIG["FT_HIDE_IN_GAMES"] and in_game
            if CONFIG["FT_ENABLED"] and not ft_game_sleep:
                caret_info = get_active_caret_info()
                if caret_info:
                    self.last_caret_seen_time = now
                    cx, cy, cw, ch = caret_info
                    local_pt = self.mapFromGlobal(QPointF(cx, cy))
                    target_x = local_pt.x()
                    target_y = local_pt.y()

                    if not self.caret_active:
                        self.cur_cx = target_x
                        self.cur_cy = target_y
                        self.cur_ch = ch
                        self.tgt_cx = target_x
                        self.tgt_cy = target_y
                        self.tgt_ch = ch
                        self.caret_active = True

                    dx = target_x - self.tgt_cx
                    dy = target_y - self.tgt_cy
                    dist_sq = dx * dx + dy * dy

                    if dist_sq > 0.16:
                        dist = dist_sq ** 0.5
                        self.caret_vel_x = dx
                        self.last_caret_move_time = now

                        # Sparkler Particles generator
                        if CONFIG.get("FT_EFFECT") == "Sparkler Particles":
                            spawn_count = min(5, max(2, int(dist * 0.22)))
                            for _ in range(spawn_count):
                                spd = random.uniform(0.6, 2.4)
                                pvx = -math.copysign(spd, dx) + random.uniform(-0.7, 0.7)
                                pvy = random.uniform(-1.4, 0.7)
                                py = target_y + random.uniform(2, max(4, ch - 2))
                                self.particles.append(
                                    SparkParticle(target_x, py, pvx, pvy, 1.0, random.uniform(1.8, 3.8), CONFIG["FT_COLOR"])
                                )

                        # Cyberpunk Glitch generator (компактные микро-прямоугольники около букв по образцу)
                        elif CONFIG.get("FT_EFFECT") == "Cyberpunk Glitch":
                            CYBER_PALETTE = [
                                ((0, 168, 255), (0, 220, 255)),   # Blue/Cyan
                                ((235, 215, 20), (255, 240, 50)), # Yellow
                                ((170, 30, 45), (230, 50, 70)),   # Red/Crimson
                                ((35, 175, 75), (50, 225, 100)),  # Green
                                ((155, 60, 200), (200, 90, 255))  # Magenta/Purple
                            ]
                            g_count = random.randint(2, 3)
                            for _ in range(g_count):
                                fill_c, border_c = random.choice(CYBER_PALETTE)
                                is_vertical = random.random() < 0.35
                                if is_vertical:
                                    gw = random.uniform(5.0, 9.0)
                                    gh = random.uniform(ch * 0.75, ch * 1.2)
                                    gx = target_x + random.uniform(-8.0, 3.0)
                                    gy = target_y + random.uniform(-3.0, 3.0)
                                else:
                                    gw = random.uniform(14.0, 30.0)
                                    gh = random.uniform(max(5.0, ch * 0.35), min(12.0, ch * 0.65))
                                    gx = target_x + random.uniform(-16.0, 6.0)
                                    gy = target_y + random.uniform(-2.0, ch * 0.5)
                                life = random.uniform(0.10, 0.17)
                                self.glitch_blocks.append(
                                    GlitchBlock(gx, gy, gw, gh, fill_c, border_c, life)
                                )

                        is_multi_line_jump = abs(dy) > 40 and dist > 200
                        is_screen_jump = dist > 750

                        if is_multi_line_jump or is_screen_jump:
                            self.cur_cx = target_x
                            self.cur_cy = target_y
                            self.cur_ch = ch

                    self.tgt_cx = target_x
                    self.tgt_cy = target_y
                    self.tgt_ch = ch
                else:
                    if now - self.last_caret_seen_time > 0.25:
                        self.caret_active = False
            else:
                self.caret_active = False
        except Exception:
            pass

    def update_dirty_region(self, force_clear=False):
        if force_clear:
            if not self.prev_dirty_rect.isEmpty():
                self.active_canvas.update(self.prev_dirty_rect)
                self.prev_dirty_rect = QRect()
            return

        cursor_rect = QRect()
        if len(self.history) >= 2:
            xs = [p[0] for p in self.history]
            ys = [p[1] for p in self.history]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            pad = int(64 * CONFIG["CURSOR_SCALE"]) + 32
            cursor_rect = QRect(
                int(min_x - pad), int(min_y - pad),
                int(max_x - min_x + pad * 2), int(max_y - min_y + pad * 2)
            )

        caret_rect = QRect()
        if self.caret_active or bool(self.particles) or bool(self.glitch_blocks):
            glow = CONFIG["FT_GLOW_RADIUS"] + 35
            min_x = min(self.cur_cx, self.tgt_cx) - glow - 35
            min_y = min(self.cur_cy, self.tgt_cy) - glow
            w_span = abs(self.tgt_cx - self.cur_cx) + glow * 2 + 70
            h_span = max(self.cur_ch, self.tgt_ch) + glow * 2 + abs(self.tgt_cy - self.cur_cy)

            if self.particles:
                pxs = [p.x for p in self.particles]
                pys = [p.y for p in self.particles]
                min_x = min(min_x, min(pxs) - 6)
                min_y = min(min_y, min(pys) - 6)
                w_span = max(w_span, max(pxs) + 6 - min_x)
                h_span = max(h_span, max(pys) + 6 - min_y)

            if self.glitch_blocks:
                g_min_x = min(b.x for b in self.glitch_blocks) - 6
                g_max_x = max(b.x + b.w for b in self.glitch_blocks) + 6
                g_min_y = min(b.y for b in self.glitch_blocks) - 6
                g_max_y = max(b.y + b.h for b in self.glitch_blocks) + 6
                min_x = min(min_x, g_min_x)
                min_y = min(min_y, g_min_y)
                w_span = max(w_span, g_max_x - min_x)
                h_span = max(h_span, g_max_y - min_y)

            caret_rect = QRect(int(min_x), int(min_y), int(w_span), int(h_span))

        curr_rect = cursor_rect.united(caret_rect)

        if not curr_rect.isEmpty():
            if CONFIG["DIRTY_RECT_OPT"] and CONFIG["RENDER_BACKEND"] == "CPU":
                update_rect = curr_rect.united(self.prev_dirty_rect)
                self.prev_dirty_rect = curr_rect
                self.active_canvas.update(update_rect)
            else:
                self.active_canvas.update()
            self.has_active_draw = True
        elif self.has_active_draw:
            self.has_active_draw = False
            if CONFIG["DIRTY_RECT_OPT"] and not self.prev_dirty_rect.isEmpty():
                self.active_canvas.update(self.prev_dirty_rect)
                self.prev_dirty_rect = QRect()
            else:
                self.active_canvas.update()

    def render_tick(self):
        now_perf = time.perf_counter()
        dt = min(0.04, max(0.001, now_perf - self.last_tick_perf))
        dt_ms = dt * 1000.0
        self.last_tick_perf = now_perf

        # Быстрый Watchdog (каждые 150 мс): удерживает оверлей поверх игр (Geometry Dash и др.)
        if sys.platform == "win32" and CONFIG.get("SHOW_IN_GAMES", True):
            if now_perf - self.last_topmost_check > 0.15:
                self.last_topmost_check = now_perf
                try:
                    hwnd = int(self.winId())
                    user32.SetWindowPos(
                        ctypes.c_void_p(hwnd),
                        ctypes.c_void_p(-1),
                        0, 0, 0, 0,
                        0x0001 | 0x0002 | 0x0010
                    )
                    user32.BringWindowToTop(ctypes.c_void_p(hwnd))

                    current_geo = QApplication.primaryScreen().virtualGeometry()
                    if self.geometry() != current_geo:
                        self.setGeometry(current_geo)
                        self.cpu_canvas.setGeometry(self.rect())
                        if self.gpu_canvas:
                            self.gpu_canvas.setGeometry(self.rect())
                except Exception:
                    pass

        target_interval_ms = 1000.0 / CONFIG["TARGET_FPS"]

        if CONFIG["AUTO_LOAD_SCALING"]:
            if dt_ms > target_interval_ms * 1.3:
                self.load_multiplier = max(0.35, self.load_multiplier - 0.08)
            else:
                self.load_multiplier = min(1.0, self.load_multiplier + 0.03)
        else:
            self.load_multiplier = 1.0

        if self.particles:
            decay = dt * 2.4
            for p in self.particles:
                p.x += p.vx
                p.y += p.vy
                p.vy += 0.06
                p.life -= decay
            self.particles = [p for p in self.particles if p.life > 0]

        if self.glitch_blocks:
            for b in self.glitch_blocks:
                b.life -= dt
                if b.life > 0 and random.random() < 0.2:
                    b.x += random.choice([-1.0, 1.0])
            self.glitch_blocks = [b for b in self.glitch_blocks if b.life > 0]

        if self.caret_active:
            effect = CONFIG.get("FT_EFFECT", "Fluid Elastic")
            dx = self.tgt_cx - self.cur_cx
            dy = self.tgt_cy - self.cur_cy
            dist = (dx * dx + dy * dy) ** 0.5

            base_speed = CONFIG["FT_SMOOTH_SPEED"]
            if effect == "Snappy Glide":
                speed = min(0.96, base_speed * 1.8 + 0.38)
            elif effect == "Cyberpunk Glitch":
                speed = min(0.92, base_speed * 1.4 + 0.28)
            else:
                speed = min(0.85, base_speed + (dist / 1200.0))

            self.cur_cx += dx * speed
            self.cur_cy += dy * speed
            self.cur_ch += (self.tgt_ch - self.cur_ch) * speed

            self.caret_vel_x *= 0.70

        if len(self.history) > 0 or self.caret_active or bool(self.particles) or bool(self.glitch_blocks) or self.has_active_draw:
            self.update_dirty_region()

    def render_scene(self, target_widget, clip_rect):
        t_start = time.perf_counter()

        painter = QPainter(target_widget)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(clip_rect, Qt.GlobalColor.transparent)

        # 1. РЕНДЕР КУРСОРА
        if CONFIG["ENABLED"] and len(self.history) >= 2 and self.cursor_pixmap:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

            now = time.time()
            duration = CONFIG["BLUR_DURATION"]
            max_alpha = CONFIG["BLUR_INTENSITY"] / 100.0
            gamma = CONFIG["FALLOFF_EXP"]
            hotspot = self.hotspot_offset
            pixmap = self.cursor_pixmap

            effective_max_copies = int(CONFIG["MAX_COPIES"] * self.load_multiplier)

            curve_pts = generate_catmull_rom_spline(
                list(self.history),
                step_px=CONFIG["STEP_PIXELS"],
                max_pts=effective_max_copies
            )

            inv_duration = 1.0 / duration
            for pt in curve_pts:
                x, y, t = pt
                age = now - t
                t_factor = 1.0 - (age * inv_duration)
                if t_factor <= 0.0:
                    continue
                t_factor = min(1.0, max(0.0, t_factor))

                opacity = max_alpha * (t_factor ** gamma)
                if opacity < 0.015:
                    continue

                painter.setOpacity(opacity)
                painter.drawPixmap(QPointF(x - hotspot.x(), y - hotspot.y()), pixmap)

        # 2. РЕНДЕР КАРЕТКИ
        if CONFIG["FT_ENABLED"] and (self.caret_active or bool(self.particles) or bool(self.glitch_blocks)):
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            r, g, b = CONFIG["FT_COLOR"]
            effect = CONFIG.get("FT_EFFECT", "Fluid Elastic")
            now = time.time()

            idle_time = now - self.last_caret_move_time
            base_alpha = 1.0
            if CONFIG["FT_PULSE_IDLE"] and idle_time > 0.2:
                pulse = 0.5 + 0.5 * math.sin(now * 3.8)
                base_alpha = 0.45 + 0.55 * pulse

            dist_x = self.tgt_cx - self.cur_cx
            base_w = CONFIG["FT_WIDTH"]
            draw_h = max(14.0, self.cur_ch)
            draw_y = self.cur_cy

            # Отрисовка искр Sparkler Particles
            if self.particles:
                for p in self.particles:
                    p_alpha = int(255 * (p.life / p.max_life) * 0.9)
                    if p_alpha > 0:
                        pr, pg, pb = p.color
                        p_rad = max(1.0, p.size * (p.life / p.max_life))
                        painter.setBrush(QColor(pr, pg, pb, p_alpha))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawEllipse(QPointF(p.x, p.y), p_rad, p_rad)

            # Отрисовка прямоугольных глитчей Cyberpunk Glitch (компактные микро-блоки по образцу)
            if self.glitch_blocks:
                for gb in self.glitch_blocks:
                    progress = max(0.0, min(1.0, gb.life / gb.max_life))
                    alpha = int(255 * progress * base_alpha)
                    if alpha <= 0:
                        continue
                    fr, fg, fb = gb.fill_rgb
                    br, bg, bb = gb.border_rgb
                    painter.setBrush(QColor(fr, fg, fb, int(alpha * 0.45)))
                    painter.setPen(QPen(QColor(br, bg, bb, alpha), 1.0))
                    painter.drawRect(QRectF(gb.x, gb.y, gb.w, gb.h))

            if self.caret_active:
                if effect == "Fluid Elastic":
                    stretch = max(-7.0, min(7.0, dist_x * 0.22 * CONFIG["FT_ELASTICITY"]))
                    if stretch >= 0:
                        draw_x = self.cur_cx
                        draw_w = base_w + stretch
                    else:
                        draw_x = self.cur_cx + stretch
                        draw_w = base_w - stretch

                    glow_rad = CONFIG["FT_GLOW_RADIUS"]
                    if glow_rad > 0:
                        glow_alpha = int(255 * (CONFIG["FT_GLOW_OPACITY"] / 100.0) * base_alpha * 0.35)
                        glow_rect = QRectF(draw_x - glow_rad, draw_y - glow_rad, draw_w + glow_rad * 2, draw_h + glow_rad * 2)
                        painter.setBrush(QColor(r, g, b, glow_alpha))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawRoundedRect(glow_rect, glow_rad + 2, glow_rad + 2)

                    painter.setBrush(QColor(r, g, b, int(255 * base_alpha)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(QRectF(draw_x, draw_y, draw_w, draw_h), draw_w / 2.0, draw_w / 2.0)

                elif effect == "Cyberpunk Glitch":
                    draw_x = self.cur_cx
                    draw_w = base_w
                    if idle_time < 0.15 and random.random() < 0.35:
                        draw_x += random.choice([-1.0, 1.0])

                    glow_rad = CONFIG["FT_GLOW_RADIUS"]
                    if glow_rad > 0:
                        glow_alpha = int(255 * (CONFIG["FT_GLOW_OPACITY"] / 100.0) * base_alpha * 0.35)
                        painter.setBrush(QColor(r, g, b, glow_alpha))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawRect(QRectF(draw_x - glow_rad, draw_y - glow_rad, draw_w + glow_rad * 2, draw_h + glow_rad * 2))

                    painter.setBrush(QColor(r, g, b, int(255 * base_alpha)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRect(QRectF(draw_x, draw_y, draw_w, draw_h))

                elif effect == "Snappy Glide":
                    draw_x = self.cur_cx
                    draw_w = base_w
                    glow_rad = CONFIG["FT_GLOW_RADIUS"]
                    if glow_rad > 0:
                        glow_alpha = int(255 * (CONFIG["FT_GLOW_OPACITY"] / 100.0) * base_alpha * 0.3)
                        painter.setBrush(QColor(r, g, b, glow_alpha))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawRoundedRect(QRectF(draw_x - glow_rad, draw_y - glow_rad, draw_w + glow_rad * 2, draw_h + glow_rad * 2), glow_rad, glow_rad)

                    painter.setBrush(QColor(r, g, b, int(255 * base_alpha)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(QRectF(draw_x, draw_y, draw_w, draw_h), draw_w / 2.0, draw_w / 2.0)

                else:  # Sparkler Particles (каретка)
                    draw_x = self.cur_cx
                    draw_w = base_w
                    glow_rad = max(4, CONFIG["FT_GLOW_RADIUS"])
                    glow_alpha = int(255 * (CONFIG["FT_GLOW_OPACITY"] / 100.0) * base_alpha * 0.4)
                    painter.setBrush(QColor(r, g, b, glow_alpha))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(QRectF(draw_x - glow_rad, draw_y - glow_rad, draw_w + glow_rad * 2, draw_h + glow_rad * 2), glow_rad, glow_rad)

                    painter.setBrush(QColor(r, g, b, int(255 * base_alpha)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(QRectF(draw_x, draw_y, draw_w, draw_h), draw_w / 2.0, draw_w / 2.0)

        painter.end()

        t_end = time.perf_counter()
        frame_ms = (t_end - t_start) * 1000.0
        self.current_frame_ms = 0.85 * self.current_frame_ms + 0.15 * frame_ms

        frame_interval_ms = 1000.0 / CONFIG["TARGET_FPS"]
        thread_load = (self.current_frame_ms / frame_interval_ms) * 100.0
        self.estimated_cpu_percent = thread_load / NUM_CPU_CORES

class SettingsWindow(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.tray_ref = None

        self.setWindowTitle("Motion Suite — FlowCursor & FlowText")
        self.resize(540, 710)

        self.init_ui()
        self.apply_dark_theme()

        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats_label)
        self.stats_timer.start(300)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        self.master_tabs = QTabWidget()
        main_layout.addWidget(self.master_tabs)

        # ------------------- 1. FLOW CURSOR -------------------
        self.tab_flow_cursor = QWidget()
        vbox_fc = QVBoxLayout(self.tab_flow_cursor)
        vbox_fc.setContentsMargins(4, 8, 4, 4)

        self.sub_tabs_cursor = QTabWidget()
        vbox_fc.addWidget(self.sub_tabs_cursor)

        # Performance
        tab_perf = QWidget()
        vbox_perf = QVBoxLayout(tab_perf)
        grp_backend = QGroupBox("Движок рендера")
        v_backend = QVBoxLayout(grp_backend)
        self.radio_cpu = QRadioButton("CPU (0% нагрузки на GPU — рекомендуется)")
        self.radio_gpu = QRadioButton("GPU (OpenGL)")
        if not HAS_OPENGL:
            self.radio_gpu.setEnabled(False)
            self.radio_gpu.setText("GPU (OpenGL недоступен)")
        self.radio_cpu.toggled.connect(lambda chk: self.overlay.switch_backend("CPU") if chk else None)
        self.radio_gpu.toggled.connect(lambda chk: self.overlay.switch_backend("GPU") if chk else None)
        v_backend.addWidget(self.radio_cpu)
        v_backend.addWidget(self.radio_gpu)
        vbox_perf.addWidget(grp_backend)

        grp_opt = QGroupBox("Оптимизация рендера")
        v_opt = QVBoxLayout(grp_opt)
        self.chk_dirty = QCheckBox("Bounding-Box рендер (устраняет фоновую нагрузку)")
        self.chk_dirty.toggled.connect(self.on_dirty_toggle)
        v_opt.addWidget(self.chk_dirty)
        self.chk_scaling = QCheckBox("Авто-скейлинг копий при нагрузке от игр")
        self.chk_scaling.toggled.connect(self.on_scaling_toggle)
        v_opt.addWidget(self.chk_scaling)
        self.chk_cpu_limit = QCheckBox("Ограничитель CPU Budget")
        self.chk_cpu_limit.toggled.connect(self.on_cpu_limit_toggle)
        v_opt.addWidget(self.chk_cpu_limit)

        self.lbl_budget = QLabel()
        self.slider_budget = QSlider(Qt.Orientation.Horizontal)
        self.slider_budget.setRange(3, 15)
        self.slider_budget.valueChanged.connect(self.on_budget_change)
        v_opt.addWidget(self.lbl_budget)
        v_opt.addWidget(self.slider_budget)
        vbox_perf.addWidget(grp_opt)

        self.lbl_stats = QLabel("Телеметрия: инициализация...")
        self.lbl_stats.setStyleSheet("color: #7ee787; font-weight: bold; font-family: Consolas; font-size: 12px;")
        vbox_perf.addWidget(self.lbl_stats)
        vbox_perf.addStretch()
        self.sub_tabs_cursor.addTab(tab_perf, "⚡ Performance")

        # Setup
        tab_setup = QWidget()
        vbox_setup = QVBoxLayout(tab_setup)
        self.chk_enabled = QCheckBox("Включить размытие курсора")
        self.chk_enabled.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.chk_enabled.toggled.connect(self.on_enabled_toggle)
        vbox_setup.addWidget(self.chk_enabled)

        self.chk_show_in_games = QCheckBox("🎮 Показывать шлейф в играх (Geometry Dash, Osu! и др.)")
        self.chk_show_in_games.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.chk_show_in_games.toggled.connect(self.on_show_in_games_toggle)
        vbox_setup.addWidget(self.chk_show_in_games)

        lbl_gd_hint = QLabel("💡 Важно, игра должна быть в окне ")
        lbl_gd_hint.setStyleSheet("color: #58a6ff; font-size: 11px; margin-left: 20px; font-weight: 500;")
        vbox_setup.addWidget(lbl_gd_hint)

        self.chk_game_hide = QCheckBox("Скрывать шлейф в полноэкранных играх (Экономия ресурсов)")
        self.chk_game_hide.toggled.connect(self.on_hide_in_games_toggle)
        vbox_setup.addWidget(self.chk_game_hide)

        grp_blur = QGroupBox("Параметры шлейфа")
        v_blur = QVBoxLayout(grp_blur)
        self.lbl_duration = QLabel()
        self.slider_duration = QSlider(Qt.Orientation.Horizontal)
        self.slider_duration.setRange(15, 90)
        self.slider_duration.valueChanged.connect(self.on_duration_change)
        v_blur.addWidget(self.lbl_duration)
        v_blur.addWidget(self.slider_duration)

        self.lbl_intensity = QLabel()
        self.slider_intensity = QSlider(Qt.Orientation.Horizontal)
        self.slider_intensity.setRange(20, 100)
        self.slider_intensity.valueChanged.connect(self.on_intensity_change)
        v_blur.addWidget(self.lbl_intensity)
        v_blur.addWidget(self.slider_intensity)

        self.lbl_falloff = QLabel()
        self.slider_falloff = QSlider(Qt.Orientation.Horizontal)
        self.slider_falloff.setRange(10, 35)
        self.slider_falloff.valueChanged.connect(self.on_falloff_change)
        v_blur.addWidget(self.lbl_falloff)
        v_blur.addWidget(self.slider_falloff)

        self.lbl_step = QLabel()
        self.slider_step = QSlider(Qt.Orientation.Horizontal)
        self.slider_step.setRange(8, 28)
        self.slider_step.valueChanged.connect(self.on_step_change)
        v_blur.addWidget(self.lbl_step)
        v_blur.addWidget(self.slider_step)
        vbox_setup.addWidget(grp_blur)
        vbox_setup.addStretch()
        self.sub_tabs_cursor.addTab(tab_setup, "⚙️ Setup")

        # Image
        tab_img = QWidget()
        vbox_img = QVBoxLayout(tab_img)

        grp_src = QGroupBox("Источник курсора")
        v_src = QVBoxLayout(grp_src)

        h_mode = QHBoxLayout()
        h_mode.addWidget(QLabel("Режим курсора:"))
        self.combo_cursor_mode = QComboBox()
        self.combo_cursor_mode.addItems(["Системный (автозахват)", "Векторная стрелка", "Свой файл (PNG / CUR / ICO)"])
        self.combo_cursor_mode.currentTextChanged.connect(self.on_cursor_mode_change)
        h_mode.addWidget(self.combo_cursor_mode)
        v_src.addLayout(h_mode)

        h_file = QHBoxLayout()
        self.btn_choose_cursor = QPushButton("📁 Выбрать файл...")
        self.btn_choose_cursor.clicked.connect(self.choose_cursor_file)
        self.lbl_cursor_filename = QLabel("Файл не выбран")
        self.lbl_cursor_filename.setStyleSheet("color: #8b949e; font-size: 11px;")
        h_file.addWidget(self.btn_choose_cursor)
        h_file.addWidget(self.lbl_cursor_filename)
        v_src.addLayout(h_file)

        h_hs = QHBoxLayout()
        h_hs.addWidget(QLabel("Точка привязки (Hotspot):"))
        self.combo_hotspot = QComboBox()
        self.combo_hotspot.addItems(["Верхний левый угол (0,0)", "Центр (прицел / точка)"])
        self.combo_hotspot.currentTextChanged.connect(self.on_hotspot_change)
        h_hs.addWidget(self.combo_hotspot)
        v_src.addLayout(h_hs)

        vbox_img.addWidget(grp_src)

        grp_look = QGroupBox("Внешний вид стрелки (для векторного режима)")
        v_look = QVBoxLayout(grp_look)
        self.lbl_scale = QLabel()
        self.slider_scale = QSlider(Qt.Orientation.Horizontal)
        self.slider_scale.setRange(6, 22)
        self.slider_scale.valueChanged.connect(self.on_scale_change)
        v_look.addWidget(self.lbl_scale)
        v_look.addWidget(self.slider_scale)

        self.lbl_outline_w = QLabel()
        self.slider_outline_w = QSlider(Qt.Orientation.Horizontal)
        self.slider_outline_w.setRange(0, 15)
        self.slider_outline_w.valueChanged.connect(self.on_outline_w_change)
        v_look.addWidget(self.lbl_outline_w)
        v_look.addWidget(self.slider_outline_w)

        self.lbl_outline_a = QLabel()
        self.slider_outline_a = QSlider(Qt.Orientation.Horizontal)
        self.slider_outline_a.setRange(0, 100)
        self.slider_outline_a.valueChanged.connect(self.on_outline_a_change)
        v_look.addWidget(self.lbl_outline_a)
        v_look.addWidget(self.slider_outline_a)

        h_c1 = QHBoxLayout()
        h_c1.addWidget(QLabel("Цвет заливки:"))
        self.btn_color_fill = QPushButton("Выбрать цвет")
        self.btn_color_fill.clicked.connect(self.choose_fill_color)
        h_c1.addWidget(self.btn_color_fill)
        v_look.addLayout(h_c1)

        h_c2 = QHBoxLayout()
        h_c2.addWidget(QLabel("Цвет обводки:"))
        self.btn_color_outline = QPushButton("Выбрать цвет")
        self.btn_color_outline.clicked.connect(self.choose_outline_color)
        h_c2.addWidget(self.btn_color_outline)
        v_look.addLayout(h_c2)

        vbox_img.addWidget(grp_look)
        vbox_img.addStretch()
        self.sub_tabs_cursor.addTab(tab_img, "🎨 Image")

        # Limits
        tab_limits = QWidget()
        vbox_limits = QVBoxLayout(tab_limits)
        grp_lim = QGroupBox("Ограничения нагрузки")
        v_lim = QVBoxLayout(grp_lim)
        self.lbl_max_copies = QLabel()
        self.slider_max_copies = QSlider(Qt.Orientation.Horizontal)
        self.slider_max_copies.setRange(15, 100)
        self.slider_max_copies.valueChanged.connect(self.on_max_copies_change)
        v_lim.addWidget(self.lbl_max_copies)
        v_lim.addWidget(self.slider_max_copies)

        self.lbl_deadzone = QLabel()
        self.slider_deadzone = QSlider(Qt.Orientation.Horizontal)
        self.slider_deadzone.setRange(5, 50)
        self.slider_deadzone.valueChanged.connect(self.on_deadzone_change)
        v_lim.addWidget(self.lbl_deadzone)
        v_lim.addWidget(self.slider_deadzone)

        self.lbl_min_speed = QLabel()
        self.slider_min_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_min_speed.setRange(5, 40)
        self.slider_min_speed.valueChanged.connect(self.on_min_speed_change)
        v_lim.addWidget(self.lbl_min_speed)
        v_lim.addWidget(self.slider_min_speed)

        h_fps = QHBoxLayout()
        h_fps.addWidget(QLabel("Целевой FPS:"))
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["60", "90", "120", "144", "165", "240", "360"])
        self.combo_fps.currentTextChanged.connect(self.on_fps_change)
        h_fps.addWidget(self.combo_fps)
        v_lim.addLayout(h_fps)

        vbox_limits.addWidget(grp_lim)
        vbox_limits.addStretch()
        self.sub_tabs_cursor.addTab(tab_limits, "🛑 Limits")

        self.master_tabs.addTab(self.tab_flow_cursor, "🖱️ FlowCursor")

        # ------------------- 2. FLOW TEXT -------------------
        self.tab_flow_text = QWidget()
        vbox_ft = QVBoxLayout(self.tab_flow_text)
        vbox_ft.setSpacing(10)
        vbox_ft.setContentsMargins(10, 10, 10, 10)

        self.chk_ft_enabled = QCheckBox("Включить плавный ввод текста (FlowText)")
        self.chk_ft_enabled.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.chk_ft_enabled.toggled.connect(self.on_ft_enabled_toggle)
        vbox_ft.addWidget(self.chk_ft_enabled)

        grp_ft_modes = QGroupBox("Динамика каретки")
        v_ft_modes = QVBoxLayout(grp_ft_modes)

        h_eff = QHBoxLayout()
        h_eff.addWidget(QLabel("Стиль анимации:"))
        self.combo_ft_effect = QComboBox()
        self.combo_ft_effect.addItems([
            "Fluid Elastic",
            "Cyberpunk Glitch",
            "Sparkler Particles",
            "Snappy Glide"
        ])
        self.combo_ft_effect.currentTextChanged.connect(self.on_ft_effect_change)
        h_eff.addWidget(self.combo_ft_effect)
        v_ft_modes.addLayout(h_eff)

        self.lbl_ft_speed = QLabel()
        self.slider_ft_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_ft_speed.setRange(15, 65)
        self.slider_ft_speed.valueChanged.connect(self.on_ft_speed_change)
        v_ft_modes.addWidget(self.lbl_ft_speed)
        v_ft_modes.addWidget(self.slider_ft_speed)

        self.lbl_ft_elastic = QLabel()
        self.slider_ft_elastic = QSlider(Qt.Orientation.Horizontal)
        self.slider_ft_elastic.setRange(5, 30)
        self.slider_ft_elastic.valueChanged.connect(self.on_ft_elastic_change)
        v_ft_modes.addWidget(self.lbl_ft_elastic)
        v_ft_modes.addWidget(self.slider_ft_elastic)

        self.lbl_ft_width = QLabel()
        self.slider_ft_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_ft_width.setRange(15, 50)
        self.slider_ft_width.valueChanged.connect(self.on_ft_width_change)
        v_ft_modes.addWidget(self.lbl_ft_width)
        v_ft_modes.addWidget(self.slider_ft_width)
        vbox_ft.addWidget(grp_ft_modes)

        grp_ft_look = QGroupBox("Свечение и Цвета")
        v_ft_look = QVBoxLayout(grp_ft_look)

        self.lbl_ft_glow_r = QLabel()
        self.slider_ft_glow_r = QSlider(Qt.Orientation.Horizontal)
        self.slider_ft_glow_r.setRange(0, 16)
        self.slider_ft_glow_r.valueChanged.connect(self.on_ft_glow_r_change)
        v_ft_look.addWidget(self.lbl_ft_glow_r)
        v_ft_look.addWidget(self.slider_ft_glow_r)

        self.lbl_ft_glow_o = QLabel()
        self.slider_ft_glow_o = QSlider(Qt.Orientation.Horizontal)
        self.slider_ft_glow_o.setRange(10, 100)
        self.slider_ft_glow_o.valueChanged.connect(self.on_ft_glow_o_change)
        v_ft_look.addWidget(self.lbl_ft_glow_o)
        v_ft_look.addWidget(self.slider_ft_glow_o)

        self.chk_ft_pulse = QCheckBox("Плавное дыхание каретки в покое")
        self.chk_ft_pulse.toggled.connect(self.on_ft_pulse_toggle)
        v_ft_look.addWidget(self.chk_ft_pulse)

        h_c_ft = QHBoxLayout()
        h_c_ft.addWidget(QLabel("Цвет каретки:"))
        self.btn_ft_color = QPushButton("Выбрать цвет")
        self.btn_ft_color.clicked.connect(self.choose_ft_color)
        h_c_ft.addWidget(self.btn_ft_color)
        v_ft_look.addLayout(h_c_ft)
        vbox_ft.addWidget(grp_ft_look)

        grp_ft_shield = QGroupBox("🛡️ Game Shield & Интеграция")
        v_ft_shield = QVBoxLayout(grp_ft_shield)
        self.chk_ft_gameshield = QCheckBox("Аппаратный пропуск инпута в играх (Zero-Lag)")
        self.chk_ft_gameshield.toggled.connect(self.on_ft_gameshield_toggle)
        v_ft_shield.addWidget(self.chk_ft_gameshield)

        self.chk_ft_hide_games = QCheckBox("Сон каретки в полноэкранных 3D играх")
        self.chk_ft_hide_games.toggled.connect(self.on_ft_hide_games_toggle)
        v_ft_shield.addWidget(self.chk_ft_hide_games)

        vbox_ft.addWidget(grp_ft_shield)
        vbox_ft.addStretch()
        self.master_tabs.addTab(self.tab_flow_text, "⌨️ FlowText")

        # ------------------- НИЖНЯЯ ПАНЕЛЬ -------------------
        h_bot = QHBoxLayout()
        self.btn_reset = QPushButton("🔄 Сбросить всё по умолчанию")
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        h_bot.addWidget(self.btn_reset)

        self.btn_hide = QPushButton("Свернуть в трей")
        self.btn_hide.clicked.connect(self.hide)
        h_bot.addWidget(self.btn_hide)
        main_layout.addLayout(h_bot)

        self.sync_ui_from_config()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def update_stats_label(self):
        backend = CONFIG["RENDER_BACKEND"]
        ms = self.overlay.current_frame_ms
        pct = self.overlay.estimated_cpu_percent
        mul = int(self.overlay.load_multiplier * 100)
        gpu_stat = "<0.2%" if (CONFIG["DIRTY_RECT_OPT"] and backend == "CPU") else ("0.0%" if backend == "CPU" else "OpenGL")
        self.lbl_stats.setText(f"GPU: ~{gpu_stat} | CPU: ~{pct:.1f}% ({ms:.2f} мс) | Качество: {mul}%")

    def sync_ui_from_config(self):
        if CONFIG["RENDER_BACKEND"] == "GPU" and HAS_OPENGL:
            self.radio_gpu.setChecked(True)
        else:
            self.radio_cpu.setChecked(True)

        self.chk_dirty.setChecked(CONFIG["DIRTY_RECT_OPT"])
        self.chk_scaling.setChecked(CONFIG["AUTO_LOAD_SCALING"])
        self.chk_cpu_limit.setChecked(CONFIG["CPU_LIMIT_ENABLED"])
        self.slider_budget.setValue(int(CONFIG["CPU_MAX_BUDGET"] * 10))
        self.on_budget_change(self.slider_budget.value())

        self.chk_enabled.setChecked(CONFIG["ENABLED"])
        self.chk_show_in_games.setChecked(CONFIG.get("SHOW_IN_GAMES", True))
        self.chk_game_hide.setChecked(CONFIG.get("HIDE_IN_GAMES", False))

        self.slider_duration.setValue(int(CONFIG["BLUR_DURATION"] * 1000))
        self.on_duration_change(self.slider_duration.value())
        self.slider_intensity.setValue(CONFIG["BLUR_INTENSITY"])
        self.on_intensity_change(self.slider_intensity.value())
        self.slider_falloff.setValue(int(CONFIG["FALLOFF_EXP"] * 10))
        self.on_falloff_change(self.slider_falloff.value())
        self.slider_step.setValue(int(CONFIG["STEP_PIXELS"] * 10))
        self.on_step_change(self.slider_step.value())

        cur_mode = CONFIG.get("CURSOR_MODE", "System")
        if cur_mode == "Custom File":
            self.combo_cursor_mode.setCurrentText("Свой файл (PNG / CUR / ICO)")
        elif cur_mode == "Vector":
            self.combo_cursor_mode.setCurrentText("Векторная стрелка")
        else:
            self.combo_cursor_mode.setCurrentText("Системный (автозахват)")

        fpath = CONFIG.get("CUSTOM_CURSOR_PATH", "")
        self.lbl_cursor_filename.setText(os.path.basename(fpath) if fpath else "Файл не выбран")

        hs_mode = CONFIG.get("HOTSPOT_MODE", "TopLeft")
        if hs_mode == "Center":
            self.combo_hotspot.setCurrentText("Центр (прицел / точка)")
        else:
            self.combo_hotspot.setCurrentText("Верхний левый угол (0,0)")

        self.slider_scale.setValue(int(CONFIG["CURSOR_SCALE"] * 10))
        self.on_scale_change(self.slider_scale.value())
        self.slider_outline_w.setValue(int(CONFIG["OUTLINE_WIDTH"] * 10))
        self.on_outline_w_change(self.slider_outline_w.value())
        self.slider_outline_a.setValue(CONFIG["OUTLINE_OPACITY"])
        self.on_outline_a_change(self.slider_outline_a.value())
        self.update_btn_color_previews()

        self.slider_max_copies.setValue(CONFIG["MAX_COPIES"])
        self.on_max_copies_change(CONFIG["MAX_COPIES"])
        self.slider_deadzone.setValue(int(CONFIG["DEADZONE_PX"] * 10))
        self.on_deadzone_change(self.slider_deadzone.value())
        self.slider_min_speed.setValue(int(CONFIG["MIN_SPEED"] * 10))
        self.on_min_speed_change(self.slider_min_speed.value())
        self.combo_fps.setCurrentText(str(CONFIG["TARGET_FPS"]))

        self.chk_ft_enabled.setChecked(CONFIG["FT_ENABLED"])
        eff = CONFIG.get("FT_EFFECT", "Fluid Elastic")
        valid_effs = ["Fluid Elastic", "Cyberpunk Glitch", "Sparkler Particles", "Snappy Glide"]
        self.combo_ft_effect.setCurrentText(eff if eff in valid_effs else "Fluid Elastic")

        self.slider_ft_speed.setValue(int(CONFIG["FT_SMOOTH_SPEED"] * 100))
        self.on_ft_speed_change(self.slider_ft_speed.value())
        self.slider_ft_elastic.setValue(int(CONFIG["FT_ELASTICITY"] * 10))
        self.on_ft_elastic_change(self.slider_ft_elastic.value())
        self.slider_ft_width.setValue(int(CONFIG["FT_WIDTH"] * 10))
        self.on_ft_width_change(self.slider_ft_width.value())
        self.slider_ft_glow_r.setValue(CONFIG["FT_GLOW_RADIUS"])
        self.on_ft_glow_r_change(CONFIG["FT_GLOW_RADIUS"])
        self.slider_ft_glow_o.setValue(CONFIG["FT_GLOW_OPACITY"])
        self.on_ft_glow_o_change(CONFIG["FT_GLOW_OPACITY"])
        self.chk_ft_pulse.setChecked(CONFIG["FT_PULSE_IDLE"])
        self.chk_ft_gameshield.setChecked(CONFIG["FT_GAME_SHIELD"])
        self.chk_ft_hide_games.setChecked(CONFIG.get("FT_HIDE_IN_GAMES", False))
        self.update_btn_ft_color_preview()

    def reset_to_defaults(self):
        CONFIG.clear()
        CONFIG.update(DEFAULT_CONFIG)
        self.sync_ui_from_config()
        self.overlay.last_hcursor = None
        self.overlay.update_default_cursor_sprite()
        self.overlay.reload_user_cursor()
        self.overlay.switch_backend(CONFIG["RENDER_BACKEND"])
        self.overlay.apply_fps(CONFIG["TARGET_FPS"])
        save_config()

    def on_dirty_toggle(self, v):
        CONFIG["DIRTY_RECT_OPT"] = v
        save_config()

    def on_scaling_toggle(self, v):
        CONFIG["AUTO_LOAD_SCALING"] = v
        save_config()

    def on_cpu_limit_toggle(self, v):
        CONFIG["CPU_LIMIT_ENABLED"] = v
        save_config()

    def on_enabled_toggle(self, v):
        CONFIG["ENABLED"] = v
        save_config()

    def on_show_in_games_toggle(self, checked):
        CONFIG["SHOW_IN_GAMES"] = checked
        if checked:
            CONFIG["HIDE_IN_GAMES"] = False
            self.chk_game_hide.setChecked(False)
        save_config()

    def on_hide_in_games_toggle(self, checked):
        CONFIG["HIDE_IN_GAMES"] = checked
        if checked:
            CONFIG["SHOW_IN_GAMES"] = False
            self.chk_show_in_games.setChecked(False)
        save_config()

    def on_cursor_mode_change(self, text):
        if "Свой файл" in text:
            CONFIG["CURSOR_MODE"] = "Custom File"
        elif "Векторная" in text:
            CONFIG["CURSOR_MODE"] = "Vector"
        else:
            CONFIG["CURSOR_MODE"] = "System"
        self.overlay.last_hcursor = None
        self.overlay.reload_user_cursor()
        self.overlay.update_default_cursor_sprite()
        save_config()

    def choose_cursor_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать файл курсора",
            "",
            "Изображения и курсоры (*.png *.cur *.ico *.bmp);;Все файлы (*.*)"
        )
        if file_path:
            CONFIG["CUSTOM_CURSOR_PATH"] = file_path
            CONFIG["CURSOR_MODE"] = "Custom File"
            self.combo_cursor_mode.setCurrentText("Свой файл (PNG / CUR / ICO)")
            self.lbl_cursor_filename.setText(os.path.basename(file_path))
            self.overlay.reload_user_cursor()
            save_config()

    def on_hotspot_change(self, text):
        if "Центр" in text:
            CONFIG["HOTSPOT_MODE"] = "Center"
        else:
            CONFIG["HOTSPOT_MODE"] = "TopLeft"
        self.overlay.reload_user_cursor()
        save_config()

    def on_budget_change(self, val):
        b = val / 10.0
        CONFIG["CPU_MAX_BUDGET"] = b
        self.lbl_budget.setText(f"Лимит бюджета CPU: {b:.1f}%")
        save_config()

    def on_duration_change(self, val):
        CONFIG["BLUR_DURATION"] = val / 1000.0
        self.lbl_duration.setText(f"Длина выдержки: {val} мс")
        save_config()

    def on_intensity_change(self, val):
        CONFIG["BLUR_INTENSITY"] = val
        self.lbl_intensity.setText(f"Яркость следа: {val}%")
        save_config()

    def on_falloff_change(self, val):
        f = val / 10.0
        CONFIG["FALLOFF_EXP"] = f
        self.lbl_falloff.setText(f"Коэффициент затухания: {f:.1f}")
        save_config()

    def on_step_change(self, val):
        s = val / 10.0
        CONFIG["STEP_PIXELS"] = s
        self.lbl_step.setText(f"Шаг сэмплов: {s:.1f} px")
        save_config()

    def on_scale_change(self, val):
        s = val / 10.0
        CONFIG["CURSOR_SCALE"] = s
        self.lbl_scale.setText(f"Масштаб стрелки: {s:.1f}x")
        self.overlay.last_hcursor = None
        self.overlay.update_default_cursor_sprite()
        self.overlay.reload_user_cursor()
        save_config()

    def on_outline_w_change(self, val):
        w = val / 10.0
        CONFIG["OUTLINE_WIDTH"] = w
        self.lbl_outline_w.setText(f"Толщина обводки: {w:.1f} px")
        self.overlay.update_default_cursor_sprite()
        save_config()

    def on_outline_a_change(self, val):
        CONFIG["OUTLINE_OPACITY"] = val
        self.lbl_outline_a.setText(f"Непрозрачность обводки: {val}%")
        self.overlay.update_default_cursor_sprite()
        save_config()

    def choose_fill_color(self):
        r, g, b = CONFIG["CURSOR_COLOR"]
        color = QColorDialog.getColor(QColor(r, g, b), self, "Цвет заливки стрелки")
        if color.isValid():
            CONFIG["CURSOR_COLOR"] = (color.red(), color.green(), color.blue())
            self.update_btn_color_previews()
            self.overlay.update_default_cursor_sprite()
            save_config()

    def choose_outline_color(self):
        r, g, b = CONFIG["OUTLINE_COLOR"]
        color = QColorDialog.getColor(QColor(r, g, b), self, "Цвет обводки стрелки")
        if color.isValid():
            CONFIG["OUTLINE_COLOR"] = (color.red(), color.green(), color.blue())
            self.update_btn_color_previews()
            self.overlay.update_default_cursor_sprite()
            save_config()

    def update_btn_color_previews(self):
        rc, gc, bc = CONFIG["CURSOR_COLOR"]
        ro, go, bo = CONFIG["OUTLINE_COLOR"]
        self.btn_color_fill.setStyleSheet(f"background-color: rgb({rc},{gc},{bc}); color: {'black' if rc+gc+bc>380 else 'white'};")
        self.btn_color_outline.setStyleSheet(f"background-color: rgb({ro},{go},{bo}); color: {'black' if ro+go+bo>380 else 'white'};")

    def on_max_copies_change(self, val):
        CONFIG["MAX_COPIES"] = val
        self.lbl_max_copies.setText(f"Макс. копий в шлейфе: {val}")
        save_config()

    def on_deadzone_change(self, val):
        d = val / 10.0
        CONFIG["DEADZONE_PX"] = d
        self.lbl_deadzone.setText(f"Мертвая зона движения: {d:.1f} px")
        save_config()

    def on_min_speed_change(self, val):
        s = val / 10.0
        CONFIG["MIN_SPEED"] = s
        self.lbl_min_speed.setText(f"Мин. скорость активации: {s:.1f} px")
        save_config()

    def on_fps_change(self, text):
        if text.isdigit():
            self.overlay.apply_fps(int(text))
            save_config()

    # Handlers FlowText
    def on_ft_enabled_toggle(self, v):
        CONFIG["FT_ENABLED"] = v
        save_config()

    def on_ft_effect_change(self, val):
        CONFIG["FT_EFFECT"] = val
        self.overlay.active_canvas.update()
        save_config()

    def on_ft_speed_change(self, val):
        s = val / 100.0
        CONFIG["FT_SMOOTH_SPEED"] = s
        self.lbl_ft_speed.setText(f"Скорость скольжения: {s:.2f}")
        save_config()

    def on_ft_elastic_change(self, val):
        e = val / 10.0
        CONFIG["FT_ELASTICITY"] = e
        self.lbl_ft_elastic.setText(f"Коэффициент упругости: {e:.1f}")
        save_config()

    def on_ft_width_change(self, val):
        w = val / 10.0
        CONFIG["FT_WIDTH"] = w
        self.lbl_ft_width.setText(f"Толщина каретки: {w:.1f} px")
        save_config()

    def on_ft_glow_r_change(self, val):
        CONFIG["FT_GLOW_RADIUS"] = val
        self.lbl_ft_glow_r.setText(f"Радиус свечения: {val} px")
        save_config()

    def on_ft_glow_o_change(self, val):
        CONFIG["FT_GLOW_OPACITY"] = val
        self.lbl_ft_glow_o.setText(f"Интенсивность свечения: {val}%")
        save_config()

    def on_ft_pulse_toggle(self, v):
        CONFIG["FT_PULSE_IDLE"] = v
        save_config()

    def on_ft_gameshield_toggle(self, v):
        CONFIG["FT_GAME_SHIELD"] = v
        save_config()

    def on_ft_hide_games_toggle(self, v):
        CONFIG["FT_HIDE_IN_GAMES"] = v
        save_config()

    def choose_ft_color(self):
        r, g, b = CONFIG["FT_COLOR"]
        color = QColorDialog.getColor(QColor(r, g, b), self, "Цвет каретки")
        if color.isValid():
            CONFIG["FT_COLOR"] = (color.red(), color.green(), color.blue())
            self.update_btn_ft_color_preview()
            save_config()

    def update_btn_ft_color_preview(self):
        r, g, b = CONFIG["FT_COLOR"]
        self.btn_ft_color.setStyleSheet(f"background-color: rgb({r},{g},{b}); color: {'black' if r+g+b>380 else 'white'};")

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: 'Segoe UI', Tahoma, sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #30363d;
                background-color: #161b22;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #21262d;
                color: #8b949e;
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #161b22;
                color: #58a6ff;
                font-weight: bold;
                border: 1px solid #30363d;
                border-bottom: none;
            }
            QGroupBox {
                border: 1px solid #30363d;
                border-radius: 6px;
                margin-top: 14px;
                padding-top: 10px;
                font-weight: bold;
                color: #58a6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #30363d;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #58a6ff;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #f0f6fc;
                width: 14px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 7px;
            }
            QComboBox {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px 8px;
                color: #c9d1d9;
            }
            QCheckBox, QRadioButton {
                spacing: 8px;
            }
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)

# =====================================================================
#             ТОЧКА ВХОДА И СИСТЕМНЫЙ ТРЕЙ
# =====================================================================
def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    app_icon = get_app_icon()
    app.setWindowIcon(app_icon)

    overlay = TrueMotionBlurOverlay()
    overlay.show()

    settings_window = SettingsWindow(overlay)
    settings_window.setWindowIcon(app_icon)

    tray = QSystemTrayIcon(app_icon, app)
    tray.setToolTip("Motion Suite — FlowCursor & FlowText")
    settings_window.tray_ref = tray

    menu = QMenu()
    act_open = menu.addAction("Настройки")
    act_open.triggered.connect(settings_window.showNormal)
    menu.addSeparator()
    act_quit = menu.addAction("Выход")
    act_quit.triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.activated.connect(lambda r: settings_window.showNormal() if r in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick) else None)
    tray.show()

    settings_window.show()

    if sys.platform == "win32":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
