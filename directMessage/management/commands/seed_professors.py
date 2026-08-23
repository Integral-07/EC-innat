from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

SEED_PROFESSORS = [
    {"username": "prof_sato", "email": "sato@example.com", "display_name": "佐藤教授"},
    {"username": "prof_suzuki", "email": "suzuki@example.com", "display_name": "鈴木教授"},
    {"username": "prof_takahashi", "email": "takahashi@example.com", "display_name": "高橋教授"},
]


class Command(BaseCommand):
    help = "directMessage の相談相手となる教授アカウントを開発用に投入します"

    def handle(self, *args, **options):
        created_count = 0
        for data in SEED_PROFESSORS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "display_name": data["display_name"],
                    "is_professor": True,
                },
            )
            if created:
                user.set_unusable_password()
                user.save()
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{created_count} 件の教授アカウントを作成しました（既存の {len(SEED_PROFESSORS) - created_count} 件はスキップ）"
            )
        )
