from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class LoginE2ETest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='pass12345',
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_with_correct_credentials_redirects_and_starts_session(self):
        response = self.client.post(reverse('login'), {
            'username': 'student1',
            'password': 'pass12345',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')  # LOGIN_REDIRECT_URL, itself redirects to catalog_list

        response = self.client.get(reverse('cart_detail'))
        self.assertEqual(response.status_code, 200)  # no longer redirected to login

    def test_login_with_wrong_password_rerenders_form_with_error(self):
        response = self.client.post(reverse('login'), {
            'username': 'student1',
            'password': 'wrong-password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            None,
            "Please enter a correct username and password. Note that both fields may be case-sensitive.",
        )

    def test_logout_ends_session(self):
        self.client.force_login(self.user)
        self.client.post(reverse('logout'))

        response = self.client.get(reverse('cart_detail'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('cart_detail')}")

    def test_is_professor_defaults_to_false(self):
        self.assertFalse(self.user.is_professor)
