from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Item
from shoppingCart.models import CartItem

from .gateways import PaymentResult
from .models import Order, OrderItem
from .services import EmptyCartError, checkout

User = get_user_model()


class DecliningGateway:
    """常に失敗を返すテスト用ゲートウェイ。"""

    def charge(self, *, amount, user, order_id):
        return PaymentResult(success=False, message='insufficient funds')


class OrderDetailE2ETest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.other_user = User.objects.create_user(
            username='student2', email='student2@example.com', password='pass12345',
        )
        cls.item = Item.objects.create(name='線形代数学', description='行列とベクトル空間', price=8000)
        cls.order = Order.objects.create(user=cls.owner, total=Decimal('8000.00'), status=Order.Status.PAID)
        OrderItem.objects.create(order=cls.order, item=cls.item, quantity=1, price=cls.item.price)

    def test_owner_can_view_order_detail(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('order_detail', args=[self.order.id]))
        self.assertContains(response, self.item.name)
        self.assertContains(response, '支払い完了')

    def test_other_user_cannot_view_order_detail(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('order_detail', args=[self.order.id]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse('order_detail', args=[self.order.id]))
        expected = f"{reverse('login')}?next={reverse('order_detail', args=[self.order.id])}"
        self.assertRedirects(response, expected)


class CheckoutServiceTest(TestCase):
    """cart -> order の中核ロジックをHTTP層を介さず直接テストする。"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.item = Item.objects.create(name='線形代数学', description='行列とベクトル空間', price=8000)

    def test_checkout_with_no_cart_items_raises(self):
        with self.assertRaises(EmptyCartError):
            checkout(self.user, [])

    @override_settings(PAYMENT_GATEWAY='payments.gateways.DummyPaymentGateway')
    def test_checkout_creates_paid_order_with_snapshot_price(self):
        cart_item = CartItem.objects.create(user=self.user, item=self.item, quantity=3)

        order = checkout(self.user, [cart_item])

        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.total, Decimal('24000.00'))
        self.assertTrue(order.transaction_id)

        order_item = order.items.get()
        self.assertEqual(order_item.quantity, 3)
        self.assertEqual(order_item.price, self.item.price)

    def test_checkout_records_failed_order_and_keeps_cart_when_gateway_declines(self):
        cart_item = CartItem.objects.create(user=self.user, item=self.item)

        with patch('payments.services.get_gateway', return_value=DecliningGateway()):
            order = checkout(self.user, [cart_item])

        self.assertEqual(order.status, Order.Status.FAILED)
        self.assertTrue(CartItem.objects.filter(pk=cart_item.pk).exists())  # cart preserved on failure
