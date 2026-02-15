"""Autoplay - 基于计算机视觉的自动化控制系统.

这是一个基于计算机视觉的自动化控制系统，通过捕获OBS虚拟摄像头画面，
使用模板匹配识别目标位置，并向Arduino发送控制指令实现自动化操作。
"""

__version__ = "0.1.0"

from autoplay.arduino import ArduinoController
from autoplay.capture import VideoCapture, cleanup_directory
from autoplay.config import Config, load_config
from autoplay.keyboard import KeyMapper, KeyStateMachine
from autoplay.logger import configure_logging
from autoplay.vision import TargetDetectionResult, TargetDetector

__all__ = [
    "ArduinoController",
    "Config",
    "KeyMapper",
    "KeyStateMachine",
    "TargetDetectionResult",
    "TargetDetector",
    "VideoCapture",
    "cleanup_directory",
    "configure_logging",
    "load_config",
]
