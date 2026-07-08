# 05_Combo.md

Version: 1.0 Draft

---

# 1. 目的

本仕様書では、Kinnan Research Simulator（KRS）における
コンボ判定・コンボ解析・チェイン解析の仕様を定義する。

本システムは

・無限コンボ判定
・有限コンボ判定
・Kinnan Chain
・Tutor Chain

を統一的に扱う。

---

# 2. 基本方針

コンボとは

「あるゲーム状態から期待値を大きく向上させる一連のAction」

と定義する。

Version1では

カード名ではなく

GameState

によって判定する。

---

# 3. Combo Engine

構成

Combo Detector

Combo Resolver

Chain Resolver

Loop Detector

Statistics Collector

Replay Logger

---

# 4. Combo

Comboは以下を持つ。

Combo ID

Name

Description

Required State

Required Cards

Current Progress

Completed

---

# 5. Combo State

状態

Not Started

Preparing

Active

Infinite

Finished

Failed

---

# 6. Combo Detector

毎Action終了後に実行する。

役割

コンボ開始

コンボ進行

コンボ終了

を判定する。

---

# 7. Combo Resolver

現在のGameStateから

実行可能なコンボActionを列挙する。

Version1では

Rule Based。

---

# 8. Chain

Chainとは

Kinnan起動を起点とする連続した価値獲得を指す。

Chain開始

↓

Hit

↓

追加マナ

↓

再起動

↓

Hit

↓

・・・

↓

終了

---

# 9. Chain終了条件

以下のいずれか。

起動不可

ヒットなし

色マナ不足

ライブラリー不足

コンボ終了

ゲーム終了

---

# 10. Infinite Combo

Infinite判定条件

状態が以前と等価

かつ

正の利益がある

場合

Infiniteと判定する。

---

# 11. Loop

Loopとは

同一Stateへ戻るAction列である。

Loopには

Loop Count

Loop Gain

を保持する。

---

# 12. Combo Progress

途中状態を保持する。

例

Pieces Collected

Current Mana

Current Board

Current Chain

---

# 13. Combo Priority

AIが複数コンボを持つ場合

Priorityを比較する。

Version1では

固定順位。

---

# 14. Combo Statistics

記録項目

Combo Name

Turn

Pieces

Mana

Actions

Loop Count

Result

Failure Reason

---

# 15. Combo Graph

コンボは

有向グラフ

として管理する。

Node

GameState

Edge

Action

---

# 16. Replay

Replayでは

Combo Start

Combo Progress

Combo End

を保存する。

---

# 17. Version1対象コンボ

Basalt Monolith

Grim Monolith

Deadeye Navigator

Palinchron

Great Whale

Peregrine Drake

Astral Dragon

Machine God's Effigy

Spark Double

Roaming Throne

---

# 18. Version2

Tutor Chain

Priority Change

Multi Combo

Stack Combo

---

# 19. Version3

自動コンボ発見

Expected Value Search

---

# 20. 成功条件

・コンボ開始を検出できる

・途中経過を保持できる

・終了理由を保持できる

・Replayできる

・統計へ保存できる