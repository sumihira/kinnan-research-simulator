# 06_MonteCarlo.md

Version: 1.0 Draft

---

# 1. 目的

本仕様書では、Kinnan Research Simulator（KRS）における
Monte Carlo Simulation Framework を定義する。

本システムの目的は大量のGoldfishシミュレーションを実行し、
統計的に有意なデータを収集・比較することである。

---

# 2. 基本方針

Monte Carlo Engine は

「ゲーム」

ではなく

「Experiment」

を実行する。

最上位単位は Experiment とする。

---

# 3. Experiment

Experiment は1つの研究条件を表す。

保持する情報

- Experiment ID
- Experiment Name
- Deck
- Strategy
- Preset
- Seed
- Number of Games
- Git Commit
- Start Time
- End Time

---

# 4. Experiment Lifecycle

Experimentは以下の状態を持つ。

Created

↓

Running

↓

Completed

または

↓

Failed

または

↓

Cancelled

---

# 5. ExperimentManager

Experiment全体を管理する。

責務

- Experiment開始
- Worker生成
- Seed管理
- Progress管理
- Resume
- Statistics集約
- Report生成

---

# 6. SimulationRunner

1ゲームを実行する。

責務

- GameState生成
- Game Engine実行
- AI実行
- Statistics取得
- Replay生成

Game終了後、結果をExperimentManagerへ返却する。

---

# 7. Worker

WorkerはSimulationRunnerを繰り返し実行する。

Version1では

1 Worker = 1 CPU Thread

とする。

---

# 8. Parallel Execution

複数Workerによる並列実行を行う。

各Workerは独立した乱数を使用する。

Worker間でGameStateを共有しない。

---

# 9. Random Seed

SeedはExperiment単位で管理する。

各GameのSeedは

Experiment Seed

+

Game ID

から生成する。

同じSeedでは完全再現できること。

---

# 10. ResultAggregator

全Game終了後に統計を集約する。

対象

- Mana
- Combo
- Chain
- AI
- Card
- Turn

---

# 11. Progress

進捗管理を行う。

表示例

Games

10000 / 100000

Progress

10%

ETA

12m34s

---

# 12. Resume

途中停止したExperimentは再開可能とする。

Resume時は

- 完了済Game
- Seed
- Statistics

を復元する。

---

# 13. Error Handling

Game単位の例外はExperimentを停止させない。

失敗GameはErrorとして記録し、

次Gameを続行する。

---

# 14. ExperimentResult

Experiment終了時に生成する。

保持する情報

- Summary
- Statistics
- Logs
- Replay
- Artifacts
├── CSV
├── Excel
├── HTML
└── Graphs

---

# 15. 保存先

Experiment結果は

experiments/

配下へ保存する。

例

experiments/

└── YYYYMMDD_HHMMSS_CurrentList/

    ├── config/
    ├── logs/
    ├── replay/
    ├── reports/
    ├── statistics/
    └── metadata.json

---

# 16. Performance

Version1目標

100,000ゲーム

数十分以内

メモリリークなし

再現性100%

---

# 17. 将来拡張

- 分散実行
- GPU利用
- クラウド実行
- 実験キュー
- Web Dashboard

---

# 18. テスト方針

以下をテストする。

- Seed再現性
- 並列実行
- Resume
- Aggregator
- Error Recovery

---

# 19. 設計原則

ExperimentはGameを変更しない。

GameはExperimentを知らない。

SimulationRunnerは1Gameのみ担当する。

Workerは独立して動作する。

---

# 20. Version1完成条件

以下を満たす。

・Experimentを開始できる

・複数Gameを実行できる

・並列実行できる

・再現可能である

・統計を集約できる

・実験結果をexperiments/へ保存できる