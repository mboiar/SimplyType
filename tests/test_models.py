import pytest

from .context import speed_typing_game


@pytest.fixture(scope="module")
def polish_wordset():
    with open("data/polish_wordset.txt") as f:
        ws = f.read()
    yield ws


def test_wordset_fromfile():
    assert 1 == 1
