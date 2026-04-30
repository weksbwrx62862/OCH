---
name: slack-gif-creator
description: Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. Use when users request animated GIFs for Slack like "make me a GIF of X doing Y for Slack."
license: Complete terms in LICENSE.txt
---

# Slack GIF Creator

A toolkit providing utilities and knowledge for creating animated GIFs optimized for Slack.

## Slack Requirements

**Dimensions:**
- Emoji GIFs: 128x128 (recommended)
- Message GIFs: 480x480

**Parameters:**
- FPS: 10-30 (lower is smaller file size)
- Colors: 48-128 (fewer = smaller file size)
- Duration: Keep under 3 seconds for emoji GIFs

## Core Workflow

```python
from core.gif_builder import GIFBuilder
from PIL import Image, ImageDraw

builder = GIFBuilder(width=128, height=128, fps=10)
for i in range(12):
    frame = Image.new('RGB', (128, 128), (240, 248, 255))
    draw = ImageDraw.Draw(frame)
    builder.add_frame(frame)

builder.save('output.gif', num_colors=48, optimize_for_emoji=True)
```

## Animation Concepts

### Shake/Vibrate
Offset object position with oscillation using math.sin() or math.cos()

### Pulse/Heartbeat
Scale object size rhythmically using math.sin()

### Bounce
Object falls and bounces using easing functions

### Spin/Rotate
Rotate object around center using PIL's rotate

### Fade In/Out
Gradually appear or disappear

### Slide
Move object from off-screen to position

### Zoom
Scale and position for zoom effect

## Dependencies

```bash
pip install pillow imageio numpy
```
