"""Token-only fixtures for prospective D parity, never launch authorization.

The runner must supply independently verified tokenizer framing/candidates.
This helper neither tokenizes nor authenticates those IDs or loads a host.
"""

from dataclasses import dataclass


class ParityInputError(ValueError):
    """A prospective synthetic parity fixture violates the fixed D contract."""


@dataclass(frozen=True)
class ParityInput:
    input_ids: tuple[int, ...]
    attention_mask: tuple[int, ...]
    labels: tuple[int, ...]
    position_ids: tuple[int, ...]
    prompt_length: int
    candidate_ids: tuple[int, ...]


def _tokens(value, eos_token_id):
    if type(value) is not tuple or not 1 <= len(value) <= 64:
        raise ParityInputError("nonempty bounded immutable token tuple required")
    if any(type(token) is not int or not 0 <= token < 49152 for token in value):
        raise ParityInputError("pinned vocabulary token IDs required")
    if eos_token_id in value:
        raise ParityInputError("framing/candidate EOS forbidden")
    return value


def parity_input(
    *,
    prefix_ids,
    suffix_ids,
    safe_ids,
    vulnerable_ids,
    eos_token_id,
    common_length,
    label,
    padded=False,
):
    if type(common_length) is not int or common_length not in (32, 64):
        raise ParityInputError("D requires common length32 or64")
    if type(padded) is not bool or (padded and common_length != 64):
        raise ParityInputError("right padding is bool and64-only")
    if type(label) is not str or label not in ("safe", "vulnerable"):
        raise ParityInputError("fixed complete candidate label required")
    if type(eos_token_id) is not int or not 0 <= eos_token_id < 49152:
        raise ParityInputError("pinned vocabulary EOS required")
    prefix = _tokens(prefix_ids, eos_token_id)
    suffix = _tokens(suffix_ids, eos_token_id)
    safe = _tokens(safe_ids, eos_token_id)
    vulnerable = _tokens(vulnerable_ids, eos_token_id)
    if safe == vulnerable:
        raise ParityInputError("distinct complete candidates required")
    reserve = max(len(safe), len(vulnerable))
    code_length = common_length - len(prefix) - len(suffix) - reserve
    if code_length < 1:
        raise ParityInputError("no synthetic code fits after longest candidate reserve")
    code = tuple((index + 1) % 49151 + 1 for index in range(code_length))
    prompt = prefix + code + suffix
    candidate = safe if label == "safe" else vulnerable
    sequence = prompt + candidate
    padding = 7 if padded else 0
    input_ids = sequence + (eos_token_id,) * padding
    # Labels remain unshifted: the actual host loss owns the next-token shift.
    return ParityInput(
        input_ids=input_ids,
        attention_mask=(1,) * len(sequence) + (0,) * padding,
        labels=(-100,) * len(prompt) + candidate + (-100,) * padding,
        position_ids=tuple(range(len(input_ids))),
        prompt_length=len(prompt),
        candidate_ids=candidate,
    )
