"""Tests for persistent caching of Gemini split-group responses."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phases.v02.site_architecture.group_splitting import (
    FinalKeywordGroupResponse,
    resolve_split_group,
)
from prompts.v02_prompts import FinalKeywordGroup


class SplitGroupCacheTests(unittest.TestCase):
    def test_validated_split_is_reused_without_another_model_call(self) -> None:
        group = {
            "group_id": "seo-overview",
            "primary_keyword": "seo overview",
            "secondary_keywords": ["seo guide"],
            "keywords": [
                {"keyword": "seo overview"},
                {"keyword": "seo guide"},
            ],
        }
        audit = {
            "status": "split",
            "confidence": 0.9,
            "potential_outliers": ["seo guide"],
            "issues": ["Distinct intent"],
            "recommendation": "Separate the guide intent.",
        }
        response = FinalKeywordGroupResponse(groups=[
            FinalKeywordGroup(
                group_id="seo-overview-page",
                primary_keyword="seo overview",
                secondary_keywords=[],
                page_type="guide",
                reasoning="Overview intent.",
            ),
            FinalKeywordGroup(
                group_id="seo-guide-page",
                primary_keyword="seo guide",
                secondary_keywords=[],
                page_type="guide",
                reasoning="Guide intent.",
            ),
        ])

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "split-groups"
            with patch(
                "phases.v02.site_architecture.group_splitting.generate_json",
                return_value=response,
            ) as generate_json:
                first = resolve_split_group("SEO", group, audit, cache_dir=cache_dir)
                second = resolve_split_group("SEO", group, audit, cache_dir=cache_dir)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 2)
        generate_json.assert_called_once()


if __name__ == "__main__":
    unittest.main()
