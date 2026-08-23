import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings
from django.utils.module_loading import import_string


@dataclass
class PaymentResult:
    success: bool
    transaction_id: str = ""
    message: str = ""


class PaymentGateway(ABC):
    """外部決済サービスとのやり取りを抽象化するインターフェース。

    本番では Stripe など実サービスのクライアントを叩く実装に差し替える想定。
    settings.PAYMENT_GATEWAY のドット区切りパスで実装クラスを切り替える。
    """

    @abstractmethod
    def charge(self, *, amount, user, order_id) -> PaymentResult:
        raise NotImplementedError


class DummyPaymentGateway(PaymentGateway):
    """開発用のダミー実装。実際の課金は行わず常に成功を返す。"""

    def charge(self, *, amount, user, order_id) -> PaymentResult:
        return PaymentResult(
            success=True,
            transaction_id=f"dummy_{uuid.uuid4().hex[:12]}",
            message="dummy payment succeeded",
        )


def get_gateway() -> PaymentGateway:
    gateway_class = import_string(settings.PAYMENT_GATEWAY)
    return gateway_class()
