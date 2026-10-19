"""Read-only complete q/v optimizer fidelity for cooperating quiescent callers.

Uses the fixed Torch2.14 synthetic step1/2 contract. This does not step, restore,
serialize or prove execution of an optimizer. Host/base byte identity, unchanged
mount placement, launch authority and learning acceptance remain separate gates.
ReferenceArtifactError reports binding errors; CheckpointFidelityError reports
optimizer schema/state/comparison errors. Callers exclusively own mutable state.
"""

from .checkpoint_optimizer import compare_adamw_states
from .reference_qv_artifact import reference_bindings


def compare_reference_optimizer_states(
    reference_wrapper,
    reference_optimizer,
    actual_wrapper,
    actual_optimizer,
    *,
    expected_step,
    exact,
):
    """Derive complete validated q/v bindings, then compare all factors/moments.

    CPU parity callers must supply exact=True. Synthetic state equality does not
    authenticate provenance or demonstrate that any training update occurred.
    """
    reference_factors, reference_base = reference_bindings(reference_wrapper)
    actual_factors, actual_base = reference_bindings(actual_wrapper)
    return compare_adamw_states(
        reference_optimizer,
        actual_optimizer,
        reference_factors,
        actual_factors,
        reference_base_parameters=reference_base,
        actual_base_parameters=actual_base,
        expected_step=expected_step,
        exact=exact,
    )
