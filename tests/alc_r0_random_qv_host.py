"""Bounded random CPU test host; fabricated metadata is NOT authentication.

Real Transformers forward/decoder/cache code, random weights and a thin MLP.
Only attention geometry matches the pinned host:30 blocks, width576, q576/v192.
Embedding1024, MLP64 and a rank16 factorized49152-output head are TEST deviations.
No pretrained asset/tokenizer/data load, CUDA, training or launch admission.
"""

from contextlib import contextmanager

import torch
from torch import nn
from transformers import LlamaConfig, LlamaForCausalLM

from aluclu.alc_r0.host import SMOLLM2_135M_CONFIG, VerifiedHost


@contextmanager
def random_cpu_host():
    """Serial fake-test owner; restore CPU RNG and thread count on all exits.

    Caller/launcher must check operational headroom before importing this test.
    This is not a memory reservation or actual-host resource qualification.
    Never use the fabricated VerifiedHost outside these test fixtures.
    """
    if (
        torch.get_default_device() != torch.device("cpu")
        or torch.get_default_dtype() != torch.float32
    ):
        raise ValueError("explicit CPU FP32 fake test context required")
    previous_threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        with torch.random.fork_rng(devices=[]):
            # torch.manual_seed also seeds CUDA/MPS; this fixture must alter
            # only the CPU generator covered by fork_rng(devices=[]).
            torch.random.default_generator.manual_seed(20261006)
            config = LlamaConfig(
                vocab_size=1024,
                hidden_size=576,
                intermediate_size=64,
                num_hidden_layers=30,
                num_attention_heads=9,
                num_key_value_heads=3,
                head_dim=64,
                max_position_embeddings=8192,
                bos_token_id=0,
                eos_token_id=0,
                tie_word_embeddings=False,
                attention_dropout=0.0,
            )
            config._attn_implementation = "eager"
            # Constructor-only random initialization; NEVER from_pretrained.
            base = LlamaForCausalLM(config)
            base.lm_head = nn.Sequential(
                nn.Linear(576, 16, bias=False),
                nn.Linear(16, 49152, bias=False),
            )
            config.vocab_size = base.vocab_size = 49152
            base.requires_grad_(False).eval()
        parameter_count = sum(p.numel() for p in base.parameters())
        if parameter_count != 31280448:
            raise ValueError("random test network parameter geometry changed")
        result = VerifiedHost(
            base,
            {"test_only_random_thin_mlp": True, "asset_authentication": False},
            # Constructor metadata is fabricated ONLY for test wiring; the
            # actual config above deliberately differs from SmolLM2 assets.
            SMOLLM2_135M_CONFIG.as_dict(),
            parameter_count,
            0,
        )
        yield result
    finally:
        torch.set_num_threads(previous_threads)
