from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

import torch
from torch import Tensor, nn

from .compression import compress_slot, truncate_factors_with_error
from .config import EpisodicMemoryConfig
from .ops import StreamingDepthwiseConv1d, l2_normalize
from .sketch import TensorSketch
from .state import EpisodicState, MemorySlot


class MassConservingRouter(nn.Module):
    """Degree-1/TensorSketch router with exact identity at zero temperature."""

    def __init__(self, config: EpisodicMemoryConfig) -> None:
        super().__init__()
        self.config = config
        self.sketch = TensorSketch(
            input_dim=config.router_dimension,
            degree=config.router_degree,
            sketch_dim=config.sketch_dim,
            n_sketches=config.n_sketches,
            seed=config.router_seed,
        )
        self.mix_logits = nn.Parameter(torch.zeros(2))
        self.temperature_raw = nn.Parameter(torch.zeros(()))

    @property
    def temperature(self) -> Tensor:
        return self.config.max_temperature * torch.tanh(self.temperature_raw)

    def scores(
        self,
        query: Tensor,
        query_sketch: Tensor,
        slots: Sequence[MemorySlot],
    ) -> Tensor:
        if not slots:
            return query.new_zeros(query.shape[0], 0)
        linear_scores = []
        polynomial_scores = []
        for slot in slots:
            scale = slot.count.clamp_min(1).sqrt()
            linear_scores.append(
                torch.einsum("bd,bd->b", query, slot.route_sum) / scale
            )
            each_sketch = torch.einsum(
                "jbm,jbm->jb",
                query_sketch,
                slot.sketch_sum,
            )
            polynomial_scores.append(each_sketch.median(dim=0).values / scale)
        mixture = self.mix_logits.softmax(dim=0)
        linear = torch.stack(linear_scores, dim=1)
        polynomial = torch.stack(polynomial_scores, dim=1)
        return mixture[0] * linear + mixture[1] * polynomial

    def weights(self, scores: Tensor, denominator_mass: Tensor) -> Tensor:
        """Return positive weights that preserve total denominator mass exactly."""

        if scores.shape != denominator_mass.shape or scores.ndim != 2:
            raise ValueError("scores and denominator_mass must share [batch, slots]")
        if scores.shape[1] == 0:
            return scores

        config = self.config
        base_mass = denominator_mass.sum(dim=1, keepdim=True).clamp_min(config.eps)
        center = (scores * denominator_mass).sum(dim=1, keepdim=True) / base_mass
        log_unnormalized = (self.temperature * (scores - center)).clamp(
            min=-config.max_log_weight,
            max=config.max_log_weight,
        )
        unnormalized = log_unnormalized.exp()
        mass_normalizer = (
            (unnormalized * denominator_mass).sum(dim=1, keepdim=True) / base_mass
        ).clamp_min(config.eps)
        return unnormalized / mass_normalizer


class BoundedEpisodicMemory(nn.Module):
    """Streaming episodic memory with exact live segments and bounded capsules.

    Completed recent segments are exact rank-``segment_size`` factors. Overflow
    is merged into a fixed ring of temporal archive capsules using a thin
    QR-plus-small-SVD truncation. Each capsule accepts a bounded number of
    segments before the oldest capsule is replaced, so both state size and
    accumulated compression depth are independent of stream length.
    """

    def __init__(self, config: EpisodicMemoryConfig) -> None:
        super().__init__()
        self.config = config
        d_model = config.d_model
        route_dim = config.router_dimension
        self.stem = StreamingDepthwiseConv1d(d_model, config.conv_kernel)
        self.query_projection = nn.Linear(d_model, d_model, bias=False)
        self.key_projection = nn.Linear(d_model, d_model, bias=False)
        self.value_projection = nn.Linear(d_model, d_model, bias=False)
        self.output_projection = nn.Linear(d_model, d_model, bias=False)
        self.route_projection = nn.Linear(d_model, route_dim, bias=False)
        self.router = MassConservingRouter(config)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for projection in (
            self.query_projection,
            self.key_projection,
            self.value_projection,
            self.output_projection,
        ):
            nn.init.xavier_uniform_(projection.weight)
        if (
            self.route_projection.weight.shape[0]
            == self.route_projection.weight.shape[1]
        ):
            nn.init.eye_(self.route_projection.weight)
        else:
            nn.init.orthogonal_(self.route_projection.weight)

    def feature_map(self, x: Tensor) -> Tensor:
        config = self.config
        return config.feature_floor + (
            config.feature_ceiling - config.feature_floor
        ) * torch.sigmoid(x)

    def initial_state(
        self,
        batch_size: int,
        *,
        device: torch.device,
        dtype: torch.dtype,
    ) -> EpisodicState:
        return EpisodicState(
            conv_history=self.stem.empty_history(
                batch_size,
                device=device,
                dtype=dtype,
            ),
            current=None,
            live=(),
            archive=(),
            archive_cursor=0,
            archive_cursor_segments=0,
            tokens_seen=0,
        )

    def _validate_state(self, x: Tensor, state: EpisodicState) -> None:
        if state.conv_history.shape[0] != x.shape[0]:
            raise ValueError("state batch size does not match x")
        if len(state.live) > self.config.live_segments:
            raise ValueError("state contains too many live segments")
        if len(state.archive) > self.config.archive_slots:
            raise ValueError("state contains too many archive slots")

    @staticmethod
    def _read_slot(
        slot: MemorySlot,
        query_feature: Tensor,
    ) -> tuple[Tensor, Tensor]:
        factor_weights = torch.einsum(
            "brd,bd->br",
            slot.right,
            query_feature,
        )
        numerator = torch.einsum(
            "brd,br->bd",
            slot.left,
            factor_weights,
        )
        denominator = torch.einsum("bd,bd->b", slot.z, query_feature)
        return numerator, denominator

    def aggregate(
        self,
        query_feature: Tensor,
        route_query: Tensor,
        route_query_sketch: Tensor,
        slots: Sequence[MemorySlot],
    ) -> tuple[Tensor, Tensor, Tensor]:
        batch, width = query_feature.shape
        if not slots:
            return (
                query_feature.new_zeros(batch, width),
                query_feature.new_zeros(batch),
                query_feature.new_zeros(batch, 0),
            )

        numerators = []
        denominators = []
        for slot in slots:
            numerator, denominator = self._read_slot(slot, query_feature)
            numerators.append(numerator)
            denominators.append(denominator)
        numerator_stack = torch.stack(numerators, dim=1)
        denominator_stack = torch.stack(denominators, dim=1)

        if self.config.routing:
            scores = self.router.scores(
                route_query,
                route_query_sketch,
                slots,
            )
            weights = self.router.weights(scores, denominator_stack)
        else:
            weights = torch.ones_like(denominator_stack)

        numerator = torch.einsum("bk,bkd->bd", weights, numerator_stack)
        denominator = denominator_stack.sum(dim=1)
        return numerator, denominator, weights

    @staticmethod
    def _token_slot(
        value: Tensor,
        key_feature: Tensor,
        route_key: Tensor,
        route_key_sketch: Tensor,
    ) -> MemorySlot:
        batch = value.shape[0]
        return MemorySlot(
            left=value.unsqueeze(1),
            right=key_feature.unsqueeze(1),
            z=key_feature,
            route_sum=route_key,
            sketch_sum=route_key_sketch,
            count=value.new_ones(batch),
            error_bound=value.new_zeros(batch),
        )

    @staticmethod
    def _append_slot(current: MemorySlot | None, token: MemorySlot) -> MemorySlot:
        if current is None:
            return token
        return MemorySlot(
            left=torch.cat((current.left, token.left), dim=1),
            right=torch.cat((current.right, token.right), dim=1),
            z=current.z + token.z,
            route_sum=current.route_sum + token.route_sum,
            sketch_sum=current.sketch_sum + token.sketch_sum,
            count=current.count + token.count,
            error_bound=current.error_bound + token.error_bound,
        )

    def _merge_archive_slot(
        self,
        previous: MemorySlot,
        incoming: MemorySlot,
    ) -> MemorySlot:
        left, right, discarded = truncate_factors_with_error(
            torch.cat((previous.left, incoming.left), dim=1),
            torch.cat((previous.right, incoming.right), dim=1),
            self.config.archive_rank,
        )
        return MemorySlot(
            left=left,
            right=right,
            z=previous.z + incoming.z,
            route_sum=previous.route_sum + incoming.route_sum,
            sketch_sum=previous.sketch_sum + incoming.sketch_sum,
            count=previous.count + incoming.count,
            error_bound=(previous.error_bound + incoming.error_bound + discarded),
        )

    def _archive_insert(
        self,
        state: EpisodicState,
        incoming: MemorySlot,
    ) -> EpisodicState:
        config = self.config
        if config.archive_slots == 0:
            return state

        compressed = compress_slot(incoming, config.archive_rank)
        archive = list(state.archive)
        cursor = state.archive_cursor
        cursor_segments = state.archive_cursor_segments

        if not archive:
            archive.append(compressed)
            cursor = 0
            cursor_segments = 1
        elif cursor_segments < config.archive_segments_per_slot:
            archive[cursor] = self._merge_archive_slot(archive[cursor], incoming)
            cursor_segments += 1
        else:
            next_cursor = (cursor + 1) % config.archive_slots
            if len(archive) < config.archive_slots:
                next_cursor = len(archive)
                archive.append(compressed)
            else:
                archive[next_cursor] = compressed
            cursor = next_cursor
            cursor_segments = 1

        return replace(
            state,
            archive=tuple(archive),
            archive_cursor=cursor,
            archive_cursor_segments=cursor_segments,
        )

    def _write_token(
        self,
        state: EpisodicState,
        token: MemorySlot,
    ) -> EpisodicState:
        config = self.config
        current = self._append_slot(state.current, token)
        live = state.live
        next_state = state

        if current.left.shape[1] == config.segment_size:
            live = live + (current,)
            current = None
            if len(live) > config.live_segments:
                evicted, live = live[0], live[1:]
                next_state = self._archive_insert(next_state, evicted)
        return replace(
            next_state,
            current=current,
            live=live,
            tokens_seen=state.tokens_seen + 1,
        )

    def forward(
        self,
        x: Tensor,
        state: EpisodicState | None = None,
        *,
        return_state: bool = False,
    ) -> Tensor | tuple[Tensor, EpisodicState]:
        if x.ndim != 3 or x.shape[-1] != self.config.d_model:
            raise ValueError(f"x must have shape [batch, time, {self.config.d_model}]")
        if state is None:
            state = self.initial_state(
                x.shape[0],
                device=x.device,
                dtype=x.dtype,
            )
        self._validate_state(x, state)

        hidden, next_history = self.stem(x, state.conv_history)
        query_features = self.feature_map(self.query_projection(hidden))
        key_features = self.feature_map(self.key_projection(hidden))
        values = self.value_projection(hidden)
        route = l2_normalize(
            self.route_projection(hidden),
            self.config.eps,
        )

        batch, time, route_width = route.shape
        sketches = self.router.sketch(route.reshape(batch * time, route_width))
        sketches = sketches.reshape(
            self.config.n_sketches,
            batch,
            time,
            self.config.sketch_dim,
        )
        state = replace(state, conv_history=next_history)

        readouts = []
        for index in range(time):
            token = self._token_slot(
                values[:, index],
                key_features[:, index],
                route[:, index],
                sketches[:, :, index],
            )
            state = self._write_token(state, token)

            slots: tuple[MemorySlot, ...] = state.archive + state.live
            if state.current is not None:
                slots = slots + (state.current,)
            numerator, denominator, _ = self.aggregate(
                query_features[:, index],
                route[:, index],
                sketches[:, :, index],
                slots,
            )
            readout = numerator / denominator.clamp_min(self.config.eps).unsqueeze(-1)
            readouts.append(readout)

        output = self.output_projection(torch.stack(readouts, dim=1))
        if return_state:
            return output, state
        return output

    def step(
        self,
        x: Tensor,
        state: EpisodicState | None = None,
    ) -> tuple[Tensor, EpisodicState]:
        if x.ndim != 2:
            raise ValueError("step expects [batch, d_model]")
        output, next_state = self.forward(
            x.unsqueeze(1),
            state,
            return_state=True,
        )
        return output[:, 0], next_state

    def maximum_retained_tokens(self) -> int:
        config = self.config
        return config.segment_size * (
            1
            + config.live_segments
            + config.archive_slots * config.archive_segments_per_slot
        )

    def saturated_state_elements_per_batch(self) -> int:
        config = self.config
        route = config.router_dimension
        sketch = config.n_sketches * config.sketch_dim
        live_slot = (
            2 * config.segment_size * config.d_model
            + config.d_model
            + route
            + sketch
            + 2
        )
        archive_slot = (
            2 * config.archive_rank * config.d_model
            + config.d_model
            + route
            + sketch
            + 2
        )
        history = (config.conv_kernel - 1) * config.d_model
        return (
            (config.live_segments + 1) * live_slot
            + config.archive_slots * archive_slot
            + history
        )

    @staticmethod
    def detach_state(state: EpisodicState) -> EpisodicState:
        return state.detach()
