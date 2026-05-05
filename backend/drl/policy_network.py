"""
EA Policy Network — PyTorch MLP for capability priority ordering.
Designed to run on AMD ROCm (exposed as "cuda" in PyTorch) or CPU.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class EAPolicyNetwork(nn.Module):
    """
    3-layer MLP. Input: 20-dim state vector. Output: log-softmax over 10 action slots.
    Architecture: Linear(20→128)→ReLU→Dropout→Linear(128→128)→ReLU→Dropout→Linear(128→64)→ReLU→Linear(64→10)→LogSoftmax
    """

    def __init__(self, state_dim: int = 20, action_dim: int = 10, hidden: int = 128):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Returns log-softmax probabilities over action slots."""
        return F.log_softmax(self.net(state), dim=-1)

    def get_priority_weights(self, state: torch.Tensor) -> torch.Tensor:
        """Returns softmax probabilities (not log) for interpretability display."""
        with torch.no_grad():
            logits = self.net(state)
            return F.softmax(logits, dim=-1)

    def get_priority_ranking(self, state: np.ndarray | torch.Tensor) -> list[int]:
        """Returns capability indices sorted by descending priority weight."""
        if isinstance(state, np.ndarray):
            state = torch.FloatTensor(state)
        if state.dim() == 1:
            state = state.unsqueeze(0)
        weights = self.get_priority_weights(state).squeeze(0)
        return weights.argsort(descending=True).tolist()

    def sample_action(self, state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Samples a priority ordering using multinomial sampling without replacement.
        Returns (action_indices, log_prob_sum) for REINFORCE.
        """
        log_probs = self.forward(state)
        probs = torch.exp(log_probs)

        # Sample without replacement using Gumbel-top-k trick
        log_uniform = torch.log(-torch.log(torch.clamp(torch.rand_like(probs), 1e-10, 1.0)))
        keys = log_probs - log_uniform
        action_indices = keys.argsort(descending=True)

        # Sum log probs along the sampled order
        selected_log_probs = log_probs.gather(-1, action_indices)
        log_prob_sum = selected_log_probs.sum()

        return action_indices, log_prob_sum


def get_device() -> torch.device:
    """
    Returns AMD ROCm device (exposed as torch.cuda) or CPU.
    ROCm check: torch.cuda.is_available() returns True when HIP/ROCm PyTorch is installed.
    Also honours HIP_VISIBLE_DEVICES / ROCR_VISIBLE_DEVICES env vars.
    """
    import os
    import logging
    _log = logging.getLogger(__name__)

    # Explicit GPU override — set HIP_VISIBLE_DEVICES=0 or CUDA_VISIBLE_DEVICES=0
    forced = os.environ.get("HIP_VISIBLE_DEVICES") or os.environ.get("CUDA_VISIBLE_DEVICES") or os.environ.get("ROCR_VISIBLE_DEVICES")

    rocm_version = getattr(torch.version, "hip", None)
    cuda_available = torch.cuda.is_available()

    if cuda_available:
        device = torch.device("cuda:0")
        try:
            name = torch.cuda.get_device_name(0)
        except Exception:
            name = "AMD GPU"
        if rocm_version:
            _log.info(f"DRL policy running on AMD ROCm {rocm_version}: {name}")
        else:
            _log.info(f"DRL policy running on GPU: {name}")
        return device

    if rocm_version:
        # ROCm PyTorch installed but CUDA interface not reporting available — try anyway
        try:
            device = torch.device("cuda:0")
            _ = torch.zeros(1).to(device)
            _log.info(f"DRL policy running on AMD ROCm {rocm_version} (forced)")
            return device
        except Exception:
            pass

    _log.info(
        "DRL policy running on CPU — LLM inference uses AMD MI300X via vLLM. "
        "To use ROCm for DRL, install ROCm-enabled PyTorch: "
        "pip install torch --index-url https://download.pytorch.org/whl/rocm6.2"
    )
    return torch.device("cpu")
