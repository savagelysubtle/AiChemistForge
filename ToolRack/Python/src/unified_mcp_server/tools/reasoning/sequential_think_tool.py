"""Sequential thinking tool for FastMCP.

Breaks down problems into sequential thinking steps.
"""

import logging
from typing import Any, Dict

from fastmcp import FastMCP

from unified_mcp_server.tools.reasoning.helpers import (
    estimate_completion_time,
    generate_thinking_steps,
)
from unified_mcp_server.tools.reasoning.validation import (
    MAX_PROBLEM_LENGTH_SEQUENTIAL,
    MIN_PROBLEM_LENGTH_SEQUENTIAL,
    sanitize_string,
    validate_approach,
    validate_problem_string,
)

logger = logging.getLogger("mcp.tools.reasoning.sequential_think")


def register_sequential_think_tool(mcp: FastMCP) -> None:
    """Register the sequential_think tool with the FastMCP instance."""

    @mcp.tool()
    async def sequential_think(
        problem: str, context: str = "", approach: str = "systematic"
    ) -> Dict[str, Any]:
        """Break down problem into sequential thinking steps.

        Use when starting complex tasks, organizing thoughts before implementation, or working
        on unfamiliar domains. Helps ensure critical steps aren't missed.

        Args:
            problem: The problem to analyze and solve (be specific about what you want to accomplish)
            context: Additional context or constraints (timeline, resources, requirements, etc.) (default: "")
            approach: Thinking approach: 'systematic' (technical/debugging), 'creative' (innovation/design),
                     'analytical' (data/research), or 'practical' (quick solutions/MVP) (default: 'systematic')
        """
        logger.debug(f"Starting sequential thinking for problem: {problem[:100]}...")

        try:
            # Input validation per MCP error handling guidelines
            validate_problem_string(
                problem, MIN_PROBLEM_LENGTH_SEQUENTIAL, MAX_PROBLEM_LENGTH_SEQUENTIAL
            )
            validate_approach(approach)

            # Sanitize inputs
            problem_clean = sanitize_string(problem)
            context_clean = sanitize_string(context) if context else ""

            logger.debug(f"Using approach: {approach}")

            # Generate thinking steps based on approach
            steps = generate_thinking_steps(approach)

            # Apply the steps to the specific problem
            analysis = {
                "problem": problem_clean,
                "context": context_clean,
                "approach": approach,
                "thinking_steps": steps,
                "next_actions": [
                    f"Work through each step systematically with the problem: '{problem_clean[:50]}{'...' if len(problem_clean) > 50 else ''}'",
                    "Consider the provided context and any additional constraints",
                    "Document insights and decisions at each step",
                    "Be prepared to iterate and refine as understanding improves",
                ],
                "metadata": {
                    "step_count": len(steps),
                    "estimated_time": estimate_completion_time(approach, len(steps)),
                },
            }

            logger.info(
                f"Generated {len(steps)} thinking steps using {approach} approach"
            )
            return {
                "success": True,
                "analysis": analysis,
                "tool": "sequential_think",
            }

        except ValueError as e:
            logger.error(f"Validation error in sequential_think: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "tool": "sequential_think",
            }
        except Exception as e:
            logger.error(f"Unexpected error in sequential_think: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tool": "sequential_think",
            }

