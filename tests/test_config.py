from dataclasses import FrozenInstanceError, replace

import pytest

from mqtt_dos import RunConfig
from mqtt_dos.config import OUTPUTS_DIR


def test_defaults_follow_paper_protocol():
    config = RunConfig()

    assert config.random_state == 42
    assert config.test_size == 0.2
    assert config.n_trials == 30
    assert config.cv_folds == 5
    assert len(config.models) == 7
    assert len(config.selectors) == 6


def test_output_dir_uses_run_name():
    config = RunConfig(run_name="smoke")

    assert config.output_dir == OUTPUTS_DIR / "smoke"


def test_config_is_frozen():
    config = RunConfig()

    with pytest.raises(FrozenInstanceError):
        config.n_trials = 1


def test_replace_creates_quick_config():
    quick = replace(RunConfig(), run_name="smoke", n_trials=2, cv_folds=2)

    assert quick.n_trials == 2
    assert RunConfig().n_trials == 30


@pytest.mark.parametrize("test_size", [0, 1, 1.5])
def test_invalid_test_size_is_rejected(test_size):
    with pytest.raises(ValueError, match="test_size"):
        RunConfig(test_size=test_size)


def test_unknown_model_is_rejected():
    with pytest.raises(ValueError, match="XGBoost"):
        RunConfig(models=("LDA", "XGBoost"))
