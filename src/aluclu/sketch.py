from __future__ import annotations

import torch
from torch import Tensor, nn


class TensorSketch(nn.Module):
    """Differentiable TensorSketch features for a homogeneous polynomial kernel."""

    def __init__(
        self,
        input_dim: int,
        degree: int,
        sketch_dim: int,
        n_sketches: int,
        seed: int,
    ) -> None:
        super().__init__()
        if input_dim < 1:
            raise ValueError("input_dim must be positive")
        if degree < 1:
            raise ValueError("degree must be positive")
        if sketch_dim < 2:
            raise ValueError("sketch_dim must be >= 2")
        if n_sketches < 1:
            raise ValueError("n_sketches must be positive")

        self.input_dim = input_dim
        self.degree = degree
        self.sketch_dim = sketch_dim
        self.n_sketches = n_sketches

        generator = torch.Generator(device="cpu")
        generator.manual_seed(seed)
        hashes = torch.randint(
            0,
            sketch_dim,
            (n_sketches, degree, input_dim),
            generator=generator,
            dtype=torch.long,
        )
        signs = torch.randint(
            0,
            2,
            (n_sketches, degree, input_dim),
            generator=generator,
            dtype=torch.long,
        ).to(torch.float32)
        signs = signs.mul(2).sub(1)
        self.register_buffer("hashes", hashes, persistent=True)
        self.register_buffer("signs", signs, persistent=True)

    def _count_sketch(self, x: Tensor, hashes: Tensor, signs: Tensor) -> Tensor:
        batch, width = x.shape
        if width != self.input_dim:
            raise ValueError(f"expected width {self.input_dim}, got {width}")
        index = hashes.to(device=x.device).view(1, width).expand(batch, width)
        values = x * signs.to(device=x.device, dtype=x.dtype).view(1, width)
        output = x.new_zeros(batch, self.sketch_dim)
        return output.scatter_add(dim=1, index=index, src=values)

    def forward(self, x: Tensor) -> Tensor:
        if x.ndim != 2:
            raise ValueError("TensorSketch expects [batch, input_dim]")

        results = []
        for sketch_index in range(self.n_sketches):
            product: Tensor | None = None
            for degree_index in range(self.degree):
                count_sketch = self._count_sketch(
                    x,
                    self.hashes[sketch_index, degree_index],
                    self.signs[sketch_index, degree_index],
                )
                spectrum = torch.fft.rfft(
                    count_sketch,
                    n=self.sketch_dim,
                    dim=-1,
                )
                product = spectrum if product is None else product * spectrum
            if product is None:
                raise RuntimeError("degree validation failed")
            results.append(torch.fft.irfft(product, n=self.sketch_dim, dim=-1))
        return torch.stack(results, dim=0)
