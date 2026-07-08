# AI_Design.md

Version: 1.0 Draft

---

# 1. 目的

本ドキュメントは Kinnan Research Simulator（KRS）における
AIアーキテクチャを定義する。

AIの目的はプレイヤーを模倣することではなく、
デッキの性能を公平かつ再現性を持って評価することである。

---

# 2. 基本理念

KRSのAIは

「ゲームAI」

ではない。

「デッキ研究AI」

である。

AIは

・期待値

・再現性

・速度

・比較可能性

を最優先する。

---

# 3. AI全体構成

                 +----------------------+
                 |     Game Engine      |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |    Decision Engine   |
                 +----------+-----------+
                            |
          +-----------------+-----------------+
          |                                   |
          v                                   v
 +----------------------+          +----------------------+
 | Action Generator     |          | Action Evaluator     |
 +----------------------+          +----------------------+
          |                                   |
          +-----------------+-----------------+
                            |
                            v
                 +----------------------+
                 |     Strategy         |
                 +----------------------+

---

# 4. 各コンポーネント

## 4.1 Action Generator

役割

現在実行可能な行動を全列挙する。

例

- 土地プレイ
- 呪文キャスト
- 起動能力
- Kinnan起動
- Tutor
- Pass

Generatorは評価を行わない。

---

## 4.2 Action Evaluator

各ActionへScoreを与える。

例

Cast Kinnan

Score = 100

Play Land

Score = 30

Tutor

Score = 60

Pass

Score = -100

Evaluatorは

盤面

手札

マナ

ライブラリー枚数

を評価する。

---

## 4.3 Decision Engine

Evaluatorから受け取ったScoreの最大値を選択する。

Version1では

ArgMax

のみ実装する。

将来的に

Beam Search

MCTS

へ置き換え可能。

---

## 4.4 Strategy

Strategyは

「どんなプレイを目指すか」

を定義する。

AI本体とは分離する。

---

# 5. Strategy一覧

Version1

BalancedStrategy

Version2

AggressiveStrategy

ComboStrategy

TutorStrategy

ChainStrategy

ShangChiStrategy

GreenSunStrategy

---

# 6. Action Pipeline

AIは以下の流れで行動する。

GameState

↓

Action Generator

↓

Action Evaluator

↓

Decision

↓

Game Engine

↓

GameState更新

↓

繰り返し

---

# 7. 評価関数

Version1ではRule Basedを採用する。

Scoreは

Score =
Mana
+ Board
+ Combo
+ Tutor
+ Chain
+ Win

で計算する。

---

# 8. Rule Based

Version1では

条件分岐で評価する。

例

Kinnanが戦場にいない

↓

Cast Kinnan

+100

---

土地が未プレイ

↓

Play Land

+20

---

無限コンボ成立

↓

Combo

+10000

---

# 9. 評価項目

Version1

・マナ期待値

・Kinnan着地

・Kinnan起動

・Combo成立

・Chain継続

・Tutor価値

・盤面価値

・勝利期待値

---

# 10. AIが知らない情報

AIは

ライブラリー順

乱数

未来

を見てはならない。

デッキ内容は知っていてよい。

---

# 11. AIログ

各Actionについて保存する。

Turn

Candidate Actions

Chosen Action

Score

Reason

Elapsed Time

---

# 12. 将来の探索

Version2

1手探索

Version3

2手探索

Version4

Beam Search

Version5

Monte Carlo Tree Search

---

# 13. Beam Search

探索幅

Top N

のみ探索する。

Version4で実装予定。

---

# 14. Monte Carlo Tree Search

Version5で実装。

UCT

Rollout

Backpropagation

を採用予定。

---

# 15. Reinforcement Learning

Version6以降

Self Play

Policy

Value

Neural Network

GPU

を検討する。

---

# 16. 設計原則

Action Generatorは評価しない。

EvaluatorはGameStateを書き換えない。

DecisionはScore最大を選ぶ。

StrategyはAIを変更しない。

Game EngineのみGameStateを書き換える。

---

# 17. テスト方針

Action Generator

Evaluator

Decision

Strategy

は個別Unit Testを作成する。

Game Engineとは独立してテストできる設計とする。

---

# 18. 将来のデッキ比較

Strategyを変更するだけで

以下の比較が可能となる。

Current List

↓

Shang-Chi Build

↓

Green Sun Build

↓

Finale Build

↓

Chord Build

↓

Nature's Rhythm Build

AI本体は変更しない。

---

# 19. Version1完成条件

以下を満たす。

・Action生成

・Action評価

・Action選択

・Rule Based

・Replay対応

・Deterministic

---

# 20. AI設計思想

KRSのAIは

「最強プレイヤー」

を作るものではない。

「最も公平にデッキを比較できる研究AI」

を作ることを目的とする。