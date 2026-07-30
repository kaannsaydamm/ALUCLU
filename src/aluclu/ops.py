from __future__ import annotations

import torch
from torch import Tensor, nn


class StreamingDepthwiseConv1d(nn.Module):
    """Causal depthwise convolution with explicit bounded streaming history."""

    def __init__(self, channels: int, kernel_size: int) -> None:
        super().__init__()
        if channels < 1 or kernel_size < 1:
            raise ValueError("channels and kernel_size must be positive")
        self.channels = channels
        self.kernel_size = kernel_size
        self.conv = nn.Conv1d(
            channels,
            channels,
            kernel_size=kernel_size,
            groups=channels,
            bias=True,
        )
        with torch.no_grad():
            self.conv.weight.zero_()
            self.conv.weight[:, 0, -1] = 1
            self.conv.bias.zero_()

    def empty_history(
        self,
        batch_size: int,
        *,
        device: torch.device,
        dtype: torch.dtype,
    ) -> Tensor:
        return torch.zeros(
            batch_size,
            self.kernel_size - 1,
            self.channels,
            device=device,
            dtype=dtype,
        )

    def forward(self, x: Tensor, history: Tensor) -> tuple[Tensor, Tensor]:
        if x.ndim != 3 or x.shape[-1] != self.channels:
            raise ValueError(f"x must have shape [batch, time, {self.channels}]")
        expected_history = (x.shape[0], self.kernel_size - 1, self.channels)
        if tuple(history.shape) != expected_history:
            raise ValueError(
                f"history must have shape {expected_history}, got {tuple(history.shape)}"
            )
        context = torch.cat((history, x), dim=1)
        output = self.conv(context.transpose(1, 2)).transpose(1, 2)
        if self.kernel_size == 1:
            next_history = context[:, :0]
        else:
            next_history = context[:, -(self.kernel_size - 1) :]
        return output, next_history


def l2_normalize(x: Tensor, eps: float) -> Tensor:
    return x / x.norm(dim=-1, keepdim=True).clamp_min(eps)
