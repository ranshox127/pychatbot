# interfaces/message_builders/base_builder.py
from abc import ABC, abstractmethod
from linebot.v3.messaging import Message


class MessageBuilder(ABC):
    """
    所有訊息建構器的抽象基礎類別。
    它定義了一個所有具體建構器都必須實現的 `build` 方法。
    """

    @abstractmethod
    def build(self) -> Message:
        """
        建構並回傳一個 linebot.v3.messaging.Message 物件。
        """
        raise NotImplementedError
