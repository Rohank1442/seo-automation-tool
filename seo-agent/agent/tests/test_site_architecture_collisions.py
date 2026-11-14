"""Tests for merging equivalent cluster pages and resolving URL collisions."""

import unittest

from phases.v02.site_architecture.builder import build_site_architecture
from phases.v02.site_architecture.validation import (
    validate_architecture,
    validate_keyword_coverage,
)


def build_inputs(cluster_name: str, group_id: str, primary: str, secondary: list[str] | None = None):
    group = {
        "group_id": group_id,
        "primary_keyword": primary,
        "secondary_keywords": secondary or [],
        "keywords": [{"keyword": term} for term in [primary, *(secondary or [])]],
        "page_type": "guide",
        "reasoning": "Related search intent.",
    }
    research = {
        "clusters": [{
            "keywords": [
                {"keyword": term, "volume": 500, "competition_level": "low", "intent": "informational"}
                for term in [primary, *(secondary or [])]
            ]
        }]
    }
    keyword_groups = {"clusters": [{"cluster": cluster_name, "groups": [group]}]}
    audit_data = {
        "clusters": [{"audits": [{"group_id": group_id, "status": "approved", "confidence": 0.95}]}]
    }
    return research, keyword_groups, audit_data


class SiteArchitectureCollisionTests(unittest.TestCase):
    def test_matching_keyword_group_is_merged_into_cluster_root(self) -> None:
        research, keyword_groups, audit_data = build_inputs(
            "Foundational SEO Strategy",
            "foundational-seo-strategy-guide",
            "foundational seo strategy",
            ["seo strategy foundation"],
        )

        architecture = build_site_architecture(
            research,
            {},
            keyword_groups,
            audit_data,
        )
        pages = architecture["pages"]
        root = pages[0]

        self.assertEqual(len(pages), 1)
        self.assertEqual(root["page_type"], "cluster")
        self.assertEqual(root["url"], "/foundational-seo-strategy/")
        self.assertEqual(root["primary_keyword"], "foundational seo strategy")
        self.assertEqual(root["secondary_keywords"], ["seo strategy foundation"])
        self.assertEqual(root["source_group_id"], "foundational-seo-strategy-guide")
        self.assertEqual(root["audit_status"], "approved")
        validate_architecture(architecture)
        validate_keyword_coverage(keyword_groups, architecture)

    def test_different_phrase_slug_collision_gets_a_distinct_url(self) -> None:
        research, keyword_groups, audit_data = build_inputs(
            "C++ SEO",
            "c-seo-guide",
            "C SEO",
        )

        architecture = build_site_architecture(
            research,
            {},
            keyword_groups,
            audit_data,
        )
        pages = architecture["pages"]

        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["url"], "/c-seo/")
        self.assertEqual(pages[1]["url"], "/c-seo-c-seo-guide/")
        self.assertEqual(len({page["url"] for page in pages}), 2)
        validate_architecture(architecture)
        validate_keyword_coverage(keyword_groups, architecture)

    def test_colliding_cluster_root_ids_and_urls_are_disambiguated(self) -> None:
        architecture = build_site_architecture(
            {"clusters": []},
            {},
            {"clusters": [{"cluster": "C++ SEO", "groups": []}, {"cluster": "C SEO", "groups": []}]},
            {"clusters": []},
        )

        pages = architecture["pages"]
        self.assertEqual(len({page["id"] for page in pages}), 2)
        self.assertEqual(len({page["url"] for page in pages}), 2)
        validate_architecture(architecture)


if __name__ == "__main__":
    unittest.main()
