# Shoppi — せどり自動出品アプリ 開発状況

最終更新: 2026-04-28

---

## 概要

女性ママ向けのせどり自動出品Webアプリ。
仕入れ先（AliExpress）から商品を探し、販売先（BASE）とInstagramへの投稿を自動化する。

- **本番URL**: https://sedori-app-s47h.onrender.com
- **リポジトリ**: https://github.com/stellareditcnt-web/sedori-app

---

## 技術スタック

| 部分 | 技術 |
|------|------|
| バックエンド | Python 3.10 + FastAPI |
| フロントエンド | HTML + TailwindCSS CDN + Alpine.js |
| AI リサーチ | Google Gemini API（gemini-2.5-flash） |
| 商品検索 | AliExpress DS 公式 API（AppKey: 533080） |
| 自動出品 | BASE API（OAuth 2.0） |
| デプロイ | Render（無料プラン） |

---

## 機能実装状況

| 機能 | 状態 | 備考 |
|------|------|------|
| Gemini トレンドリサーチ | ✅ 完了 | コンセプト入力→キーワード生成 |
| 商品検索 | ✅ 完了 | AliExpress DS 公式 API（JPY・日本語・JP発送） |
| 価格自動計算 | ✅ 完了 | 原価×3（変更可能） |
| BASE OAuth認証 | ✅ 完了 | base_token.json に保存。リフレッシュトークン自動更新対応 |
| BASE 自動出品 | ✅ 完了 | 画像・タイトル・説明文・価格を自動投稿 |
| デプロイ（スマホ対応） | ✅ 完了 | Render + PWA対応UI |
| Instagram 自動投稿 | ⏳ 進行中 | Meta Developer App作成済み。Graph API実装待ち |
| AliExpress 公式 API | ✅ 完了 | DS API（Dropshipping individual）審査即通過・切り替え済み |
| 価格ルール詳細化 | ⏳ 未定 | 現在は原価×3のみ |
| Taobao 連携 | ❌ スコープ外 | 難易度高のため今回は対象外 |
| TikTok Shop 連携 | ❌ スコープ外 | 審査が厳しいため今回は対象外 |

---

## 環境変数（.env）

```
GEMINI_API_KEY=              # Google AI Studio で取得
BASE_CLIENT_ID=              # BASE 開発者ポータル
BASE_CLIENT_SECRET=          # BASE 開発者ポータル
BASE_REDIRECT_URI=           # 本番: https://sedori-app-s47h.onrender.com/auth/callback
ALIEXPRESS_APP_KEY=533080    # AliExpress Open Platform（DS App）
ALIEXPRESS_APP_SECRET=       # AliExpress Open Platform（DS App）
RAPIDAPI_KEY=                # 現在未使用（公式APIに切り替え済み）
# 後で追加
# INSTAGRAM_ACCESS_TOKEN=    # Meta Developer App作成済み・実装待ち
```

---

## ファイル構成

```
sedori-app/
├── main.py                  # FastAPI エントリーポイント
├── config.py                # 価格ルール設定（price_multiplier）
├── routers/
│   ├── research.py          # Gemini トレンドリサーチ API
│   ├── products.py          # AliExpress 商品検索 API
│   ├── publish.py           # BASE / Instagram 出品 API
│   └── base_auth.py         # BASE OAuth 認証フロー
├── templates/
│   └── index.html           # フロントエンド（TailwindCSS + Alpine.js）
├── static/js/
│   └── app.js               # フロントエンド ロジック
├── requirements.txt
├── render.yaml
└── .env                     # ローカル用（Git管理外）
```

---

## 残タスク・TODO

### 優先度高
- [x] AliExpress 公式 DS API に切り替え完了（`routers/products.py`）
- [ ] Instagram 自動投稿の実装
  - [x] Meta Developer App 作成（ユースケース: Instagramでメッセージとコンテンツを管理）
  - [x] Instagram ビジネスアカウント設定済み
  - [ ] Instagram Graph API アクセストークン取得
  - [ ] `/api/publish` の instagram 部分を実装

### 優先度中
- [ ] 価格ルールの詳細化（送料・手数料込みの自動計算）
- [ ] BASE 出品後に商品URLを取得して表示
- [ ] 商品説明文を Gemini で日本語に自動翻訳・改善

### 優先度低
- [ ] Render の有料プランへの移行（無料プランは15分で自動スリープ）
- [x] RapidAPI 撤廃済み（AliExpress 公式 API に完全移行）

---

## 既知の問題

| 問題 | 原因 | 対処 |
|------|------|------|
| Render が最初のアクセスで遅い | 無料プランのスリープ機能 | 有料プランで解消（月$7〜） |
| BASE 認証トークンの期限切れ | OAuth トークンに1時間の有効期限あり | リフレッシュトークン自動更新を実装済み（2026-04-28） |
| BASE管理画面URLが誤っていた | パスが `/items/detail/` だった | `/shop_admin/items/edit/` に修正済み（2026-04-28） |

---

## BASE 認証手順（再認証が必要な場合）

1. `https://sedori-app-s47h.onrender.com/auth/base` にアクセス
2. BASE アカウントでログインして許可
3. `{"message":"BASE認証完了！"}` が表示されれば OK

---

## ローカル起動方法

```bash
cd /Users/utausaru/Desktop/開発/sedori-app
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8010
```

ブラウザで `http://localhost:8010` を開く。
