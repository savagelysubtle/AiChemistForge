"""Problem decomposition tool for FastMCP.

Decomposes complex problems into smaller, manageable parts.
"""

import logging
from typing import Any, Dict

from fastmcp import FastMCP

from unified_mcp_server.tools.reasoning.helpers import (
    analyze_dependencies,
    calculate_priority,
    calculate_subproblem_count,
    estimate_complexity,
    generate_focus_questions,
    get_domain_dimensions,
    suggest_execution_order,
)
from unified_mcp_server.tools.reasoning.validation import (
    MAX_PROBLEM_LENGTH_DECOMPOSE,
    MIN_PROBLEM_LENGTH_DECOMPOSE,
    sanitize_string,
    validate_domain,
    validate_problem_string,
    validate_target_size,
)

logger = logging.getLogger("mcp.tools.reasoning.decompose_problem")


def register_decompose_problem_tool(mcp: FastMCP) -> None:
    """Register the decompose_problem tool with the FastMCP instance."""

    @mcp.tool()
    async def decompose_problem(
        problem: str, target_size: str = "small", domain: str = "general"
    ) -> Dict[str, Any]:
        """Decompose a complex problem into smaller, manageable parts.

        Use when facing large problems that need organization into parallel streams, phases,
        or smaller testable pieces. Ideal for breaking down projects, migrations, implementations,
        or debugging system-wide issues.

        Args:
            problem: The complex problem to decompose (be specific about scope and constraints)
            target_size: Target size for sub-problems: 'small' (detailed), 'medium' (balanced), 'large' (high-level) (default: 'small')
            domain: Problem domain: 'technical', 'analytical', 'creative', or 'general' (default: 'general')
        """
        logger.debug(f"Starting problem decomposition for: {problem[:100]}...")

        try:
            # Input validation per MCP error handling guidelines
            validate_problem_string(
                problem, MIN_PROBLEM_LENGTH_DECOMPOSE, MAX_PROBLEM_LENGTH_DECOMPOSE
            )
            validate_target_size(target_size)
            validate_domain(domain)

            # Sanitize input
            problem_clean = sanitize_string(problem)

            logger.debug(
                f"Decomposing with target_size: {target_size}, domain: {domain}"
            )

            # Determine decomposition strategy based on domain
            dimensions = get_domain_dimensions(domain)

            # Adjust granularity based on target size
            num_subproblems = calculate_subproblem_count(target_size, len(dimensions))
            relevant_dimensions = dimensions[:num_subproblems]

            decomposition = {
                "original_problem": problem_clean,
                "target_size": target_size,
                "domain": domain,
                "sub_problems": [
                    {
                        "id": i + 1,
                        "category": dim,
                        "description": f"Address the {dim.lower()} aspects of: {problem_clean[:100]}{'...' if len(problem_clean) > 100 else ''}",
                        "focus_questions": generate_focus_questions(dim, problem_clean),
                        "priority": calculate_priority(dim, domain),
                    }
                    for i, dim in enumerate(relevant_dimensions)
                ],
                "dependencies": analyze_dependencies(relevant_dimensions),
                "recommended_order": suggest_execution_order(relevant_dimensions),
                "metadata": {
                    "total_dimensions": len(dimensions),
                    "selected_dimensions": len(relevant_dimensions),
                    "complexity_estimate": estimate_complexity(
                        problem_clean, len(relevant_dimensions)
                    ),
                },
            }

            logger.info(
                f"Decomposed problem into {len(relevant_dimensions)} sub-problems"
            )
            return {
                "success": True,
                "decomposition": decomposition,
                "total_sub_problems": len(relevant_dimensions),
                "tool": "decompose_problem",
            }

        except ValueError as e:
            logger.error(f"Validation error in decompose_problem: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "tool": "decompose_problem",
            }
        except Exception as e:
            logger.error(f"Unexpected error in decompose_problem: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tool": "decompose_problem",
            }

