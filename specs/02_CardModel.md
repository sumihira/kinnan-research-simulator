# 02_CardModel.md

Version: 1.0 Draft

---

# 1. 目的

本仕様書では、Kinnan Research Simulator（KRS）における
カードおよびゲームオブジェクトのデータモデルを定義する。

本仕様は

- ゲームエンジン
- プレイAI
- Monte Carlo
- Replay
- Logging

全ての基盤となる。

---

# 2. 設計方針

Cardはゲーム内で最も基本となるオブジェクトである。

カード自身は状態を持たず、
ゲーム中の状態はPermanentが保持する。

つまり

Card = 印刷されている情報

Permanent = 戦場での状態

とする。

---

# 3. オブジェクト構成

Game
└── Player
　　　├── Library
　　　├── Hand
　　　├── Battlefield
　　　├── Graveyard
　　　├── Exile
　　　└── Command Zone
Battlefield
└── Permanent
　　　└── Card
　　　　　　└── Ability

---

# 4. Card

Cardは印刷情報を保持する。

## プロパティ

id
oracle_id
name
mana_cost
mana_value
colors
color_identity
types
subtypes
supertypes
oracle_text
keywords
power
toughness
loyalty
defense
layout
set_code
collector_number
rarity
artist
image_url
scryfall_uri

---

Cardはゲーム中に変更されない。

Immutableとする。

---

# 5. Permanent

Permanentは戦場上の状態を保持する。

## プロパティ

card
controller
owner
zone
tapped
summoning_sick
is_token
is_copy
copy_source
counters
damage
chosen_values
timestamp
continuous_effects

---

Permanentのみゲーム中に状態変化する。

---

# 6. Ability

Abilityはカード能力を表す。

種類
Activated
Triggered
Static
Mana
Replacement
ETB
LTB

---

共通プロパティ
id
name
oracle_text
ability_type
source

---

# 7. ManaCost

ManaCostは支払いコストを表す。

保持情報
Generic
White
Blue
Black
Red
Green
Colorless
Phyrexian
Hybrid
Snow
X

---

API
can_pay()
pay()
copy()

---

# 8. ManaPool

ManaPoolは現在保持しているマナ。

保持情報
W
U
B
R
G
C

---

API
add()
remove()
clear()
can_pay()
copy()

---

# 9. Zone

全ての領域はZoneを継承する。
種類
Library
Hand
Battlefield
Graveyard
Exile
Stack
CommandZone

---

共通API
add()
remove()
shuffle()
move()
contains()

---

# 10. Player

Playerはプレイヤー情報を保持する。
保持情報
id
name
library
hand
battlefield
graveyard
exile
command_zone
mana_pool
land_play_count
commander_cast_count

---

Version1では

対戦相手は存在しない。

Playerは1人のみ。

---

# 11. GameState

ゲーム全体を保持する。
保持情報
turn
active_player
phase
priority
stack
random_seed
game_id
log
statistics

---

GameStateはゲーム全体の唯一の状態管理クラスとする。

---

# 12. Action

AIが選択可能な行動。
種類
Draw
PlayLand
CastSpell
ActivateAbility
PassPriority
ResolveTrigger
ResolveSpell

---

Actionは評価可能である。

---

# 13. Trigger

Triggerは待機中の誘発。
保持情報
source
condition
effect
controller
timestamp
resolved

---

# 14. Effect

Effectは実際のゲーム処理。

例
AddMana
DrawCard
Untap
Tap
CreateToken
CopyPermanent
SearchLibrary
Shuffle
ReturnPermanent

---

AbilityはEffectを実行する。

---

# 15. Card Database

全カードはCardDatabaseが保持する。
責務
Scryfall取得
ローカルキャッシュ
Oracle更新
検索
ID管理

---

# 16. Replay

Replayでは
Action
GameState
Random Seed
Log
を保存する。

Replayからゲームを完全再現できること。

---

# 17. 設計原則

CardはImmutable

GameStateのみゲーム全体を管理する

Permanentのみ状態変化する

AbilityはEffectのみ呼び出す

AIはGameStateのみ参照する

---

# 18. クラス依存図

Game
↓
GameState
↓
Player
↓
Zone
↓
Permanent
↓
Card
↓
Ability
↓
Effect

---

# 19. Version2以降

今後追加予定
Battle
Planeswalker
Emblem
Sticker
Attraction
Dungeon
Initiative
Energy
Experience Counter
Poison

---

# 20. 成功条件

以下を満たすこと。
・Cardを生成できる
・Permanentを生成できる
・GameStateを生成できる
・Playerを生成できる
・ManaPoolを操作できる
・Replayへ保存できる
・AIがGameStateのみで判断できる