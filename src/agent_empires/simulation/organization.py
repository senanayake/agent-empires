"""Explicit roles and function coverage over the live knowledge roster.

Coverage is an assignment, not proof of capability, knowledge or a graph path.
Replacement removes the old actor's memberships/access and assignments. It
preserves prepared replacement state but copies nothing from the departing actor.
Application coordinates authority, channels and delivery via their public APIs.
"""
from .actors import Actor, require_text
from .events import CausalLink, EntityRef, Event, EventHistory
from .knowledge import KnowledgeStore


class Organization:
    def __init__(self, store: KnowledgeStore, history: EventHistory, *,
                 roles: dict[str, str], functions: dict[str, tuple[str, ...]]) -> None:
        for actor_id, role in roles.items():
            store.actor_for(actor_id)
            require_text(role, 'role')
        for function_id, holders in functions.items():
            require_text(function_id, 'function_id')
            if type(holders) is not tuple or len(set(holders)) != len(holders):
                raise ValueError('function holders must be a unique immutable tuple')
            for actor_id in holders:
                store.actor_for(actor_id)
        self._store, self._history = store, history
        self._roles = dict(roles)
        self._functions = dict(functions)

    def members(self, team_id: str) -> tuple[str, ...]:
        return tuple(a.actor_id for a in self._store.actors
                     if a.team_id == team_id and self._store.is_present(a.actor_id))

    def role_for(self, actor_id: str) -> str | None:
        return self._roles.get(actor_id) if self._store.is_present(actor_id) else None

    def function_holders(self, function_id: str) -> tuple[str, ...]:
        if function_id not in self._functions:
            raise ValueError('unknown organizational function')
        return tuple(sorted(a for a in self._functions[function_id] if self._store.is_present(a)))

    @property
    def uncovered_functions(self) -> tuple[str, ...]:
        return tuple(sorted(f for f in self._functions if not self.function_holders(f)))

    def assign_function(self, function_id: str, actor_id: str, *, tick: int,
                        command_id: str, correlation_id: str) -> Event:
        holders = self.function_holders(function_id)
        if not self._store.is_present(actor_id):
            raise ValueError('function requires a present actor')
        if actor_id in holders:
            raise ValueError('function already assigned to actor')
        event = self._history.append(
            tick=tick, event_type='FunctionAssigned', command_id=command_id,
            correlation_id=correlation_id,
            entities=(EntityRef('organizational_function', function_id, 1), EntityRef('actor', actor_id, 1)),
            payload={'function_id': function_id, 'actor_id': actor_id},
        )
        self._functions[function_id] += (actor_id,)
        return event

    def register_actor(self, actor: Actor, *, role: str, tick: int,
                       command_id: str, correlation_id: str) -> Event:
        require_text(role, 'role')
        event = self._store.register_actor(actor, tick=tick, command_id=command_id,
                                            correlation_id=correlation_id)
        self._roles[actor.actor_id] = role
        return event

    def validate_replacement(self, actor_id: str, replacement: Actor, role: str) -> None:
        require_text(role, 'role')
        if type(replacement) is not Actor:
            raise TypeError('expected replacement Actor')
        if not self._store.is_present(actor_id):
            raise ValueError('replacement requires a present departing actor')
        if actor_id == replacement.actor_id:
            raise ValueError('replacement requires a distinct identity')
        known = next((a for a in self._store.actors if a.actor_id == replacement.actor_id), None)
        if known is not None:
            if known != replacement or not self._store.is_present(known.actor_id):
                raise ValueError('replacement conflicts with a registered or departed identity')
        else:
            self._store.validate_registration(replacement)

    def replace_actor(self, actor_id: str, replacement: Actor, *, role: str, tick: int,
                      command_id: str, correlation_id: str) -> tuple[Event, ...]:
        """Replace with a new or explicitly prepared present actor.

        Preflight precedes the first fact; subsequent writes use validated data.
        An existing prepared actor keeps only its own holdings and functions.
        No role or team of the departing actor is implicitly copied.
        """
        self.validate_replacement(actor_id, replacement, role)
        removed = sorted(f for f, holders in self._functions.items() if actor_id in holders)
        root = self._history.append(
            tick=tick, event_type='ActorReplaced', command_id=command_id,
            correlation_id=correlation_id,
            entities=(EntityRef('actor', actor_id, 1), EntityRef('actor', replacement.actor_id, 1)),
            payload={'departing_actor': actor_id, 'replacement_actor': replacement.actor_id,
                     'removed_team_membership': self._store.actor_for(actor_id).team_id,
                     'removed_role': self._roles.get(actor_id), 'assigned_role': role,
                     'removed_functions': removed},
        )
        parents = (CausalLink(root.event_id, 'direct_cause'),)
        events = [root]
        if not any(a.actor_id == replacement.actor_id for a in self._store.actors):
            events.append(self._store.register_actor(replacement, tick=tick,
                command_id=command_id + '.register', correlation_id=correlation_id, parents=parents))
        events.extend(self._store.depart_actor(actor_id, tick=tick, command_id=command_id + '.depart',
                                               correlation_id=correlation_id, parents=parents))
        self._roles.pop(actor_id, None)
        self._roles[replacement.actor_id] = role
        for function_id in removed:
            self._functions[function_id] = tuple(a for a in self._functions[function_id] if a != actor_id)
        return tuple(events)
