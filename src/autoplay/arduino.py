"""Arduino通信模块."""

import functools
import time
from typing import Literal, Self

import serial
import serial.tools.list_ports
import structlog

from autoplay.config import ArduinoConfig

logger = structlog.get_logger()


def retry_on_error(max_retries: int = 3, delay: float = 0.5):
    """重试装饰器.

    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying...",
                        error=str(e),
                        function=func.__name__,
                    )
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


class ArduinoController:
    """Arduino控制器，支持连接复用和自动重试."""

    def __init__(self, config: ArduinoConfig) -> None:
        """初始化Arduino控制器.

        Args:
            config: Arduino配置
        """
        self.config = config
        self._serial: serial.Serial | None = None
        self._port: str | None = None
        self._logger = structlog.get_logger()

    def __enter__(self) -> Self:
        """上下文管理器入口."""
        self.connect()
        return self

    def __exit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        """上下文管理器出口."""
        self.disconnect()

    @retry_on_error(max_retries=3, delay=0.5)
    def connect(self) -> None:
        """建立Arduino连接."""
        port = self.find_port()
        if port is None:
            raise ConnectionError("未找到Arduino设备")

        self._port = port
        self._logger.info("正在连接Arduino", port=port, baudrate=self.config.baudrate)

        self._serial = serial.Serial(
            port,
            self.config.baudrate,
            timeout=self.config.timeout,
        )

        # 等待Arduino初始化
        time.sleep(0.5)
        self._logger.info("Arduino连接成功")

    def disconnect(self) -> None:
        """断开Arduino连接."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
            self._serial = None
            self._logger.info("Arduino已断开")

    @retry_on_error(max_retries=2, delay=0.2)
    def send_command(
        self, direction: Literal["left", "right"], distance: int, key: str
    ) -> None:
        """发送控制指令.

        Args:
            direction: 方向 (left/right)
            distance: 距离值
            key: 按键值

        Raises:
            ConnectionError: 当未连接时
            RuntimeError: 当发送失败时
        """
        if self._serial is None or not self._serial.is_open:
            raise ConnectionError("Arduino未连接")

        data = f"{direction}:{distance}:{key}"
        encoded_data = data.encode("utf-8")

        try:
            self._serial.write(encoded_data)
            self._logger.debug(
                "指令已发送", direction=direction, distance=distance, key=key
            )
        except serial.SerialException as e:
            raise RuntimeError(f"发送数据失败: {e}") from e

    def find_port(self) -> str | None:
        """自动查找Arduino端口.

        Returns:
            端口号，未找到时返回None
        """
        ports = serial.tools.list_ports.comports()
        target_vid = self.config.get_vid_int()
        target_pid = self.config.get_pid_int()

        self._logger.debug(
            "正在查找Arduino设备",
            target_vid=hex(target_vid),
            target_pid=hex(target_pid),
        )

        for port in ports:
            self._logger.debug(
                "检查端口",
                device=port.device,
                vid=hex(port.vid) if port.vid else None,
                pid=hex(port.pid) if port.pid else None,
            )

            if port.vid == target_vid and port.pid == target_pid:
                self._logger.info("找到Arduino设备", port=port.device)
                return port.device

        self._logger.warning("未找到Arduino设备")
        return None

    def is_connected(self) -> bool:
        """检查是否已连接."""
        return self._serial is not None and self._serial.is_open
