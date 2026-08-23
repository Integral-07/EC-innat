from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Item

from .models import CartItem

User = get_user_model()


class CartE2ETest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.other_user = User.objects.create_user(
            username='student2', email='student2@example.com', password='pass12345',
        )
        cls.item = Item.objects.create(name='線形代数学', description='行列とベクトル空間', price=8000)
        cls.soldout_item = Item.objects.create(
            name='日本国憲法', description='教職課程必修', price=5500, is_soldout=True,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_add_item_to_cart_creates_cart_item(self):
        self.client.post(reverse('cart_item_create', args=[self.item.id]))
        self.assertTrue(CartItem.objects.filter(user=self.user, item=self.item).exists())

    def test_add_same_item_twice_increments_quantity_instead_of_duplicating(self):
        self.client.post(reverse('cart_item_create', args=[self.item.id]))
        self.client.post(reverse('cart_item_create', args=[self.item.id]))

        self.assertEqual(CartItem.objects.filter(user=self.user, item=self.item).count(), 1)
        cart_item = CartItem.objects.get(user=self.user, item=self.item)
        self.assertEqual(cart_item.quantity, 2)

    def test_soldout_item_cannot_be_added_to_cart(self):
        self.client.post(reverse('cart_item_create', args=[self.soldout_item.id]))
        self.assertFalse(CartItem.objects.filter(user=self.user, item=self.soldout_item).exists())

    def test_cart_detail_shows_added_items_and_total(self):
        CartItem.objects.create(user=self.user, item=self.item, quantity=2)
        response = self.client.get(reverse('cart_detail'))
        self.assertContains(response, self.item.name)
        self.assertContains(response, '¥16000')  # 8000 * 2

    def test_remove_item_deletes_cart_item(self):
        CartItem.objects.create(user=self.user, item=self.item)
        self.client.post(reverse('cart_item_delete', args=[self.item.id]))
        self.assertFalse(CartItem.objects.filter(user=self.user, item=self.item).exists())

    def test_cannot_remove_another_users_cart_item(self):
        other_cart_item = CartItem.objects.create(user=self.other_user, item=self.item)
        self.client.post(reverse('cart_item_delete', args=[self.item.id]))
        self.assertTrue(CartItem.objects.filter(pk=other_cart_item.pk).exists())

    def test_cart_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('cart_detail'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('cart_detail')}")

    def test_get_request_cannot_add_to_cart(self):
        response = self.client.get(reverse('cart_item_create', args=[self.item.id]))
        self.assertEqual(response.status_code, 405)


class CheckoutE2ETest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.item = Item.objects.create(name='線形代数学', description='行列とベクトル空間', price=8000)

    def setUp(self):
        self.client.force_login(self.user)

    def test_checkout_with_empty_cart_shows_error_and_stays_on_cart_page(self):
        response = self.client.post(reverse('cart_checkout'), follow=True)
        self.assertRedirects(response, reverse('cart_detail'))
        self.assertContains(response, 'カートが空です')

    def test_checkout_with_items_clears_cart_and_redirects_to_order(self):
        CartItem.objects.create(user=self.user, item=self.item, quantity=2)

        response = self.client.post(reverse('cart_checkout'))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(CartItem.objects.filter(user=self.user).exists())

        from payments.models import Order
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.total, Decimal('16000.00'))
        self.assertRedirects(response, reverse('order_detail', args=[order.id]))
