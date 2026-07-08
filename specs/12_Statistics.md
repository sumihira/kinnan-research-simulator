# 12_Statistics.md

Version: 1.0 Draft

---

# 1. 目的

本仕様書では、Kinnan Research Simulator（KRS）で収集・集計する統計情報を定義する。

統計情報は以下の目的で利用する。

- デッキ比較
- プレイ分析
- コンボ分析
- AI評価
- レポート生成
- グラフ生成

全ての統計情報は再現可能であること。

---

# 2. 統計レベル

統計情報は4つの粒度で収集する。

Level 1

ゲーム全体

Level 2

ターン単位

Level 3

Action単位

Level 4

カード単位

---

# 3. Game Statistics

1ゲーム終了時に集計する。

記録項目

Game ID

Random Seed

Simulation Version

Strategy

Deck Name

Deck Hash

Game Result

Total Turns

Total Actions

Elapsed Time

---

# 4. Turn Statistics

各ターン終了時に記録する。

Turn Number

Starting Hand Size

Cards Drawn

Land Played

Available Mana

Mana Produced

Mana Spent

Floating Mana

Battlefield Count

Hand Count

Library Count

Graveyard Count

Kinnan Activated

Chain Count

Combo Active

---

# 5. Mana Statistics

マナに関する統計。

Available Mana

Produced Mana

Spent Mana

Floating Mana

Color Breakdown

W

U

B

R

G

C

最大マナ

平均マナ

---

# 6. Card Statistics

カードごとに集計する。

Draw Count

Cast Count

Play Count

Tutor Count

Hit Count

Activation Count

Win Contribution

---

# 7. Kinnan Statistics

Kinnan専用統計。

Cast Turn

Average Cast Turn

Activation Count

Average Activation Count

Mana Generated

Trigger Count

Extra Mana

Copies

---

# 8. Trigger Statistics

Trigger数

Resolve数

Miss数

Extra Trigger数

Average Trigger / Turn

---

# 9. Combo Statistics

Combo Name

Pieces

Start Turn

Completion Turn

Succeeded

Failed

Failure Reason

Loop Count

Generated Mana

---

# 10. Chain Statistics

Chain ID

Starting Turn

Activation Count

Cards Hit

Cards Missed

Maximum Depth

Ending Reason

Generated Mana

---

# 11. Tutor Statistics

Tutor Name

Target Card

Success

Cast Turn

Cards Searched

---

# 12. Mulligan Statistics

Starting Hand

London Mulligan Count

Bottom Cards

Keep Turn

---

# 13. AI Statistics

Strategy

Chosen Action

Candidate Count

Evaluation Score

Decision Time

Search Depth

---

# 14. Performance Statistics

Simulation Time

Average Game Time

Peak Memory

CPU Time

Games Per Second

---

# 15. Deck Statistics

Deck Name

Commander

Card Count

Creature Count

Land Count

Artifact Count

Instant Count

Sorcery Count

Enchantment Count

Average Mana Value

---

# 16. Comparison Statistics

複数デッキ比較用。

Average Mana

Average Combo Turn

Average Chain

Average Kinnan Turn

Average Win Turn

Hit Rate

Combo Rate

---

# 17. Export

CSV

Excel

JSON

SQLite

HTML

---

# 18. グラフ

Turn vs Mana

Turn vs Battlefield

Turn vs Hand

Combo Distribution

Chain Distribution

Activation Distribution

---

# 19. Version2以降

Heatmap

Timeline

Card Network

AI Comparison

Strategy Comparison

---

# 20. 成功条件

以下を満たすこと。

・1ゲーム単位で統計を保存できる

・ターン単位で統計を保存できる

・カード単位で統計を保存できる

・CSVへ出力できる

・Excelへ出力できる

・比較レポートを生成できる