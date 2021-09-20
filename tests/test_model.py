import os
import time
from pathlib import Path
from typing import Text, Optional

import pytest

import rasa
import rasa.constants
import rasa.shared.utils.io
from rasa import model
from rasa.exceptions import ModelNotFound
from rasa.model import (
    get_latest_model,
    get_model,
)


def test_get_latest_model(tmp_path: Path):
    path = tmp_path / "test_get_latest_model"
    path.mkdir()
    Path(path / "model_one.tar.gz").touch()

    # create second model later to be registered as distinct in Windows
    time.sleep(0.1)
    Path(path / "model_two.tar.gz").touch()

    path_of_latest = os.path.join(path, "model_two.tar.gz")
    assert get_latest_model(str(path)) == path_of_latest


def test_get_model_context_manager(trained_rasa_model: str):
    with get_model(trained_rasa_model) as unpacked:
        assert os.path.exists(unpacked)

    assert not os.path.exists(unpacked)


def test_get_local_model(trained_rasa_model: str):
    assert rasa.model.get_local_model(trained_rasa_model) == trained_rasa_model


@pytest.mark.parametrize("model_path", ["foobar", "rasa", "README.md", None])
def test_get_local_model_exception(model_path: Optional[Text]):
    with pytest.raises(ModelNotFound):
        rasa.model.get_local_model(model_path)


@pytest.mark.parametrize("model_path", ["foobar", "rasa", "README.md", None])
def test_get_model_exception(model_path: Optional[Text]):
    with pytest.raises(ModelNotFound):
        get_model(model_path)
