# architecture.md

Version: 1.0 Draft

---

# 1. 目的

本ドキュメントは Kinnan Research Simulator（KRS）のシステム全体構成を定義する。

各コンポーネントの責務、依存関係、およびデータフローを明確にし、
保守性・拡張性・テスト容易性を確保することを目的とする。

---

# 2. 設計理念

KRSは

「データ駆動型シミュレーションプラットフォーム」

として設計する。

設計原則

- Single Responsibility Principle
- Dependency Inversion Principle
- Data Driven Design
- Deterministic Simulation
- Test First
- Replayability

---

# 3. システム全体図

```

```
                         +----------------------+
                         |        config        |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |   Card Database      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |     Game Engine      |
                         +----------+-----------+
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
          v                         v                         v
   +-------------+          +---------------+        +---------------+
   | ComboEngine |          | TriggerEngine |        | ManaEngine    |
   +-------------+          +---------------+        +---------------+
          |                         |                         |
          +------------+------------+-------------------------+
                       |
                       v
               +----------------------+
               |      AI Engine       |
               +----------+-----------+
                          |
                          v
               +----------------------+
               | MonteCarlo Engine    |
               +----------+-----------+
                          |
                          v
               +----------------------+
               | Statistics Engine    |
               +----------+-----------+
                          |
                          v
               +----------------------+
               | Report Generator     |
               +----------------------+

```

---

# 4. ディレクトリ構成

```

```
src/
    ai/
    cards/
    combo/
    config/
    engine/
    game/
    io/
    logging/
    mana/
    montecarlo/
    replay/
    report/
    statistics/
    trigger/
    utils/

config/
    strategies/
    combos/
    presets/
    simulation/
    logging/
    report/

docs/

specs/

tests/

experiments/

```

---

# 5. コンポーネント責務

## Game Engine

ゲーム状態の管理。

責務

- Turn
- Phase
- Zone
- Action
- GameState

---

## Card Database

カード情報の取得・管理。

責務

- Scryfall取得
- キャッシュ
- Oracle管理
- カード検索

---

## Mana Engine

マナ生成・支払い・色拘束判定。

---

## Trigger Engine

誘発型能力の検出・解決。

---

## Combo Engine

コンボの検出・進行・終了判定。

---

## AI Engine

プレイ判断。

構成

- Action Generator
- Action Evaluator
- Decision Engine
- Strategy

---

## MonteCarlo Engine

大量シミュレーション実行。

責務

- 並列実行
- Seed管理
- 実験管理

---

## Statistics Engine

統計情報収集。

責務

- Turn統計
- Card統計
- Combo統計
- AI統計

---

## Report Generator

結果出力。

CSV

Excel

HTML

グラフ

---

# 6. データフロー

Deck

↓

Card Database

↓

GameState生成

↓

AI

↓

Action

↓

Game Engine

↓

Statistics

↓

Report

---

# 7. 設定ファイル

config配下の設定はコードを書き換えずに変更可能とする。

対象

- Strategy
- Combo
- Simulation
- Logging
- Report

---

# 8. Replay

Replayは以下を保存する。

- Random Seed
- Action
- GameState
- Statistics

Replayのみでゲームを完全再現できること。

---

# 9. ログ

ログは用途ごとに分類する。

- Engine
- AI
- Combo
- Statistics
- Error

---

# 10. テスト方針

各モジュールは独立してテスト可能であること。

Unit Test

Integration Test

Simulation Test

Regression Test

---

# 11. モジュール依存関係

```

```
config
    ↓

CardDatabase
    ↓

GameEngine
    ↓

AI
    ↓

MonteCarlo
    ↓

Statistics
    ↓

Report

```

逆方向の依存は禁止する。

---

# 12. 設計原則

- CardはImmutable
- Permanentのみ状態を持つ
- GameStateのみゲーム状態を管理する
- AIはGameStateを書き換えない
- EngineのみGameStateを書き換える
- Strategyは設定ファイルで切り替える
- コンボ定義はデータとして管理する

---

# 13. Version1 スコープ

Version1では以下を対象とする。

- Goldfish
- Single Player
- Kinnan
- Rule Based AI
- Monte Carlo Simulation
- Statistics
- Replay

---

# 14. 将来拡張

- Multiplayer
- 他統率者対応
- MCTS
- 強化学習
- GUI
- Web UI
- デッキ最適化AI
- 分散シミュレーション

---

# 15. 完成条件

以下を満たすこと。

- モジュールが責務ごとに分離されている
- 各モジュールが独立してテストできる
- 設定ファイルのみで実験条件を変更できる
- Replayから完全再現できる
- 新カード・新コンボ・新Strategyを容易に追加できる