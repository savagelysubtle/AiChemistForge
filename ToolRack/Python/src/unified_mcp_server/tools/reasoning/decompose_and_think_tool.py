"""Decompose and think tool for FastMCP.

Combines problem decomposition with sequential thinking for comprehensive planning.
"""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from unified_mcp_server.tools.reasoning.helpers import (
    analyze_dependencies,
    build_dependency_graph,
    calculate_graph_complexity,
    calculate_max_depth,
    calculate_priority,
    calculate_subproblem_count,
    detect_circular_dependencies,
    determine_dependency_levels,
    estimate_completion_time,
    estimate_complexity,
    find_critical_path,
    generate_dependency_recommendations,
    generate_focus_questions,
    generate_thinking_steps,
    get_domain_dimensions,
    identify_bottlenecks,
    suggest_execution_order,
)
from unified_mcp_server.tools.reasoning.validation import (
    MAX_PROBLEM_LENGTH_DECOMPOSE,
    MIN_PROBLEM_LENGTH_DECOMPOSE,
    sanitize_string,
    validate_approach,
    validate_domain,
    validate_problem_string,
    validate_target_size,
)

logger = logging.getLogger("mcp.tools.reasoning.decompose_and_think")


def _calculate_criterion_score(
    criterion: str,
    decomposition: Dict[str, Any],
    thinking_plans: Dict[str, Any],
    dependency_analysis: Dict[str, Any],
) -> float:
    """Calculate score for a success criterion based on plan quality."""
    # Base score
    score = 0.7

    # Increase score based on plan completeness
    if decomposition.get("sub_problems"):
        score += 0.1
    if thinking_plans:
        score += 0.1
    if dependency_analysis and not dependency_analysis.get("metadata", {}).get(
        "has_cycles", False
    ):
        score += 0.1

    return min(score, 1.0)


def _calculate_confidence_score(
    decomposition: Dict[str, Any],
    thinking_plans: Dict[str, Any],
    dependency_analysis: Dict[str, Any],
) -> float:
    """Calculate overall confidence score based on plan quality."""
    score = 0.7

    # Increase based on decomposition quality
    if len(decomposition.get("sub_problems", [])) >= 3:
        score += 0.05

    # Increase based on thinking plans
    if thinking_plans:
        score += 0.05

    # Decrease if cycles detected
    if dependency_analysis and dependency_analysis.get("metadata", {}).get(
        "has_cycles", False
    ):
        score -= 0.1

    return max(0.0, min(score, 1.0))


def register_decompose_and_think_tool(mcp: FastMCP) -> None:
    """Register the decompose_and_think tool with the FastMCP instance."""

    @mcp.tool()
    async def decompose_and_think(
        problem: str,
        target_size: str = "medium",
        domain: str = "general",
        approach: str = "systematic",
        include_dependencies: bool = True,
        include_reflection: bool = True,
        success_criteria: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Decompose a complex problem and apply sequential thinking to each sub-problem.

        Combines problem decomposition with sequential thinking for comprehensive planning.
        Outputs sub-problems with priorities, dependency analysis, execution steps, and optional reflection.

        Args:
            problem: The complex problem to decompose and plan (be specific about scope)
            target_size: Decomposition granularity: 'small' (detailed), 'medium' (balanced), 'large' (high-level) (default: 'medium')
            domain: Problem domain: 'technical', 'analytical', 'creative', or 'general' (default: 'general')
            approach: Thinking approach for each sub-problem: 'systematic', 'creative', 'analytical', or 'practical' (default: 'systematic')
            include_dependencies: Whether to analyze dependencies between sub-problems (default: True)
            include_reflection: Whether to reflect on the overall plan (default: True)
            success_criteria: Optional criteria for reflection evaluation (default: None)
        """
        logger.debug(f"Starting decompose_and_think for: {problem[:100]}...")

        try:
            # Input validation using shared validation functions
            validate_problem_string(
                problem, MIN_PROBLEM_LENGTH_DECOMPOSE, MAX_PROBLEM_LENGTH_DECOMPOSE
            )
            validate_target_size(target_size)
            validate_domain(domain)
            validate_approach(approach)

            # Sanitize input
            problem_clean = sanitize_string(problem)

            # Step 1: Decompose the problem (simulate decompose_problem call)
            dimensions = get_domain_dimensions(domain)
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

            # Step 2: Optional dependency analysis (simulate analyze_dependencies call)
            dependency_analysis = None
            if include_dependencies:
                components = [sub["category"] for sub in decomposition["sub_problems"]]
                relationships = decomposition["dependencies"]
                graph = build_dependency_graph(components, relationships)
                cycles = detect_circular_dependencies(graph)
                dependency_analysis = {
                    "components": components,
                    "dependency_graph": graph,
                    "critical_path": find_critical_path(graph),
                    "levels": determine_dependency_levels(graph),
                    "bottlenecks": identify_bottlenecks(graph),
                    "circular_dependencies": cycles if cycles else None,
                    "recommendations": generate_dependency_recommendations(graph, cycles),
                    "metadata": {
                        "relationship_count": len(relationships),
                        "graph_complexity": calculate_graph_complexity(graph),
                        "max_depth": calculate_max_depth(graph),
                        "has_cycles": len(cycles) > 0,
                        "cycle_count": len(cycles),
                    },
                }

            # Step 3: Apply sequential thinking to each sub-problem (simulate sequential_think calls)
            thinking_plans = {}
            total_steps = 0
            for sub_prob in decomposition["sub_problems"]:
                sub_problem_desc = sub_prob["description"]
                steps = generate_thinking_steps(approach)
                analysis = {
                    "problem": sub_problem_desc,
                    "approach": approach,
                    "thinking_steps": steps,
                    "next_actions": [
                        f"Work through each step for: '{sub_problem_desc[:50]}{'...' if len(sub_problem_desc) > 50 else ''}'",
                        "Document insights and decisions at each step",
                    ],
                    "metadata": {
                        "step_count": len(steps),
                        "estimated_time": estimate_completion_time(
                            approach, len(steps)
                        ),
                    },
                }
                thinking_plans[sub_prob["category"]] = analysis
                total_steps += len(steps)

            # Step 4: Optional reflection (simulate reflect_on_solution call)
            reflection = None
            if include_reflection:
                if success_criteria is None:
                    success_criteria = [
                        "Addresses the core problem effectively",
                        "Provides clear sub-problem breakdown",
                        "Includes actionable thinking steps",
                        "Considers dependencies and risks",
                        "Has measurable implementation path",
                    ]

                reflection = {
                    "original_problem": problem_clean,
                    "solution_summary": {
                        "decomposition": decomposition,
                        "thinking_plans": thinking_plans,
                        "dependency_analysis": dependency_analysis,
                    },
                    "evaluation": {
                        "strengths": [
                            "Comprehensive breakdown into manageable sub-problems",
                            "Detailed thinking steps for each component",
                            "Dependency analysis identifies bottlenecks and critical paths",
                            "Structured approach reduces overwhelm",
                        ],
                        "weaknesses": [
                            "May require refinement for very unique problems",
                            "Dependency assumptions are heuristic-based",
                            "Time estimates are approximate",
                        ],
                        "opportunities": [
                            "Integrate with actual tool execution (e.g., solve_with_tools)",
                            "Add iterative feedback loops",
                            "Customize thinking approaches per sub-problem",
                        ],
                        "threats": [
                            "Over-decomposition for simple problems",
                            "Circular dependencies in complex domains",
                            "Resource constraints not fully modeled",
                        ],
                    },
                    "criteria_assessment": [
                        {
                            "criterion": crit,
                            "score": _calculate_criterion_score(
                                crit, decomposition, thinking_plans, dependency_analysis
                            ),
                            "notes": f"Plan addresses: {crit}",
                        }
                        for crit in success_criteria
                    ],
                    "recommendations": {
                        "improvements": [
                            "Validate dependencies with domain experts",
                            "Add resource allocation to sub-problems",
                            "Incorporate testing/validation steps",
                        ],
                        "alternatives": [
                            "Use smaller decomposition for quick wins",
                            "Combine with solve_with_tools for tool orchestration",
                        ],
                        "next_steps": [
                            "Execute highest-priority sub-problems first",
                            "Monitor progress and adjust dependencies",
                            "Reflect again after initial implementation",
                        ],
                    },
                    "confidence_score": _calculate_confidence_score(
                        decomposition, thinking_plans, dependency_analysis
                    ),
                }

            # Compile final output
            result = {
                "success": True,
                "problem": problem_clean,
                "decomposition": decomposition,
                "dependency_analysis": dependency_analysis
                if include_dependencies
                else None,
                "thinking_plans": thinking_plans,
                "reflection": reflection if include_reflection else None,
                "metadata": {
                    "total_sub_problems": len(decomposition["sub_problems"]),
                    "total_thinking_steps": total_steps,
                    "estimated_total_time": f"{total_steps * 15 // 60:.1f} hours"
                    if total_steps > 4
                    else f"{total_steps * 15} minutes",
                },
                "tool": "decompose_and_think",
            }

            logger.info(
                f"Completed decompose_and_think: {len(decomposition['sub_problems'])} sub-problems, {total_steps} thinking steps"
            )
            return result

        except ValueError as e:
            logger.error(f"Validation error in decompose_and_think: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "tool": "decompose_and_think",
            }
        except Exception as e:
            logger.error(f"Unexpected error in decompose_and_think: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tool": "decompose_and_think",
            }

