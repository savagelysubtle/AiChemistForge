"""Shared validation functions and constants for reasoning tools."""

from typing import List

# Constants for validation
VALID_APPROACHES = ["systematic", "creative", "analytical", "practical"]
VALID_TARGET_SIZES = ["small", "medium", "large"]
VALID_DOMAINS = ["technical", "analytical", "creative", "general"]
VALID_RELATIONSHIP_TYPES = ["depends_on", "blocks", "enables", "integrates_with"]

# Limits
MAX_PROBLEM_LENGTH_SEQUENTIAL = 10000
MAX_PROBLEM_LENGTH_DECOMPOSE = 20000
MIN_PROBLEM_LENGTH_SEQUENTIAL = 5
MIN_PROBLEM_LENGTH_DECOMPOSE = 10
MAX_COMPONENTS = 100


def validate_problem_string(
    problem: str, min_length: int = MIN_PROBLEM_LENGTH_SEQUENTIAL, max_length: int = MAX_PROBLEM_LENGTH_SEQUENTIAL
) -> None:
    """Validate problem string input.

    Args:
        problem: Problem string to validate
        min_length: Minimum required length
        max_length: Maximum allowed length

    Raises:
        ValueError: If validation fails
    """
    if not problem or not isinstance(problem, str):
        raise ValueError("Problem parameter is required and must be a non-empty string")

    problem_stripped = problem.strip()
    if len(problem_stripped) < min_length:
        raise ValueError(
            f"Problem description must be at least {min_length} characters long"
        )

    if len(problem) > max_length:
        raise ValueError(
            f"Problem description is too long (max {max_length} characters)"
        )


def validate_approach(approach: str) -> None:
    """Validate thinking approach parameter.

    Args:
        approach: Approach string to validate

    Raises:
        ValueError: If validation fails
    """
    if approach not in VALID_APPROACHES:
        raise ValueError(
            f"Invalid approach '{approach}'. Must be one of: {VALID_APPROACHES}"
        )


def validate_target_size(target_size: str) -> None:
    """Validate target size parameter.

    Args:
        target_size: Target size string to validate

    Raises:
        ValueError: If validation fails
    """
    if target_size not in VALID_TARGET_SIZES:
        raise ValueError(
            f"Invalid target_size '{target_size}'. Must be one of: {VALID_TARGET_SIZES}"
        )


def validate_domain(domain: str) -> None:
    """Validate domain parameter.

    Args:
        domain: Domain string to validate

    Raises:
        ValueError: If validation fails
    """
    if domain not in VALID_DOMAINS:
        raise ValueError(
            f"Invalid domain '{domain}'. Must be one of: {VALID_DOMAINS}"
        )


def validate_components(components: List[str]) -> List[str]:
    """Validate and normalize component list.

    Args:
        components: List of component names

    Returns:
        Validated and normalized component list

    Raises:
        ValueError: If validation fails
    """
    if not components or not isinstance(components, list):
        raise ValueError(
            "Components parameter is required and must be a non-empty list"
        )

    if len(components) > MAX_COMPONENTS:
        raise ValueError(f"Too many components for analysis (max {MAX_COMPONENTS})")

    validated_components = []
    for i, comp in enumerate(components):
        if not isinstance(comp, str) or not comp.strip():
            raise ValueError(f"Component {i + 1} must be a non-empty string")
        validated_components.append(comp.strip())

    # Remove duplicates while preserving order
    unique_components = list(dict.fromkeys(validated_components))
    return unique_components


def validate_relationship_type(rel_type: str) -> None:
    """Validate relationship type.

    Args:
        rel_type: Relationship type string to validate

    Raises:
        ValueError: If validation fails
    """
    if rel_type not in VALID_RELATIONSHIP_TYPES:
        raise ValueError(
            f"Invalid relationship type '{rel_type}'. Must be one of: {VALID_RELATIONSHIP_TYPES}"
        )


def sanitize_string(value: str, max_length: int = None) -> str:
    """Sanitize string input by stripping whitespace and optionally truncating.

    Args:
        value: String to sanitize
        max_length: Optional maximum length to truncate to

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""
    sanitized = value.strip()
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized



