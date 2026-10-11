"""ALUCLU public exports, resolved lazily without importing computational dependencies.

Dependency errors propagate when an export is requested. Star imports intentionally
resolve the complete public API. Direct submodule imports use normal importlib semantics.
"""

from importlib import import_module as _import_module

__version__ = "0.1.0"

_EXPORTS = {
    "AppendOutcome": ("aluclu.cognition", "AppendOutcome"),
    "CognitionError": ("aluclu.cognition", "CognitionError"),
    "EncryptedLedger": ("aluclu.cognition", "EncryptedLedger"),
    "InputBoundaryError": ("aluclu.cognition", "InputBoundaryError"),
    "LedgerCursorCheckpoint": ("aluclu.cognition", "LedgerCursorCheckpoint"),
    "LedgerRecord": ("aluclu.cognition", "LedgerRecord"),
    "LedgerSecurityScope": ("aluclu.cognition", "LedgerSecurityScope"),
    "SafeStateCodec": ("aluclu.cognition", "SafeStateCodec"),
    "StateIntegrityError": ("aluclu.cognition", "StateIntegrityError"),
    "VerifiedLedgerCursor": ("aluclu.cognition", "VerifiedLedgerCursor"),
    "VerifiedLedgerSession": ("aluclu.cognition", "VerifiedLedgerSession"),
    "canonical_json_bytes": ("aluclu.cognition", "canonical_json_bytes"),
    "strict_json_loads": ("aluclu.cognition", "strict_json_loads"),
    "validate_event_id": ("aluclu.cognition", "validate_event_id"),
    "compress_slot": ("aluclu.compression", "compress_slot"),
    "factor_matrix": ("aluclu.compression", "factor_matrix"),
    "truncate_factors": ("aluclu.compression", "truncate_factors"),
    "truncate_factors_with_error": (
        "aluclu.compression",
        "truncate_factors_with_error",
    ),
    "AlucluConfig": ("aluclu.config", "AlucluConfig"),
    "EpisodicMemoryConfig": ("aluclu.config", "EpisodicMemoryConfig"),
    "ExactCacheConfig": ("aluclu.config", "ExactCacheConfig"),
    "GatedDeltaConfig": ("aluclu.config", "GatedDeltaConfig"),
    "BoundedEpisodicMemory": ("aluclu.episodic", "BoundedEpisodicMemory"),
    "MassConservingRouter": ("aluclu.episodic", "MassConservingRouter"),
    "ResidualSurpriseCache": ("aluclu.exact_cache", "ResidualSurpriseCache"),
    "GatedDeltaRule2": ("aluclu.gated_delta", "GatedDeltaRule2"),
    "BoundedLocalAttention": ("aluclu.local_attention", "BoundedLocalAttention"),
    "parameter_count": ("aluclu.metrics", "parameter_count"),
    "tensor_tree_bytes": ("aluclu.metrics", "tensor_tree_bytes"),
    "AlucluBlock": ("aluclu.model", "AlucluBlock"),
    "AlucluLanguageModel": ("aluclu.model", "AlucluLanguageModel"),
    "AlucluLanguageModelOutput": ("aluclu.model", "AlucluLanguageModelOutput"),
    "MQARBatch": ("aluclu.mqar", "MQARBatch"),
    "generate_mqar_batch": ("aluclu.mqar", "generate_mqar_batch"),
    "mqar_accuracy": ("aluclu.mqar", "mqar_accuracy"),
    "build_research_config": ("aluclu.presets", "build_research_config"),
    "TensorSketch": ("aluclu.sketch", "TensorSketch"),
    "AlucluBlockState": ("aluclu.state", "AlucluBlockState"),
    "AlucluModelState": ("aluclu.state", "AlucluModelState"),
    "EpisodicState": ("aluclu.state", "EpisodicState"),
    "ExactCacheState": ("aluclu.state", "ExactCacheState"),
    "GatedDeltaState": ("aluclu.state", "GatedDeltaState"),
    "LocalAttentionState": ("aluclu.state", "LocalAttentionState"),
    "MemorySlot": ("aluclu.state", "MemorySlot"),
    "ZOOLOGY_ICLR24_COMMIT": ("aluclu.zoology_mqar", "ZOOLOGY_ICLR24_COMMIT"),
    "ZOOLOGY_ICLR24_RAW_PROTOCOL_ID": (
        "aluclu.zoology_mqar",
        "ZOOLOGY_ICLR24_RAW_PROTOCOL_ID",
    ),
    "ZOOLOGY_ICLR24_REPAIRED_PROTOCOL_ID": (
        "aluclu.zoology_mqar",
        "ZOOLOGY_ICLR24_REPAIRED_PROTOCOL_ID",
    ),
    "ZOOLOGY_MQAR_IGNORE_INDEX": ("aluclu.zoology_mqar", "ZOOLOGY_MQAR_IGNORE_INDEX"),
    "ZoologyMQARBatch": ("aluclu.zoology_mqar", "ZoologyMQARBatch"),
    "ZoologyMQARConfig": ("aluclu.zoology_mqar", "ZoologyMQARConfig"),
    "generate_zoology_mqar_batch": (
        "aluclu.zoology_mqar",
        "generate_zoology_mqar_batch",
    ),
    "zoology_mqar_accuracy": ("aluclu.zoology_mqar", "zoology_mqar_accuracy"),
    "zoology_mqar_loss": ("aluclu.zoology_mqar", "zoology_mqar_loss"),
}

__all__ = [
    "ZOOLOGY_ICLR24_COMMIT",
    "ZOOLOGY_ICLR24_RAW_PROTOCOL_ID",
    "ZOOLOGY_ICLR24_REPAIRED_PROTOCOL_ID",
    "ZOOLOGY_MQAR_IGNORE_INDEX",
    "AlucluBlock",
    "AlucluBlockState",
    "AlucluConfig",
    "AlucluLanguageModel",
    "AlucluLanguageModelOutput",
    "AlucluModelState",
    "AppendOutcome",
    "BoundedEpisodicMemory",
    "BoundedLocalAttention",
    "CognitionError",
    "EncryptedLedger",
    "EpisodicMemoryConfig",
    "EpisodicState",
    "ExactCacheConfig",
    "ExactCacheState",
    "GatedDeltaConfig",
    "GatedDeltaRule2",
    "GatedDeltaState",
    "InputBoundaryError",
    "LedgerCursorCheckpoint",
    "LedgerRecord",
    "LedgerSecurityScope",
    "LocalAttentionState",
    "MQARBatch",
    "MassConservingRouter",
    "MemorySlot",
    "ResidualSurpriseCache",
    "SafeStateCodec",
    "StateIntegrityError",
    "TensorSketch",
    "VerifiedLedgerCursor",
    "VerifiedLedgerSession",
    "ZoologyMQARBatch",
    "ZoologyMQARConfig",
    "__version__",
    "build_research_config",
    "canonical_json_bytes",
    "compress_slot",
    "factor_matrix",
    "generate_mqar_batch",
    "generate_zoology_mqar_batch",
    "mqar_accuracy",
    "parameter_count",
    "strict_json_loads",
    "tensor_tree_bytes",
    "truncate_factors",
    "truncate_factors_with_error",
    "validate_event_id",
    "zoology_mqar_accuracy",
    "zoology_mqar_loss",
]


def __getattr__(name: str):
    try:
        module_name, symbol_name = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(_import_module(module_name), symbol_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
