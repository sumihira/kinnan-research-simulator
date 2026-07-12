from krs.engine.action_executor import ActionExecutor
from krs.ai.kinnan_hit_selector import KinnanHitSelector

def __init__(
    self,
    action_executor: ActionExecutor | None = None,
    kinnan_hit_selector: KinnanHitSelector | None = None,
) -> None:
    self._action_executor = (
        action_executor or ActionExecutor()
    )
    self._kinnan_hit_selector = (
        kinnan_hit_selector or KinnanHitSelector()
    )