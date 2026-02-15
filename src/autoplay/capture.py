"""视频捕获模块."""

import os
import time
from pathlib import Path
from typing import Self

import cv2
import numpy as np
import structlog

from autoplay.config import CaptureConfig, StorageConfig

logger = structlog.get_logger()


class VideoCapture:
    """视频捕获管理器，支持资源自动释放."""

    def __init__(self, capture_config: CaptureConfig, storage_config: StorageConfig) -> None:
        """初始化视频捕获器.

        Args:
            capture_config: 视频捕获配置
            storage_config: 存储配置
        """
        self.capture_config = capture_config
        self.storage_config = storage_config
        self._cap: cv2.VideoCapture | None = None
        self._logger = structlog.get_logger()
        self._screenshot_dir = Path(storage_config.screenshot_dir)

    def __enter__(self) -> Self:
        """上下文管理器入口."""
        self.open()
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object) -> None:
        """上下文管理器出口."""
        self.close()

    def open(self) -> None:
        """打开摄像头连接."""
        self._logger.info(
            "正在打开摄像头",
            device_index=self.capture_config.device_index,
            width=self.capture_config.width,
            height=self.capture_config.height,
        )

        self._cap = cv2.VideoCapture(self.capture_config.device_index)

        if not self._cap.isOpened():
            msg = f"无法打开摄像头设备 {self.capture_config.device_index}"
            raise RuntimeError(msg)

        # 设置分辨率
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_config.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_config.height)

        # 创建截图目录
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._logger.info("截图目录已创建", path=str(self._screenshot_dir))

    def close(self) -> None:
        """释放摄像头资源."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            self._logger.info("摄像头资源已释放")

    def capture_frame(self, frame_num: int) -> np.ndarray:
        """捕获单帧图像并保存.

        Args:
            frame_num: 帧序号

        Returns:
            捕获的帧图像

        Raises:
            RuntimeError: 当无法获取帧时
        """
        if self._cap is None:
            raise RuntimeError("摄像头未打开")

        ret, frame = self._cap.read()

        if not ret:
            raise RuntimeError("无法获取摄像头帧")

        # 保存帧为图像
        filename = self._screenshot_dir / f"screenshot_{frame_num}.png"
        cv2.imwrite(str(filename), frame)
        self._logger.debug("截图已保存", filename=str(filename))

        # 清理旧截图
        self._cleanup_old_screenshots()

        # 等待指定间隔
        time.sleep(self.capture_config.screenshot_interval)

        return frame

    def _cleanup_old_screenshots(self) -> None:
        """清理超过最大数量的旧截图."""
        files = [
            f for f in self._screenshot_dir.iterdir()
            if f.is_file() and f.suffix == ".png"
        ]

        if len(files) >= self.capture_config.max_screenshots:
            # 按修改时间排序，删除最旧的文件
            oldest_file = min(files, key=lambda f: f.stat().st_mtime)
            try:
                oldest_file.unlink()
                self._logger.debug("已删除旧截图", filename=str(oldest_file))
            except OSError as e:
                self._logger.warning("删除旧截图失败", filename=str(oldest_file), error=str(e))

    def cleanup_all_screenshots(self) -> None:
        """清理所有截图文件."""
        if not self._screenshot_dir.exists():
            return

        for f in self._screenshot_dir.iterdir():
            if f.is_file() and f.suffix == ".png":
                try:
                    f.unlink()
                except OSError:
                    pass

        self._logger.info("所有截图已清理", directory=str(self._screenshot_dir))


def cleanup_directory(directory: str | Path) -> None:
    """清理目录中的所有文件.

    Args:
        directory: 要清理的目录路径
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return

    for f in dir_path.iterdir():
        if f.is_file():
            try:
                f.unlink()
            except OSError as e:
                logger.warning("删除文件失败", filename=str(f), error=str(e))

    logger.info("目录已清理", directory=str(dir_path))
