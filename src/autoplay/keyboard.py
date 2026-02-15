"""键盘控制模块."""

import random
from typing import Literal

import structlog

logger = structlog.get_logger()


class KeyStateMachine:
    """按键状态机，管理按键序列逻辑."""

    def __init__(
        self,
        movement_keys: list[str] | None = None,
        action_keys: list[str] | None = None,
    ) -> None:
        """初始化按键状态机.

        Args:
            movement_keys: 移动按键列表，默认为 ["w", "a", "s", "d"]
            action_keys: 动作按键列表，默认为 ["-", "f", "e", "r", "n"]
        """
        self.movement_keys = set(movement_keys or ["w", "a", "s", "d"])
        self.action_keys = set(action_keys or ["-", "f", "e", "r", "n"])
        self._previous_key: str | None = None
        self._logger = structlog.get_logger()

    def next_key(self) -> str:
        """根据状态机逻辑生成下一个按键.

        规则：
        - 如果上一次是移动键，这一次只能是动作键
        - 如果上一次是"r"，这一次可以是移动键
        - 其他情况，随机选择所有键

        Returns:
            下一个按键
        """
        if self._previous_key in self.movement_keys:
            # 上一次是移动键，选择动作键
            key = random.choice(list(self.action_keys))
        elif self._previous_key == "r":
            # 上一次是r，选择移动键
            key = random.choice(list(self.movement_keys))
        else:
            # 其他情况，选择所有键
            all_keys = self.movement_keys | self.action_keys
            key = random.choice(list(all_keys))

        self._previous_key = key
        self._logger.debug("生成按键", key=key, previous=self._previous_key)

        return key

    def reset(self) -> None:
        """重置状态机."""
        self._previous_key = None
        self._logger.debug("状态机已重置")

    def get_previous_key(self) -> str | None:
        """获取上一个按键.

        Returns:
            上一个按键，如果没有则返回None
        """
        return self._previous_key


def check_exit_key(exit_key: str) -> bool:
    """检查是否按下了退出键.

    Args:
        exit_key: 退出键名称

    Returns:
        是否按下了退出键
    """
    import keyboard

    return keyboard.is_pressed(exit_key)


class KeyMapper:
    """按键映射器，支持预设按键序列."""

    def __init__(self) -> None:
        """初始化按键映射器."""
        self._presets: dict[str, list[str]] = {
            "Shenzhen": [
                "d",
                "n",
                "r",
                "w",
                "n",
                "n",
                "r",
                "-",
                "w",
                "n",
                "n",
                "n",
                "r",
                "s",
                "r",
            ],
        }
        self._logger = structlog.get_logger()

    def get_preset(self, name: str) -> list[str] | None:
        """获取预设按键序列.

        Args:
            name: 预设名称

        Returns:
            按键序列，未找到时返回None
        """
        sequence = self._presets.get(name)
        if sequence:
            self._logger.debug("加载预设序列", name=name, length=len(sequence))
        return sequence

    def add_preset(self, name: str, sequence: list[str]) -> None:
        """添加预设按键序列.

        Args:
            name: 预设名称
            sequence: 按键序列
        """
        self._presets[name] = sequence
        self._logger.info("添加预设序列", name=name, length=len(sequence))
