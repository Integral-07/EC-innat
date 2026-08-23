# ec-innat

単位（科目）を購入するというモチーフの EC サイト（Django）。

## アプリ構成

- `accounts` — カスタムユーザーモデル（`AbstractUser` 継承）とログイン機能
- `catalog` — 購入可能な科目（`Item`）の一覧・詳細
- `shoppingCart` — カート（`CartItem`）。追加・削除・購入（チェックアウト）
- `payments` — 注文（`Order` / `OrderItem`）と決済ゲートウェイの抽象化
- `directMessage` — 学生と教授のDM（`Conversation` / `Message`）、AIによる断り返信（Gemini API、キー未設定時はダミー文にフォールバック）

## セットアップ

```bash
python3 manage.py migrate
python3 manage.py seed_catalog      # 開発用の科目データを投入
python3 manage.py seed_professors   # DM相手の教授アカウントを投入（パスワードは "password"）
python3 manage.py runserver
```

学生役のアカウントは `python3 manage.py createsuperuser` などで別途作成してください（サインアップ画面は未実装）。

主要な URL:

- `/catalog/list/` — 科目一覧
- `/catalog/details/<item_id>/` — 科目詳細（カートに入れる）
- `/cart/` — カート（購入する）
- `/orders/<order_id>/` — 注文確認

## 決済モジュールについて

決済処理は外部サービス（Stripe 等）への委託を前提に、`payments` アプリ内で抽象化している。

- `payments/gateways.py` の `PaymentGateway` が実装すべきインターフェース（`charge()`）
- 開発時は `DummyPaymentGateway`（常に成功を返すダミー実装）を使用
- 実際に使う実装は `settings.PAYMENT_GATEWAY`（ドット区切りパス）で指定

```python
# ec_innat/settings.py
PAYMENT_GATEWAY = 'payments.gateways.DummyPaymentGateway'
```

本番で外部サービスに接続する場合は、`payments/gateways.py`（または別モジュール）に
`PaymentGateway` を実装したクラスを追加し、`PAYMENT_GATEWAY` をそのクラスのパスに
差し替えるだけでよい。呼び出し側（`payments/services.py` の `checkout()`）の変更は不要。

注文（`Order`）を作成できる経路はカート画面の「購入する」ボタンが叩く
`POST /cart/checkout/`（`shoppingCart.views.cart_checkout`）のみで、
`payments` アプリの URL は確認用の `GET /orders/<id>/` しか公開していない。

## テスト

各アプリの `tests.py` に単体〜結合テスト、`e2e_tests/` に複数アプリをまたぐ
一連のユーザージャーニー（購入フロー、DM+AI断りフロー）を置いている。
Gemini API はモック化しているので、テスト実行に `GEMINI_API_KEY` は不要。

```bash
python3 manage.py test                 # 全テスト実行
python3 manage.py test catalog         # 特定アプリのみ

python3 -m coverage run manage.py test # カバレッジ計測付きで実行
python3 -m coverage report             # 結果をターミナルに表示
python3 -m coverage html               # htmlcov/index.html にレポート出力
```
