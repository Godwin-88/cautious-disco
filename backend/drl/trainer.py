"""
REINFORCE trainer for the EA Policy Network.
Runs on AMD ROCm (PyTorch CUDA interface) or CPU.
Trains in ~30 seconds on CPU, <5 seconds on ROCm.
"""

import os
import json
import time
import logging
import numpy as np
import torch
import torch.optim as optim

from backend.drl.policy_network import EAPolicyNetwork, get_device
from backend.drl.environment import EAEnvironment

log = logging.getLogger(__name__)

CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "checkpoints")
DEFAULT_CHECKPOINT = os.path.join(CHECKPOINT_DIR, "ea_policy_v1.pt")


class REINFORCETrainer:
    """Vanilla policy gradient trainer for EAPolicyNetwork on EAEnvironment."""

    def __init__(
        self,
        policy: EAPolicyNetwork | None = None,
        env: EAEnvironment | None = None,
        lr: float = 1e-3,
        device: torch.device | None = None,
    ):
        self.device = device or get_device()
        self.policy = (policy or EAPolicyNetwork()).to(self.device)
        self.env = env or EAEnvironment()
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        self.training_log: list[dict] = []

    def compute_returns(self, rewards: list[float], gamma: float = 0.99) -> torch.Tensor:
        """Compute discounted returns (single-step env: just the reward)."""
        returns = []
        G = 0.0
        for r in reversed(rewards):
            G = r + gamma * G
            returns.insert(0, G)
        returns_t = torch.FloatTensor(returns).to(self.device)
        # Normalise
        if returns_t.std() > 1e-8:
            returns_t = (returns_t - returns_t.mean()) / (returns_t.std() + 1e-8)
        return returns_t

    def train(self, n_episodes: int = 100, gamma: float = 0.99) -> list[dict]:
        """
        Run REINFORCE for n_episodes.
        Returns training_log list of {episode, reward, loss}.
        Saves checkpoint every 25 episodes and at end.
        """
        log.info(f"Starting REINFORCE training: {n_episodes} episodes on {self.device}")
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)

        t0 = time.time()
        episode_rewards = []

        for episode in range(n_episodes):
            self.policy.train()
            state = self.env.reset()
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)

            # Single-step episode: sample one ordering
            action_indices, log_prob_sum = self.policy.sample_action(state_t.squeeze(0))
            action_np = action_indices.cpu().numpy()

            _, reward, _ = self.env.step(action_np)

            # REINFORCE update
            returns = self.compute_returns([reward], gamma)
            loss = -(log_prob_sum * returns[0])

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 1.0)
            self.optimizer.step()

            episode_rewards.append(reward)
            entry = {
                "episode": episode,
                "reward": round(reward, 4),
                "loss": round(loss.item(), 6),
                "avg_reward_last10": round(float(np.mean(episode_rewards[-10:])), 4),
            }
            self.training_log.append(entry)

            if episode % 25 == 0 or episode == n_episodes - 1:
                log.info(
                    f"  Episode {episode+1}/{n_episodes} | "
                    f"reward={reward:.4f} | loss={loss.item():.6f} | "
                    f"avg10={entry['avg_reward_last10']:.4f}"
                )
                self.save_checkpoint(DEFAULT_CHECKPOINT)

        elapsed = time.time() - t0
        log.info(f"Training completed in {elapsed:.1f}s | final avg reward: {np.mean(episode_rewards[-20:]):.4f}")

        # Save training log alongside checkpoint
        log_path = DEFAULT_CHECKPOINT.replace(".pt", "_log.json")
        with open(log_path, "w") as f:
            json.dump(self.training_log, f, indent=2)

        return self.training_log

    def save_checkpoint(self, path: str):
        torch.save({
            "policy_state_dict": self.policy.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "training_log": self.training_log,
            "device": str(self.device),
        }, path)

    def load_checkpoint(self, path: str = DEFAULT_CHECKPOINT) -> bool:
        if not os.path.exists(path):
            log.warning(f"Checkpoint not found: {path}")
            return False
        checkpoint = torch.load(path, map_location=self.device)
        self.policy.load_state_dict(checkpoint["policy_state_dict"])
        if "optimizer_state_dict" in checkpoint:
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        if "training_log" in checkpoint:
            self.training_log = checkpoint["training_log"]
        log.info(f"Loaded checkpoint from {path}")
        return True


def load_trained_policy(checkpoint_path: str = DEFAULT_CHECKPOINT) -> EAPolicyNetwork:
    """Convenience function: load a trained policy for inference."""
    device = get_device()
    policy = EAPolicyNetwork().to(device)
    if os.path.exists(checkpoint_path):
        checkpoint = torch.load(checkpoint_path, map_location=device)
        policy.load_state_dict(checkpoint["policy_state_dict"])
        log.info(f"Policy loaded from {checkpoint_path}")
    else:
        log.warning(f"No checkpoint at {checkpoint_path} — using random policy. Run: python -m pipeline.train_drl")
    policy.eval()
    return policy


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    trainer = REINFORCETrainer()
    trainer.train(n_episodes=150)
    print(f"Checkpoint saved to: {DEFAULT_CHECKPOINT}")
