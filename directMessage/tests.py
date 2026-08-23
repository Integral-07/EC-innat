from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Conversation, Message

User = get_user_model()


def make_gemini_client(reply_text):
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(text=reply_text)
    return client


class ProfessorListAndConversationStartE2ETest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.professor = User.objects.create_user(
            username='prof_sato', email='sato@example.com', password='password', is_professor=True,
        )

    def setUp(self):
        self.client.force_login(self.student)

    def test_professor_list_shows_professors_only(self):
        response = self.client.get(reverse('professor_list'))
        self.assertContains(response, self.professor.username)
        self.assertNotContains(response, self.student.username)

    def test_starting_conversation_creates_it_and_redirects_to_thread(self):
        response = self.client.post(reverse('conversation_start', args=[self.professor.id]))
        conversation = Conversation.objects.get(student=self.student, professor=self.professor)
        self.assertRedirects(response, reverse('conversation_detail', args=[conversation.id]))

    def test_starting_conversation_twice_reuses_existing_one(self):
        self.client.post(reverse('conversation_start', args=[self.professor.id]))
        self.client.post(reverse('conversation_start', args=[self.professor.id]))
        self.assertEqual(
            Conversation.objects.filter(student=self.student, professor=self.professor).count(), 1,
        )

    def test_cannot_start_conversation_with_non_professor(self):
        response = self.client.post(reverse('conversation_start', args=[self.student.id]))
        self.assertEqual(response.status_code, 404)


class ConversationThreadE2ETest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.other_student = User.objects.create_user(
            username='student2', email='student2@example.com', password='pass12345',
        )
        cls.professor = User.objects.create_user(
            username='prof_sato', email='sato@example.com', password='password', is_professor=True,
        )
        cls.conversation = Conversation.objects.create(student=cls.student, professor=cls.professor)

    def test_student_can_send_message(self):
        self.client.force_login(self.student)
        self.client.post(
            reverse('message_create', args=[self.conversation.id]),
            {'body': '単位をお願いします'},
        )
        message = Message.objects.get(conversation=self.conversation)
        self.assertEqual(message.sender, self.student)
        self.assertEqual(message.body, '単位をお願いします')

    def test_blank_message_is_not_saved(self):
        self.client.force_login(self.student)
        self.client.post(reverse('message_create', args=[self.conversation.id]), {'body': '   '})
        self.assertFalse(Message.objects.filter(conversation=self.conversation).exists())

    def test_professor_can_view_and_reply_in_same_thread(self):
        self.client.force_login(self.student)
        self.client.post(reverse('message_create', args=[self.conversation.id]), {'body': '単位をお願いします'})

        self.client.force_login(self.professor)
        response = self.client.get(reverse('conversation_detail', args=[self.conversation.id]))
        self.assertContains(response, '単位をお願いします')

        self.client.post(reverse('message_create', args=[self.conversation.id]), {'body': '対応できません'})
        self.assertEqual(Message.objects.filter(conversation=self.conversation).count(), 2)

    def test_unrelated_user_cannot_view_conversation(self):
        self.client.force_login(self.other_student)
        response = self.client.get(reverse('conversation_detail', args=[self.conversation.id]))
        self.assertEqual(response.status_code, 404)

    def test_inbox_lists_conversation_with_last_message_preview(self):
        Message.objects.create(conversation=self.conversation, sender=self.student, body='単位をお願いします')

        self.client.force_login(self.student)
        response = self.client.get(reverse('dm_inbox'))
        self.assertContains(response, self.professor.display_name or self.professor.username)
        self.assertContains(response, '単位をお願いします')


@override_settings(GEMINI_API_KEY='test-key')
class AiDeclineReplyE2ETest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.professor = User.objects.create_user(
            username='prof_sato', email='sato@example.com', password='password', is_professor=True,
        )
        cls.conversation = Conversation.objects.create(student=cls.student, professor=cls.professor)

    def test_only_professor_sees_ai_decline_button(self):
        Message.objects.create(conversation=self.conversation, sender=self.student, body='単位をお願いします')

        self.client.force_login(self.student)
        response = self.client.get(reverse('conversation_detail', args=[self.conversation.id]))
        self.assertNotContains(response, 'AIで断る')

        self.client.force_login(self.professor)
        response = self.client.get(reverse('conversation_detail', args=[self.conversation.id]))
        self.assertContains(response, 'AIで断る')

    @patch('directMessage.ai_reply.get_gemini_client')
    def test_ai_decline_reply_uses_gemini_and_posts_generated_text(self, mock_get_client):
        mock_get_client.return_value = make_gemini_client('丁寧だが毅然とした断りの返信です。')
        Message.objects.create(conversation=self.conversation, sender=self.student, body='単位をお願いします')

        self.client.force_login(self.professor)
        response = self.client.post(reverse('ai_decline_reply', args=[self.conversation.id]))

        self.assertRedirects(response, reverse('conversation_detail', args=[self.conversation.id]))
        latest = Message.objects.filter(conversation=self.conversation).latest('created_at')
        self.assertEqual(latest.sender, self.professor)
        self.assertEqual(latest.body, '丁寧だが毅然とした断りの返信です。')

    @patch('directMessage.ai_reply.get_gemini_client')
    def test_ai_decline_button_disabled_after_professor_already_replied(self, mock_get_client):
        mock_get_client.return_value = make_gemini_client('断ります。')
        Message.objects.create(conversation=self.conversation, sender=self.student, body='単位をお願いします')
        self.client.force_login(self.professor)
        self.client.post(reverse('ai_decline_reply', args=[self.conversation.id]))

        response = self.client.get(reverse('conversation_detail', args=[self.conversation.id]))
        self.assertContains(response, 'disabled')

    def test_ai_decline_reply_falls_back_to_dummy_when_gemini_key_missing(self):
        Message.objects.create(conversation=self.conversation, sender=self.student, body='単位をお願いします')
        self.client.force_login(self.professor)

        with override_settings(GEMINI_API_KEY=''):
            self.client.post(reverse('ai_decline_reply', args=[self.conversation.id]))

        latest = Message.objects.filter(conversation=self.conversation).latest('created_at')
        self.assertIn('成績評価は公正な基準', latest.body)

    @patch('directMessage.ai_reply.get_gemini_client')
    def test_ai_decline_reply_falls_back_to_dummy_when_gemini_call_fails(self, mock_get_client):
        mock_get_client.return_value.models.generate_content.side_effect = Exception('network error')
        Message.objects.create(conversation=self.conversation, sender=self.student, body='単位をお願いします')
        self.client.force_login(self.professor)

        self.client.post(reverse('ai_decline_reply', args=[self.conversation.id]))

        latest = Message.objects.filter(conversation=self.conversation).latest('created_at')
        self.assertIn('成績評価は公正な基準', latest.body)

    def test_student_cannot_trigger_ai_decline(self):
        Message.objects.create(conversation=self.conversation, sender=self.student, body='単位をお願いします')
        self.client.force_login(self.student)
        response = self.client.post(reverse('ai_decline_reply', args=[self.conversation.id]))
        self.assertEqual(response.status_code, 404)


class AiDeclineDebugButtonE2ETest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username='student1', email='student1@example.com', password='pass12345',
        )
        cls.professor = User.objects.create_user(
            username='prof_sato', email='sato@example.com', password='password', is_professor=True,
        )
        cls.conversation = Conversation.objects.create(student=cls.student, professor=cls.professor)

    def setUp(self):
        self.client.force_login(self.professor)

    @override_settings(DEBUG=True)
    def test_debug_button_visible_and_injects_student_message_then_ai_reply(self):
        response = self.client.get(reverse('conversation_detail', args=[self.conversation.id]))
        self.assertContains(response, 'AIで断る（デバッグ）')

        self.client.post(reverse('ai_decline_reply_debug', args=[self.conversation.id]))
        messages = list(Message.objects.filter(conversation=self.conversation).order_by('created_at'))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].sender, self.student)
        self.assertEqual(messages[1].sender, self.professor)

    @override_settings(DEBUG=False)
    def test_debug_endpoint_and_button_hidden_when_debug_is_off(self):
        response = self.client.get(reverse('conversation_detail', args=[self.conversation.id]))
        self.assertNotContains(response, 'AIで断る（デバッグ）')

        response = self.client.post(reverse('ai_decline_reply_debug', args=[self.conversation.id]))
        self.assertEqual(response.status_code, 404)
