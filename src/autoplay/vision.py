"""图像处理模块."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
import structlog
from PIL import Image

from autoplay.config import VisionConfig

logger = structlog.get_logger()


@dataclass
class TargetDetectionResult:
    """目标检测结果."""

    direction: Literal["left", "right"]
    distance: int
    confidence: float
    bbox: tuple[int, int, int, int] | None = None  # (x, y, width, height)


class TargetDetector:
    """目标检测器，使用模板匹配算法."""

    def __init__(self, config: VisionConfig) -> None:
        """初始化目标检测器.

        Args:
            config: 图像处理配置
        """
        self.config = config
        self._logger = structlog.get_logger()
        self._template = self._load_template()

    def _load_template(self) -> np.ndarray:
        """加载模板图像.

        Returns:
            模板图像数组

        Raises:
            FileNotFoundError: 当模板文件不存在时
        """
        template_path = Path(self.config.template_path)
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")

        template = cv2.imread(str(template_path))
        if template is None:
            raise RuntimeError(f"无法加载模板图像: {template_path}")

        self._logger.info("模板已加载", path=str(template_path), shape=template.shape)
        return template

    def detect(self, screenshot_path: str | Path) -> TargetDetectionResult | None:
        """检测目标位置.

        Args:
            screenshot_path: 截图文件路径

        Returns:
            检测结果，未找到时返回None
        """
        screenshot_path = Path(screenshot_path)

        if not screenshot_path.exists():
            self._logger.error("截图文件不存在", path=str(screenshot_path))
            return None

        # 打开图片获取尺寸
        try:
            with Image.open(screenshot_path) as image:
                width, height = image.size
        except Exception as e:
            self._logger.error("无法打开截图", path=str(screenshot_path), error=str(e))
            return None

        mid_screen_x = width // 2

        # 使用OpenCV读取图像
        screenshot = cv2.imread(str(screenshot_path))
        if screenshot is None:
            self._logger.error("无法读取截图", path=str(screenshot_path))
            return None

        # 过滤红色部分
        filtered_screenshot = self._filter_red_color(screenshot)
        filtered_template = self._filter_red_color(self._template)

        # 生成缩放比例
        scales = np.linspace(
            self.config.scales_start,
            self.config.scales_end,
            self.config.scales_steps,
        )

        # 多尺度匹配
        best_match, best_val, best_scale = self._multi_scale_match(
            filtered_screenshot, filtered_template, scales, self.config.match_threshold
        )

        if best_match is None:
            self._logger.debug("未找到匹配目标", path=str(screenshot_path))
            return None

        # 计算目标中心位置
        top_left = best_match[0]
        w, h = best_match[1], best_match[2]
        bottom_right = (top_left[0] + w, top_left[1] + h)
        mid_x_prev = (top_left[0] + bottom_right[0]) // 2

        # 应用偏移修正
        fix_x = int(1.5 * (mid_x_prev - top_left[0]))
        adjusted_top_left = (top_left[0] - fix_x, top_left[1])
        adjusted_bottom_right = (bottom_right[0] - fix_x, bottom_right[1])
        mid_x = (adjusted_top_left[0] + adjusted_bottom_right[0]) // 2

        # 判断方向
        direction: Literal["left", "right"] = "right" if mid_x > mid_screen_x else "left"
        distance = abs(mid_x - mid_screen_x)

        self._logger.debug(
            "目标检测成功",
            direction=direction,
            distance=distance,
            confidence=best_val,
            scale=best_scale,
        )

        return TargetDetectionResult(
            direction=direction,
            distance=distance,
            confidence=best_val,
            bbox=(adjusted_top_left[0], adjusted_top_left[1], w, h),
        )

    def _filter_red_color(self, image: np.ndarray) -> np.ndarray:
        """HSV颜色空间过滤红色部分.

        Args:
            image: 输入图像

        Returns:
            过滤后的图像
        """
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 定义红色的HSV范围（红色在HSV空间中跨越0度/360度边界）
        lower_red1 = np.array(self.config.red_hsv_lower1)
        upper_red1 = np.array(self.config.red_hsv_upper1)
        lower_red2 = np.array(self.config.red_hsv_lower2)
        upper_red2 = np.array(self.config.red_hsv_upper2)

        # 构建两个红色掩码并合并
        mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
        mask = mask1 + mask2

        # 应用掩码
        return cv2.bitwise_and(image, image, mask=mask)

    def _multi_scale_match(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        scales: np.ndarray,
        threshold: float,
    ) -> tuple[tuple | None, float, float]:
        """多尺度模板匹配.

        Args:
            screenshot: 截图图像
            template: 模板图像
            scales: 缩放比例数组
            threshold: 匹配阈值

        Returns:
            (最佳匹配位置, 最佳匹配值, 最佳缩放比例)
        """
        gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        template_h, template_w = template.shape[:2]

        best_match = None
        best_val = 0.0
        best_scale = 1.0

        for scale in scales:
            # 缩放模板
            scaled_w = int(template_w * scale)
            scaled_h = int(template_h * scale)

            if scaled_w < 10 or scaled_h < 10:
                continue

            scaled_template = cv2.resize(template, (scaled_w, scaled_h))
            scaled_template_gray = cv2.cvtColor(scaled_template, cv2.COLOR_BGR2GRAY)

            # 模板匹配
            result = cv2.matchTemplate(
                gray_screenshot, scaled_template_gray, cv2.TM_CCOEFF_NORMED
            )
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            # 更新最佳匹配
            if max_val > threshold and max_val > best_val:
                best_val = max_val
                best_match = (max_loc, scaled_w, scaled_h)
                best_scale = scale

        return best_match, best_val, best_scale
