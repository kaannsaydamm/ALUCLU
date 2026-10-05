"""Pure bounded E3 token schedule, never tokenizer provenance or launch authority.

No direct Torch calls, assets, files, tokenizer or execution. Existing package
initialization imports Torch; this module never allocates tensors or launches it.
D ParityInput remains unchanged.
Caller supplies separately authenticated framing/candidates for vocab49152/EOS0.
"""

import hashlib
from dataclasses import asdict, dataclass

from .canonical import canonical_json_bytes


class StressInputError(ValueError):
    """The separate fixed E3 schedule is malformed or differs."""


@dataclass(frozen=True)
class StressInput:
    label: str
    input_ids: tuple[int, ...]
    attention_mask: tuple[int, ...]
    labels: tuple[int, ...]
    position_ids: tuple[int, ...]
    prompt_length: int
    candidate_ids: tuple[int, ...]


@dataclass(frozen=True)
class StressSchedule:
    prefix_ids: tuple[int, ...]
    suffix_ids: tuple[int, ...]
    safe_ids: tuple[int, ...]
    vulnerable_ids: tuple[int, ...]
    inputs: tuple[StressInput, ...]


def _tokens(value):
    if (
        type(value) is not tuple
        or not 1 <= len(value) <= 64
        or any(type(token) is not int or not 1 <= token < 49152 for token in value)
    ):
        raise StressInputError(
            "nonempty bounded exact token tuple, vocab49152/EOS0 required"
        )
    return value


def build_stress_schedule(*, prefix_ids, suffix_ids, safe_ids, vulnerable_ids):
    """Exactly16 safe-first alternating inputs; reuse for BOTH future updates."""
    prefix, suffix, safe, vulnerable = map(
        _tokens, (prefix_ids, suffix_ids, safe_ids, vulnerable_ids)
    )
    if safe == vulnerable:
        raise StressInputError("distinct complete candidates required")
    reserve = max(len(safe), len(vulnerable))
    code_length = 4096 - len(prefix) - len(suffix) - reserve
    if code_length < 1:
        raise StressInputError("longest-candidate reserve leaves no synthetic code")
    code = tuple((index + 1) % 49151 + 1 for index in range(code_length))
    prompt = prefix + code + suffix
    pair = tuple(
        StressInput(
            label=label,
            input_ids=prompt + candidate,
            attention_mask=(1,) * (len(prompt) + len(candidate)),
            labels=(-100,) * len(prompt) + candidate,
            position_ids=tuple(range(len(prompt) + len(candidate))),
            prompt_length=len(prompt),
            candidate_ids=candidate,
        )
        for label, candidate in (("safe", safe), ("vulnerable", vulnerable))
    )
    return StressSchedule(prefix, suffix, safe, vulnerable, pair * 8)


def validate_stress_schedule(schedule):
    """Check exact bounded types before rebuilding the fixed expected schedule."""
    if type(schedule) is not StressSchedule:
        raise StressInputError("exact immutable StressSchedule required")
    framing = (
        schedule.prefix_ids,
        schedule.suffix_ids,
        schedule.safe_ids,
        schedule.vulnerable_ids,
    )
    for value in framing:
        _tokens(value)
    if type(schedule.inputs) is not tuple or len(schedule.inputs) != 16:
        raise StressInputError("exact16 immutable stress inputs required")
    for item in schedule.inputs:
        if (
            type(item) is not StressInput
            or type(item.label) is not str
            or item.label not in ("safe", "vulnerable")
            or type(item.prompt_length) is not int
            or not 1 <= item.prompt_length < 4096
        ):
            raise StressInputError("exact typed bounded stress input required")
        _tokens(item.candidate_ids)
        for name in ("input_ids", "attention_mask", "labels", "position_ids"):
            value = getattr(item, name)
            if (
                type(value) is not tuple
                or not 1 <= len(value) <= 4096
                or any(type(token) is not int for token in value)
            ):
                raise StressInputError(
                    "bounded exact immutable integer arrays required"
                )
    expected = build_stress_schedule(
        prefix_ids=framing[0],
        suffix_ids=framing[1],
        safe_ids=framing[2],
        vulnerable_ids=framing[3],
    )
    if schedule != expected:
        raise StressInputError("fixed4096 reserve/framing/supervision/order differs")


def stress_schedule_sha256(schedule):
    """Consistency digest only; cannot attest tokenizer/host or authorize execution."""
    validate_stress_schedule(schedule)
    payload = {
        "schema_id": "aluclu/alc-r0/e3-stress-inputs/v1",
        "common_length": 4096,
        "updates": 2,
        "microbatches_per_update": 16,
        "vocab_size": 49152,
        "eos_token_id": 0,
        "schedule": asdict(schedule),
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
