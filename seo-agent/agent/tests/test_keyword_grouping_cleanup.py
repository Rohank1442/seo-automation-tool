"""Unit tests for repairing Gemini keyword-group assignments."""

import unittest

from phases.v02.keyword_grouping_stage.validation import (
    clean_keyword_grouping,
    validate_grouping,
)


def keyword_records(*terms: str) -> list[dict[str, str]]:
    return [{"keyword": term} for term in terms]


class KeywordGroupingCleanupTests(unittest.TestCase):
    def test_primary_assignment_wins_over_secondary_assignment(self) -> None:
        keywords = keyword_records("topic one", "shared term", "topic two")
        grouping = {
            "clusters": [],
            "groups": [
                {
                    "group_id": "first-group",
                    "primary_keyword": "topic one",
                    "secondary_keywords": ["shared term"],
                },
                {
                    "group_id": "second-group",
                    "primary_keyword": "shared term",
                    "secondary_keywords": ["topic two"],
                },
            ],
        }

        cleaned, _, _, _, duplicates = clean_keyword_grouping(keywords, grouping)

        self.assertEqual(cleaned["groups"][0]["secondary_keywords"], [])
        self.assertEqual(cleaned["groups"][1]["primary_keyword"], "shared term")
        self.assertEqual(duplicates[0]["kept_group"], "second-group")
        validate_grouping(keywords, cleaned)

    def test_first_duplicate_primary_wins_and_next_keyword_is_promoted(self) -> None:
        keywords = keyword_records("shared term", "first helper", "second helper")
        grouping = {
            "groups": [
                {
                    "group_id": "first-group",
                    "primary_keyword": "shared term",
                    "secondary_keywords": ["first helper"],
                },
                {
                    "group_id": "second-group",
                    "primary_keyword": "shared term",
                    "secondary_keywords": ["second helper"],
                },
            ]
        }

        cleaned, _, dropped, promoted, duplicates = clean_keyword_grouping(keywords, grouping)

        self.assertEqual(cleaned["groups"][0]["primary_keyword"], "shared term")
        self.assertEqual(cleaned["groups"][1]["primary_keyword"], "second helper")
        self.assertEqual(dropped, 0)
        self.assertEqual(promoted, 1)
        self.assertEqual(duplicates[0]["kept_group"], "first-group")
        validate_grouping(keywords, cleaned)

    def test_first_duplicate_secondary_wins(self) -> None:
        keywords = keyword_records("topic one", "topic two", "shared term")
        grouping = {
            "groups": [
                {
                    "group_id": "first-group",
                    "primary_keyword": "topic one",
                    "secondary_keywords": ["shared term"],
                },
                {
                    "group_id": "second-group",
                    "primary_keyword": "topic two",
                    "secondary_keywords": ["shared term"],
                },
            ]
        }

        cleaned, _, _, _, duplicates = clean_keyword_grouping(keywords, grouping)

        self.assertEqual(cleaned["groups"][0]["secondary_keywords"], ["shared term"])
        self.assertEqual(cleaned["groups"][1]["secondary_keywords"], [])
        self.assertEqual(duplicates[0]["kept_group"], "first-group")
        validate_grouping(keywords, cleaned)

    def test_unresearched_terms_are_removed_and_empty_group_is_dropped(self) -> None:
        keywords = keyword_records("known term")
        grouping = {
            "groups": [
                {
                    "group_id": "invented-only",
                    "primary_keyword": "made up keyword",
                    "secondary_keywords": [],
                },
                {
                    "group_id": "known-group",
                    "primary_keyword": "known term",
                    "secondary_keywords": ["another made up keyword"],
                },
            ]
        }

        cleaned, removed, dropped, promoted, duplicates = clean_keyword_grouping(keywords, grouping)

        self.assertEqual([group["group_id"] for group in cleaned["groups"]], ["known-group"])
        self.assertEqual(removed, ["made up keyword", "another made up keyword"])
        self.assertEqual(dropped, 1)
        self.assertEqual(promoted, 0)
        self.assertEqual(duplicates, [])
        validate_grouping(keywords, cleaned)

    def test_missing_researched_keyword_still_fails_validation(self) -> None:
        keywords = keyword_records("assigned term", "missing term")
        grouping = {
            "groups": [
                {
                    "group_id": "one-group",
                    "primary_keyword": "assigned term",
                    "secondary_keywords": [],
                }
            ]
        }

        cleaned, *_ = clean_keyword_grouping(keywords, grouping)

        with self.assertRaisesRegex(ValueError, "missing term"):
            validate_grouping(keywords, cleaned)


if __name__ == "__main__":
    unittest.main()
