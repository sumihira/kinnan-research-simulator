from krs.actions.cast_commander import CastCommanderAction
from krs.cards.card import Card
from krs.mana.mana_cost import ManaCost
from krs.abilities.static import StaticAbility

def create_kinnan() -> Card:
    return Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power="2",
        toughness="2",
    )


def test_cast_commander_action_stores_card_and_base_cost() -> None:
    kinnan = create_kinnan()
    cost = ManaCost(
        green=1,
        blue=1,
    )

    action = CastCommanderAction(
        player_id=0,
        turn_number=1,
        card=kinnan,
        base_cost=cost,
    )

    assert action.card is kinnan
    assert action.base_cost == cost