"""Load and save the JSON artifacts used by final site architecture."""

import json
import os
from typing import Any, Dict

V01_OUTPUT_PATH = os.path.join(
    "outputs",
    "page_opportunities.json",
)

V02_OUTPUT_DIR = os.path.join(
    "outputs",
    "v02",
)

SITE_PROFILE_PATH = os.path.join(
    V02_OUTPUT_DIR,
    "site_profile.json",
)

KEYWORD_GROUPS_PATH = os.path.join(
    V02_OUTPUT_DIR,
    "keyword_groups.json",
)

GROUP_AUDIT_PATH = os.path.join(
    V02_OUTPUT_DIR,
    "keyword_group_audit.json",
)

ARCHITECTURE_PATH = os.path.join(
    V02_OUTPUT_DIR,
    "site_architecture.json",
)


def load_json_file(
    path: str,
) -> Dict[str, Any]:
    """
    Load a JSON object from disk.

    Args:
        path:
            Path to the JSON file.

    Returns:
        Parsed JSON dictionary.

    Raises:
        FileNotFoundError:
            If the file does not exist.

        ValueError:
            If the file does not contain a JSON object.
    """

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Required file was not found: {path}"
        )

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON file: {path}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object in: {path}"
        )

    return data


def save_json_file(
    path: str,
    data: Dict[str, Any],
) -> None:
    """
    Save a JSON object to disk.

    Args:
        path:
            Destination file path.

        data:
            Dictionary to serialize.
    """

    directory = os.path.dirname(path)

    if directory:
        os.makedirs(
            directory,
            exist_ok=True,
        )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_v01_research(path: str = V01_OUTPUT_PATH) -> Dict[str, Any]:
    """
    Load the keyword/page opportunity research produced by v0.1.
    """

    return load_json_file(
        path
    )


def load_site_profile(path: str = SITE_PROFILE_PATH) -> Dict[str, Any]:
    """
    Load the SiteProfile produced during the v0.2 foundation stage.
    """

    return load_json_file(
        path
    )


def load_keyword_groups(path: str = KEYWORD_GROUPS_PATH) -> Dict[str, Any]:
    """
    Load the semantic keyword groups produced by v0.2 grouping.
    """

    return load_json_file(
        path
    )


def load_group_audit(path: str = GROUP_AUDIT_PATH) -> Dict[str, Any]:
    """
    Load the keyword group audit produced by the audit stage.
    """

    return load_json_file(
        path
    )
