"""Validate page architecture structure and keyword coverage."""

from typing import Any, Dict

from .keywords import collect_group_keywords, normalize_keyword


def validate_architecture(
    architecture: Dict[str, Any],
) -> None:
    """
    Validate the final architecture.

    Checks:

    - page IDs are unique
    - URLs are unique
    - every page has a URL
    - every child references an existing parent
    - every non-cluster page has a primary keyword
    - every page is indexable only when it has a valid URL
    """

    pages = architecture.get(
        "pages",
        [],
    )

    page_ids = set()
    urls = set()

    for page in pages:
        page_id = page.get(
            "id"
        )

        url = page.get(
            "url"
        )

        if not page_id:
            raise ValueError(
                "Architecture contains a page without an ID."
            )

        if page_id in page_ids:
            raise ValueError(
                f"Duplicate page ID: {page_id}"
            )

        page_ids.add(
            page_id
        )

        if not url:
            raise ValueError(
                f"Page has no URL: {page_id}"
            )

        if url in urls:
            raise ValueError(
                f"Duplicate URL: {url}"
            )

        urls.add(
            url
        )

        if page.get(
            "page_type"
        ) != "cluster":

            if not page.get(
                "primary_keyword"
            ):
                raise ValueError(
                    f"Non-cluster page has no primary keyword: "
                    f"{page_id}"
                )

    for page in pages:
        parent_id = page.get(
            "parent_page_id"
        )

        if parent_id is not None:
            if parent_id not in page_ids:
                raise ValueError(
                    f"Page '{page['id']}' references "
                    f"missing parent '{parent_id}'."
                )


def validate_keyword_coverage(
    keyword_groups: Dict[str, Any],
    architecture: Dict[str, Any],
) -> None:
    """
    Validate that every keyword from the final semantic groups is
    represented by at least one architecture page.

    This protects against accidental keyword loss during the
    architecture transformation.
    """

    expected = set()

    for cluster in keyword_groups.get(
        "clusters",
        [],
    ):
        for group in cluster.get(
            "groups",
            [],
        ):
            for keyword in collect_group_keywords(
                group
            ):
                expected.add(
                    normalize_keyword(
                        keyword
                    )
                )

    actual = set()

    for page in architecture.get(
        "pages",
        [],
    ):
        primary = page.get(
            "primary_keyword"
        )

        if primary:
            actual.add(
                normalize_keyword(
                    primary
                )
            )

        for keyword in page.get(
            "secondary_keywords",
            [],
        ):
            actual.add(
                normalize_keyword(
                    keyword
                )
            )

    missing = expected - actual

    if missing:
        raise ValueError(
            "Final architecture lost keywords: "
            + ", ".join(
                sorted(missing)
            )
        )
