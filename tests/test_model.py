import torch

from aluclu import (
    AlucluConfig,
    AlucluLanguageModel,
    EpisodicMemoryConfig,
    ExactCacheConfig,
    GatedDeltaConfig,
    generate_mqar_batch,
    mqar_accuracy,
)


def model_config() -> AlucluConfig:
    episodic = EpisodicMemoryConfig(
        d_model=8,
        segment_size=2,
        live_segments=1,
        archive_slots=1,
        archive_segments_per_slot=2,
        archive_rank=2,
        router_dim=4,
        router_degree=3,
        sketch_dim=8,
        n_sketches=3,
    )
    delta = GatedDeltaConfig(
        d_model=8,
        n_heads=2,
        head_key_dim=4,
        head_value_dim=4,
    )
    return AlucluConfig(
        d_model=8,
        n_layers=2,
        ffn_multiplier=2,
        local_window=5,
        local_heads=2,
        local_attention_every=1,
        episodic_every=2,
        exact_cache_every=2,
        gated_delta=delta,
        episodic=episodic,
        exact_cache=ExactCacheConfig(
            d_model=8,
            n_heads=2,
            capacity=4,
        ),
    )


def test_aluclu_chunking_matches_single_forward() -> None:
    torch.manual_seed(30)
    model = AlucluLanguageModel(32, model_config()).eval()
    input_ids = torch.randint(0, 32, (2, 13))
    full = model(input_ids)
    state = None
    logits = []
    offset = 0
    for length in (3, 1, 4, 5):
        output = model(
            input_ids[:, offset : offset + length],
            state=state,
        )
        logits.append(output.logits)
        state = output.state
        offset += length
    torch.testing.assert_close(
        torch.cat(logits, dim=1),
        full.logits,
        rtol=1e-5,
        atol=1e-6,
    )
    assert state is not None and state.tokens_seen == 13


def test_aluclu_step_matches_single_forward() -> None:
    torch.manual_seed(31)
    model = AlucluLanguageModel(32, model_config()).eval()
    input_ids = torch.randint(0, 32, (2, 9))
    full = model(input_ids)
    state = None
    logits = []
    for index in range(input_ids.shape[1]):
        token_logits, state = model.step(input_ids[:, index], state)
        logits.append(token_logits)
    torch.testing.assert_close(
        torch.stack(logits, dim=1),
        full.logits,
        rtol=1e-5,
        atol=1e-6,
    )


def test_exact_cache_uses_gated_delta_write_surprise_priorities() -> None:
    torch.manual_seed(34)
    model = AlucluLanguageModel(32, model_config()).eval()
    block = model.blocks[1]
    assert block.exact_cache is not None
    x = torch.randn(2, 7, 8)
    state = block.initial_state(
        2,
        device=torch.device("cpu"),
        dtype=torch.float32,
    )
    hidden = block.mixer_norm(x)

    with torch.no_grad():
        _, _, write_surprise = block.gated_delta(
            hidden,
            state.gated_delta,
            return_state=True,
            return_write_surprise=True,
        )
        _, next_state = block(x, state)

    assert next_state.exact_cache is not None
    expected = (
        write_surprise.topk(
            block.exact_cache.config.capacity,
            dim=1,
        )
        .values.sort(dim=1)
        .values
    )
    actual = next_state.exact_cache.priority.sort(dim=1).values
    torch.testing.assert_close(actual, expected)
    assert next_state.exact_cache.valid.all()
    assert next_state.exact_cache.tokens_seen == x.shape[1]


def test_masked_mqar_loss_and_metric() -> None:
    torch.manual_seed(32)
    batch = generate_mqar_batch(
        3,
        3,
        2,
        key_vocab_size=8,
        value_vocab_size=8,
    )
    model = AlucluLanguageModel(batch.vocab_size, model_config())
    output = model(
        batch.input_ids,
        labels=batch.labels,
        loss_mask=batch.loss_mask,
    )
    assert output.loss is not None
    assert torch.isfinite(output.loss)
    accuracy = mqar_accuracy(output.logits, batch)
    assert 0 <= accuracy.item() <= 1
    output.loss.backward()
    assert all(
        parameter.grad is None or torch.isfinite(parameter.grad).all()
        for parameter in model.parameters()
    )


def test_model_state_is_bounded_at_equal_segment_phase() -> None:
    torch.manual_seed(33)
    model = AlucluLanguageModel(32, model_config()).eval()
    state = None
    sizes = []
    with torch.no_grad():
        for index in range(50):
            _, state = model.step(torch.randint(0, 32, (1,)), state)
            if index >= 30 and index % 2 == 0:
                sizes.append(state.tensor_numel())
    assert len(set(sizes[-5:])) == 1
