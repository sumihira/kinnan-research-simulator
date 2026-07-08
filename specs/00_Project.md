# Kinnan Research Simulator

Version: 1.0 Draft

---

# 1. プロジェクト概要

## プロジェクト名

Kinnan Research Simulator（KRS）

## 目的

Magic: The Gathering 統率者戦において、
《Kinnan, Bonder Prodigy》デッキを対象とした研究・検証・構築支援ツールを開発する。

- デッキ構築
- プレイ順
- コンボ成立率
- マナ期待値

を統計的に解析することを目的とする。

---

# 2. 開発理念

本プロジェクトは

「勘ではなく、統計でデッキを構築する」

ことを理念とする。

全てのカード採用について

- 数値
- ログ
- リプレイ

による検証を行えることを目標とする。

---

# 3. Version 1.0 ゴール

Version 1.0 完成条件は以下を満たすこと。

## シミュレーション

- 100枚統率者デッキ対応
- ロンドンマリガン対応
- 色拘束対応
- 土地プレイ
- ドロー
- マナ計算
- プレイAI
- Kinnan誘発
- コンボ判定
- Kinnan起動
- ETB処理
- コピー処理

---

## Monte Carlo

100,000ゲーム以上のシミュレーションが可能。

以下を出力する。

- Turn毎平均マナ
- Kinnan着地率
- 起動可能率
- 起動回数
- チェイン回数
- コンボ成立率
- 無限到達率

---

## 比較機能

複数デッキを比較可能。

例

Current List

vs

Shang-Chi Build

vs

Green Sun Build

---

## ログ

全ゲームについて

- プレイログ
- リプレイ
- Random Seed

を保存可能。

---

## レポート

Excel

CSV

HTML

を出力できること。

---

# 4. Version 2.0

Version2では

カード評価システムを追加する。

例

Green Sun's Zenith

採用期待値

+3.1%

など。

---

# 5. Version 3.0

デッキ最適化AI

カード採用候補提案

期待値ランキング

自動構築支援

を目標とする。

---

# 6. 対応フォーマット

Commander

100枚

シングルトン

統率者1枚

現在はKinnan専用。

将来的に他統率者対応。

---

# 7. 開発方針

以下を原則とする。

- テストファースト
- 小さなコミット
- Issue単位で実装
- Pull Request単位でレビュー
- GitHubによる管理
- 仕様書を先に作成

---

# 8. コーディング規約

Python

PEP8準拠

型ヒント必須

Docstring推奨

pytest必須

Black使用

Ruff使用

---

# 9. データ取得

カードデータは

Scryfall API

を利用する。

カード情報はローカルキャッシュを行う。

---

# 10. ログ

以下を保存する。

Game ID

Random Seed

プレイログ

盤面

手札

ライブラリー

評価値

Replay JSON

---

# 11. 統計

Version1では以下を集計する。

平均マナ

平均土地数

平均マナクリ数

平均マナアーティファクト数

Kinnan着地率

Kinnan起動率

平均起動回数

平均チェイン数

無限率

勝利ターン

---

# 12. プロジェクト構成

data/

docs/

experiments/

scripts/

specs/

src/

tests/

---

# 13. 成功条件

以下を満たした時点をVersion1.0完成とする。

現在のKinnanリストと

Shang-Chi採用版を

100,000ゲーム比較し

・Turn毎平均マナ

・起動率

・チェイン率

・無限率

・勝利ターン

・プレイログ

・Replay

を比較・分析できること。