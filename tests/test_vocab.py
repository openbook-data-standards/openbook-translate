from __future__ import annotations

from openbook_translate import vocab


def test_sports_parsed_from_table() -> None:
    assert {"sport:soccer", "sport:basketball", "sport:cricket", "sport:unknown"} <= vocab.SPORTS
    assert vocab.SPORT_NAMES["sport:soccer"] == "Soccer"
    assert vocab.SPORT_NAMES["sport:unknown"] == "Unknown"
    assert "athletics:100m" in vocab.DISCIPLINES and "athletics:100m" not in vocab.SPORTS
    assert len(vocab.SPORTS) >= 30


def test_segments_exact_and_families() -> None:
    assert "segment:soccer:full-time" in vocab.SEGMENTS
    assert "segment:unknown:unknown" in vocab.SEGMENTS
    patterns = {f.pattern for f in vocab.SEGMENT_FAMILIES}
    assert {"segment:baseball:inning-<n>", "segment:tennis:set-<n>-game-<m>"} <= patterns
    assert vocab.is_known_segment("segment:baseball:inning-1")
    assert vocab.is_known_segment("segment:baseball:inning-14")
    assert vocab.is_known_segment("segment:tennis:set-3-game-12")
    assert not vocab.is_known_segment("segment:baseball:inning-0")
    assert not vocab.is_known_segment("segment:baseball:inning-x")
    assert not vocab.is_known_segment("segment:baseball:inning-1-extra")
    assert not vocab.is_known_segment("segment:soccer:3rd-half")


def test_market_types_have_shape_category_sides() -> None:
    ml = vocab.MARKET_TYPES["market:moneyline"]
    assert (ml.shape, ml.category) == ("n-way", "main-line")
    assert "home" in ml.sides and "away" in ml.sides
    total = vocab.MARKET_TYPES["market:total"]
    assert (total.shape, total.category, total.sides) == ("over-under", "main-line", "over, under")
    assert "market:unknown" in vocab.MARKET_TYPES
    assert len(vocab.MARKET_TYPES) >= 50
    # the shape legend table (binary, n-way, ...) is not mistaken for market ids
    assert "binary" not in vocab.MARKET_TYPES


def test_or_unknown_helpers() -> None:
    assert vocab.sport_or_unknown("soccer") == "sport:soccer"
    assert vocab.sport_or_unknown("sport:soccer") == "sport:soccer"
    assert vocab.sport_or_unknown("curling") == "sport:unknown"
    assert vocab.sport_or_unknown("") == "sport:unknown"
    assert vocab.segment_or_unknown("soccer", "1st-half") == "segment:soccer:1st-half"
    assert vocab.segment_or_unknown("sport:soccer", "1st-half") == "segment:soccer:1st-half"
    assert vocab.segment_or_unknown("baseball", "inning-11") == "segment:baseball:inning-11"
    assert vocab.segment_or_unknown("soccer", "5th-half") == "segment:unknown:unknown"
    assert vocab.segment_or_unknown("curling", "full-time") == "segment:unknown:unknown"
    assert vocab.market_or_unknown("moneyline") == "market:moneyline"
    assert vocab.market_or_unknown("market:total") == "market:total"
    assert vocab.market_or_unknown("bananas") == "market:unknown"


def test_is_known() -> None:
    assert vocab.is_known_sport("sport:soccer") and not vocab.is_known_sport("soccer")
    assert vocab.is_known_market("market:spread") and not vocab.is_known_market("spread")
    assert vocab.is_known_side("home") and vocab.is_known_side("home-or-draw") and not vocab.is_known_side("left")


def test_catch_all_constants() -> None:
    assert vocab.SPORT_UNKNOWN == "sport:unknown"
    assert vocab.SEGMENT_UNKNOWN == "segment:unknown:unknown"
    assert vocab.MARKET_UNKNOWN == "market:unknown"
    assert vocab.sport_slug("sport:soccer") == "soccer"


def test_deprecated_loaded() -> None:
    assert set(vocab.DEPRECATED) >= {"fields", "listValues", "messageTypes"}
    assert not vocab.is_deprecated("sport:soccer")
