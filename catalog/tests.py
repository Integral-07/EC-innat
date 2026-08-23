from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Item

User = get_user_model()


class CatalogListE2ETest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.available_item = Item.objects.create(
            name='線形代数学', description='行列とベクトル空間', price=8000,
        )
        cls.soldout_item = Item.objects.create(
            name='日本国憲法', description='教職課程必修', price=5500, is_soldout=True,
        )

    def test_anonymous_user_sees_decoy_storefront_not_real_catalog(self):
        response = self.client.get(reverse('catalog_list'))
        self.assertContains(response, '文具舎コトノハ')
        self.assertNotContains(response, self.available_item.name)
        self.assertNotContains(response, 'IN-NAT-EC')

    def test_anonymous_user_cannot_reach_item_detail(self):
        response = self.client.get(reverse('catalog_details', args=[self.available_item.id]))
        self.assertRedirects(response, reverse('catalog_list'), target_status_code=200)

    def test_authenticated_user_sees_real_catalog(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('catalog_list'))
        self.assertContains(response, self.available_item.name)
        self.assertContains(response, self.soldout_item.name)
        self.assertNotContains(response, '文具舎コトノハ')

    def test_authenticated_user_sees_item_detail(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('catalog_details', args=[self.available_item.id]))
        self.assertContains(response, self.available_item.name)
        self.assertContains(response, self.available_item.description)

    def test_soldout_item_detail_disables_add_to_cart_button(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('catalog_details', args=[self.soldout_item.id]))
        self.assertContains(response, 'disabled')
        self.assertContains(response, '売り切れ')

    def test_price_is_rendered_without_decimal_places(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('catalog_list'))
        self.assertContains(response, '¥8000')
        self.assertNotContains(response, '¥8000.00')
