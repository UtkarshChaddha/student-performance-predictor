# ============================================================
# ADHYAN DQN SERVICE
# ============================================================

from pathlib import Path

import torch
import torch.nn as nn

from backend.config import settings


# ------------------------------------------------------------
# ACTIONS
# ------------------------------------------------------------

ACTIONS = [
    "EXPLAIN",
    "HINT",
    "REVISION",
    "CHALLENGE",
    "PRACTICE",
    "SIMPLIFY",
]


# ------------------------------------------------------------
# Q-NETWORK
# ------------------------------------------------------------

class QNetwork(nn.Module):

    def __init__(self, state_dim: int = 4, action_dim: int = 6):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),

            nn.Linear(64, 64),
            nn.ReLU(),

            nn.Linear(64, action_dim),
        )

    def forward(self, state):
        return self.network(state)


# ------------------------------------------------------------
# MODEL LOADING
# ------------------------------------------------------------

_model = None


def get_model_path() -> Path:
    """
    Gets the DQN model path from settings.

    Expected environment variable:

        DQN_MODEL_PATH=backend/models/adhyan_dqn.pth
    """

    model_path = Path(settings.dqn_model_path)

    if not model_path.is_absolute():
        model_path = Path(__file__).resolve().parent.parent / model_path

    return model_path


def load_model():

    global _model

    if _model is not None:
        return _model

    model_path = get_model_path()

    if not model_path.exists():
        raise FileNotFoundError(
            "DQN model is not available."
        )

    model = QNetwork(
        state_dim=4,
        action_dim=len(ACTIONS),
    )

    checkpoint = torch.load(
        model_path,
        map_location="cpu",
        weights_only=True,
    )

    # Support either:
    # 1. raw state_dict
    # 2. {"model_state_dict": ...}

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        state_dict = checkpoint["model_state_dict"]
    else:
        state_dict = checkpoint

    model.load_state_dict(state_dict)

    model.eval()

    _model = model

    return _model


# ------------------------------------------------------------
# STATE CREATION
# ------------------------------------------------------------

def build_state(
    accuracy: float,
    attempts: int,
    time_taken: float,
    mastery: float,
):
    """
    Creates the 4-dimensional DQN state.

    Values are normalized between 0 and 1.
    """

    accuracy = max(0.0, min(1.0, accuracy))

    attempts_normalized = min(
        max(attempts, 0) / 20.0,
        1.0,
    )

    time_normalized = min(
        max(time_taken, 0.0) / 300.0,
        1.0,
    )

    mastery = max(0.0, min(1.0, mastery))

    return [
        accuracy,
        attempts_normalized,
        time_normalized,
        mastery,
    ]


# ------------------------------------------------------------
# RECOMMENDATION
# ------------------------------------------------------------

def recommend(
    accuracy: float,
    attempts: int,
    time_taken: float,
    mastery: float,
):
    model = load_model()

    state = build_state(
        accuracy=accuracy,
        attempts=attempts,
        time_taken=time_taken,
        mastery=mastery,
    )

    tensor = torch.tensor(
        [state],
        dtype=torch.float32,
    )

    with torch.no_grad():

        q_values = model(tensor)[0]

    action_index = int(
        torch.argmax(q_values).item()
    )

    action = ACTIONS[action_index]

    return {
        "action": action,
        "action_index": action_index,
        "q_values": [
            round(float(value), 4)
            for value in q_values.tolist()
        ],
        "state": [
            round(float(value), 4)
            for value in state
        ],
    }