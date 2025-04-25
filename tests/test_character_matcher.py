import logging
from dataclasses import dataclass
from typing import List

from nikke_arena.character_matcher import CharacterMatcher

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    image_name: str
    expected_id: str


def test_character_matcher(matcher: CharacterMatcher):
    cases: List[TestCase] = [
        TestCase(image_name="001-rosanna.png", expected_id="012"),
        TestCase(image_name="002-jackal.png", expected_id="007"),
        TestCase(image_name="003-anis-sparkling-summer.png", expected_id="008"),
        TestCase(image_name="004-crown.png", expected_id="009"),
        TestCase(image_name="005-maiden-ice-rose.png", expected_id="032"),
        TestCase(image_name="006-rapi-red-hood.png", expected_id="013"),
    ]

    for case in cases:
        image_path = f"testdata/matcher/targets/{case.image_name}"
        result = matcher.match(image_path)
        assert result is not None
        assert result.character.id == case.expected_id

def test_character_matcher_populate_db(matcher: CharacterMatcher):
    matcher.populate_from_image_directory("testdata/ref")

