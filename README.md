# FlowMK

A lightweight Windows desktop overlay that adds smooth motion blur to your mouse cursor and dynamic animations to your text caret.

Built with Python and PyQt6 using native Win32 APIs for low overhead and zero click latency.

---

## Features

### 🖱️ Cursor Motion Blur (FlowCursor)
- **Smooth Spline Trails:** Uses Catmull-Rom spline interpolation so fast cursor flicks don't look like separated dots.
- **Cursor Detection:** Automatically captures current Windows cursors (arrow, hand, text beam, etc.).
- **Custom Cursor Support:** Load your own `.png`, `.cur`, or `.ico` sprite and choose the hotspot (top-left or center).
- **Game Overlay Support:** Can render on top of borderless games (Geometry Dash, osu!, etc.).
- **Zero Input Lag:** The overlay uses native `WS_EX_TRANSPARENT` and `WS_EX_NOACTIVATE` flags. It will never steal window focus or delay your clicks.
- **Low Resource Usage:** Uses dirty bounding-box rendering on the CPU so it only repaints the pixels where the trail actually is.

### ⌨️ Smooth Caret (FlowText)
Tracks active text inputs across editors, browsers, and Windows apps via the Win32 Accessibility API.

Includes 4 distinct animation modes:
- **Fluid Elastic:** An elastic pill that stretches horizontally based on typing speed.
- **Cyberpunk Glitch:** Spawns tiny colored holographic glitch blocks around characters as you type.
- **Sparkler Particles:** Emits fading glowing sparks behind the caret with mild gravity.
- **Snappy Glide:** Ultra-responsive smooth glide (~25–30 ms) with zero slow spring delay.

---

## 🎮 Important Note for Gamers (Geometry Dash, osu!, etc.)

If you want the trail to appear over games:

1. Enable **"Show trail in games"** in FlowMK settings.
2. In your game's video settings, set display mode to **Borderless** (or Windowed Borderless) instead of *Exclusive Fullscreen*.
   > **Why?** Windows Exclusive Fullscreen bypasses the Desktop Window Manager (DWM) at the GPU level, which blocks all external desktop overlays. Borderless looks and feels identical to fullscreen while allowing overlays to render.
3. If your game runs with Administrator rights (e.g. via Steam or mod loaders), make sure to also run **FlowMK as Administrator**.

---

## 🚀 Running from Source

### Requirements
- Windows 10 or 11 (64-bit)
- Python 3.10+

### Setup
```bash
git clone https://github.com/your-username/FlowMK.git
cd FlowMK
pip install PyQt6
python FlowMK.pyw
