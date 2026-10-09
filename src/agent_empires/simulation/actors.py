"""Actor identity used by holdings; kinds confer no knowledge or authority."""

from dataclasses import dataclass


def require_text(value: str, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must be nonempty")


@dataclass(frozen=True, slots=True)
class Actor:
    """Minimal roster entry, not a role, function or capability profile."""

    actor_id: str
    kind: str
    team_id: str

    def __post_init__(self) -> None:
        for field in ("actor_id", "kind", "team_id"):
            require_text(getattr(self, field), field)
        if self.kind not in ("human", "agent"):
            raise ValueError("actor kind must be human or agent")
