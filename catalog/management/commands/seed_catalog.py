from django.core.management.base import BaseCommand

from catalog.models import Item

SEED_ITEMS = [
    {
        "name": "線形代数学",
        "description": "行列・ベクトル空間・固有値問題を扱う数学基礎科目。理系全学部の必修単位。",
        "price": 8000,
        "is_soldout": False,
    },
    {
        "name": "微分積分学",
        "description": "1変数・多変数の微分積分を学ぶ数学基礎科目。",
        "price": 8000,
        "is_soldout": False,
    },
    {
        "name": "情報リテラシー",
        "description": "PCの基本操作、タイピング、レポート作成のためのソフトウェア活用法を学ぶ全学共通科目。",
        "price": 6000,
        "is_soldout": False,
    },
    {
        "name": "統計学入門",
        "description": "記述統計・推測統計の基礎を学び、データ分析の基本的な考え方を身につける。",
        "price": 7500,
        "is_soldout": False,
    },
    {
        "name": "英語コミュニケーションI",
        "description": "リスニング・スピーキングを中心とした実践的英語運用能力を養う語学科目。",
        "price": 6500,
        "is_soldout": True,
    },
    {
        "name": "アルゴリズムとデータ構造",
        "description": "探索・整列アルゴリズムと基本的なデータ構造の設計・実装を学ぶ専門科目。",
        "price": 9000,
        "is_soldout": False,
    },
    {
        "name": "経済学概論",
        "description": "ミクロ経済学・マクロ経済学の基礎理論を学ぶ社会科学系科目。",
        "price": 7000,
        "is_soldout": False,
    },
    {
        "name": "日本国憲法",
        "description": "日本国憲法の基本原理と主要な判例を学ぶ、教職課程必修の一般科目。",
        "price": 5500,
        "is_soldout": True,
    },
]


class Command(BaseCommand):
    help = "catalog アプリの Item に開発用のサンプルデータ（履修可能科目）を投入します"

    def handle(self, *args, **options):
        created_count = 0
        for data in SEED_ITEMS:
            item, created = Item.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "price": data["price"],
                    "is_soldout": data["is_soldout"],
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{created_count} 件の Item を作成しました（既存の {len(SEED_ITEMS) - created_count} 件はスキップ）"
            )
        )
