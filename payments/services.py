from django.db import transaction

from .gateways import get_gateway
from .models import Order, OrderItem


class EmptyCartError(Exception):
    pass


def checkout(user, cart_items):
    """カート内容から Order を作成し、決済ゲートウェイに課金を委託する。

    成功時はカートを空にして支払い済みの Order を返す。
    失敗時も Order は failed として記録され、カートはそのまま残す。
    """
    cart_items = list(cart_items)
    if not cart_items:
        raise EmptyCartError("カートが空です")

    total = sum(ci.subtotal for ci in cart_items)

    with transaction.atomic():
        order = Order.objects.create(user=user, total=total)
        OrderItem.objects.bulk_create([
            OrderItem(order=order, item=ci.item, quantity=ci.quantity, price=ci.item.price)
            for ci in cart_items
        ])

    result = get_gateway().charge(amount=total, user=user, order_id=order.id)

    if result.success:
        order.status = Order.Status.PAID
        order.transaction_id = result.transaction_id
        order.save()
        for ci in cart_items:
            ci.delete()
    else:
        order.status = Order.Status.FAILED
        order.save()

    return order
