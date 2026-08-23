"""
複数アプリ（catalog / shoppingCart / payments / directMessage）をまたいだ
一連のユーザージャーニーを通しで検証するE2Eテスト。
各アプリ単体の詳細な分岐は各アプリの tests.py で担保しているので、
ここでは「一連の流れが繋がって動くこと」に焦点を当てる。
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Item
from directMessage.models import Conversation, Message
from payments.models import Order
from shoppingCart.models import CartItem

User = get_user_model()


class PurchaseJourneyE2ETest(TestCase):
    """匿名アクセス→ログイン→商品閲覧→カート→購入完了までの一連の流れ。"""

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.item = Item.objects.create(name='線形代数学', description='行列とベクトル空間', price=8000)

    def test_full_purchase_journey(self):
        # 1. 匿名ではダミーの入口ページが見える(実データは見えない)
        response = self.client.get(reverse('catalog_list'))
        self.assertContains(response, '文具舎コトノハ')
        self.assertNotContains(response, self.item.name)

        # 2. ログイン
        self.client.login(username='student1', password='pass12345')

        # 3. 本物のカタログと商品詳細が見える
        response = self.client.get(reverse('catalog_list'))
        self.assertContains(response, self.item.name)

        response = self.client.get(reverse('catalog_details', args=[self.item.id]))
        self.assertContains(response, self.item.name)

        # 4. カートに追加
        self.client.post(reverse('cart_item_create', args=[self.item.id]))
        self.assertTrue(CartItem.objects.filter(user=self.student, item=self.item).exists())

        response = self.client.get(reverse('cart_detail'))
        self.assertContains(response, self.item.name)

        # 5. 購入する
        response = self.client.post(reverse('cart_checkout'))
        order = Order.objects.get(user=self.student)
        self.assertRedirects(response, reverse('order_detail', args=[order.id]))
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.total, Decimal('8000.00'))

        # 6. カートは空になり、注文詳細に商品が表示される
        self.assertFalse(CartItem.objects.filter(user=self.student).exists())
        response = self.client.get(reverse('order_detail', args=[order.id]))
        self.assertContains(response, self.item.name)
        self.assertContains(response, '支払い完了')


class DirectMessageJourneyE2ETest(TestCase):
    """学生が教授に相談 → 教授がAIで断る、までの一連の流れ。"""

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.professor = User.objects.create_user(
            username='prof_sato', email='sato@example.com', password='password',
            display_name='佐藤教授', is_professor=True,
        )

    @override_settings(GEMINI_API_KEY='test-key')
    @patch('directMessage.ai_reply.get_gemini_client')
    def test_full_dm_journey(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = MagicMock(
            text='成績基準に基づき対応できません。',
        )
        mock_get_client.return_value = mock_client

        # 1. 学生が教授一覧から相談を開始
        self.client.login(username='student1', password='pass12345')
        response = self.client.get(reverse('professor_list'))
        self.assertContains(response, '佐藤教授')

        response = self.client.post(reverse('conversation_start', args=[self.professor.id]))
        conversation = Conversation.objects.get(student=self.student, professor=self.professor)
        self.assertRedirects(response, reverse('conversation_detail', args=[conversation.id]))

        # 2. 学生がメッセージを送信
        self.client.post(
            reverse('message_create', args=[conversation.id]),
            {'body': '単位をいただけないでしょうか。'},
        )

        # 3. 教授側からスレッドが見え、AIで断るボタンが使える
        self.client.logout()
        self.client.login(username='prof_sato', password='password')
        response = self.client.get(reverse('conversation_detail', args=[conversation.id]))
        self.assertContains(response, '単位をいただけないでしょうか。')
        self.assertNotContains(response, 'disabled')  # AIで断るボタンは有効

        response = self.client.post(reverse('ai_decline_reply', args=[conversation.id]))
        self.assertRedirects(response, reverse('conversation_detail', args=[conversation.id]))

        # 4. AIの返信がスレッドに残り、送った直後はボタンがdisableになる
        latest = Message.objects.filter(conversation=conversation).latest('created_at')
        self.assertEqual(latest.sender, self.professor)
        self.assertEqual(latest.body, '成績基準に基づき対応できません。')

        response = self.client.get(reverse('conversation_detail', args=[conversation.id]))
        self.assertContains(response, 'disabled')

        # 5. 学生側にも返信が見える
        self.client.logout()
        self.client.login(username='student1', password='pass12345')
        response = self.client.get(reverse('conversation_detail', args=[conversation.id]))
        self.assertContains(response, '成績基準に基づき対応できません。')
