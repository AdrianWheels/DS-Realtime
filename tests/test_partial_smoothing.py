import pytest

from utils.stable_partial import StablePartial


def test_stable_partial_emits_after_stability():
    sp = StablePartial(min_chars=4, stable_ms=300)
    t = 0.0
    assert sp.consider("hola", now=t) is None
    t += 0.1
    assert sp.consider("hola", now=t) is None
    t += 0.35
    assert sp.consider("hola", now=t) == "hola"
    t += 0.05
    assert sp.consider("hola", now=t) is None
    t += 0.05
    assert sp.consider("hola mu", now=t) is None
    t += 0.3
    assert sp.consider("hola mu", now=t) is None
    t += 0.1
    assert sp.consider("hola mu", now=t) == "hola mu"


def test_word_or_punct_allows_short_partials():
    sp = StablePartial(min_chars=10, stable_ms=200)
    t = 0.0
    sp.consider("hi", now=t)
    t += 0.25
    assert sp.consider("hi ", now=t) is None
    t += 0.25
    assert sp.consider("hi ", now=t) == "hi "
    t += 0.1
    sp.consider("wow", now=t)
    t += 0.25
    assert sp.consider("wow,", now=t) is None
    t += 0.25
    assert sp.consider("wow,", now=t) == "wow,"
