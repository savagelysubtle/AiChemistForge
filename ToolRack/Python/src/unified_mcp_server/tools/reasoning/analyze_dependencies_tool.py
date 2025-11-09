"""Dependency analysis tool for FastMCP.

Analyzes dependencies and relationships between components.
"""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from unified_mcp_server.tools.reasoning.helpers import (
    build_dependency_graph,
    calculate_graph_complexity,
    calculate_max_depth,
    detect_circular_dependencies,
    determine_dependency_levels,
    find_critical_path,
    generate_dependency_recommendations,
    identify_bottlenecks,
)
from unified_mcp_server.tools.reasoning.validation import (
    MAX_COMPONENTS,
    VALID_RELATIONSHIP_TYPES,
    validate_components,
    validate_relationship_type,
)

logger = logging.getLogger("mcp.tools.reasoning.analyze_dependencies")


def register_analyze_dependencies_tool(mcp: FastMCP) -> None:
    """Register the analyze_dependencies tool with the FastMCP instance."""

    @mcp.tool()
    async def analyze_dependencies(
        components: List[str], relationships: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Analyze dependencies and relationships between components.

        Use for planning work order, identifying bottlenecks, understanding parallel work opportunities,
        or preparing for refactoring. Helps map component coupling and critical paths.

        Relationship types: 'depends_on', 'blocks', 'enables', 'integrates_with'

        Args:
            components: List of component names to analyze (use actual module/service/task names)
            relationships: Optional list of relationships like [{"from": "A", "to": "B", "type": "depends_on"}] (default: None)
        """
        logger.debug(
            f"Starting dependency analysis for {len(components) if components else 0} components"
        )

        try:
            # Input validation per MCP error handling guidelines
            unique_components = validate_components(components)
            if len(unique_components) != len(components):
                logger.warning(
                    f"Removed {len(components) - len(unique_components)} duplicate components"
                )

            # Validate relationships if provided
            validated_relationships = []
            if relationships:
                if not isinstance(relationships, list):
                    raise ValueError("Relationships must be a list of dictionaries")

                for i, rel in enumerate(relationships):
                    if not isinstance(rel, dict):
                        raise ValueError(f"Relationship {i + 1} must be a dictionary")

                    required_keys = ["from", "to", "type"]
                    missing_keys = [key for key in required_keys if key not in rel]
                    if missing_keys:
                        raise ValueError(
                            f"Relationship {i + 1} missing required keys: {missing_keys}"
                        )

                    if rel["from"] not in unique_components:
                        raise ValueError(
                            f"Relationship {i + 1}: 'from' component '{rel['from']}' not in components list"
                        )

                    if rel["to"] not in unique_components:
                        raise ValueError(
                            f"Relationship {i + 1}: 'to' component '{rel['to']}' not in components list"
                        )

                    # Validate relationship type
                    validate_relationship_type(rel["type"])

                    validated_relationships.append(rel)

            logger.debug(
                f"Analyzing {len(unique_components)} unique components with {len(validated_relationships)} relationships"
            )

            # Build dependency graph with error handling
            graph = build_dependency_graph(unique_components, validated_relationships)

            # Detect circular dependencies
            cycles = detect_circular_dependencies(graph)

            # Analyze the dependency structure
            analysis = {
                "components": unique_components,
                "total_components": len(unique_components),
                "dependency_graph": graph,
                "critical_path": find_critical_path(graph),
                "levels": determine_dependency_levels(graph),
                "bottlenecks": identify_bottlenecks(graph),
                "circular_dependencies": cycles if cycles else None,
                "recommendations": generate_dependency_recommendations(graph, cycles),
                "metadata": {
                    "relationship_count": len(validated_relationships),
                    "graph_complexity": calculate_graph_complexity(graph),
                    "max_depth": calculate_max_depth(graph),
                    "has_cycles": len(cycles) > 0,
                    "cycle_count": len(cycles),
                },
            }

            logger.info(
                f"Completed dependency analysis: {len(unique_components)} components, {len(validated_relationships)} relationships"
            )
            return {
                "success": True,
                "analysis": analysis,
                "tool": "analyze_dependencies",
            }

        except ValueError as e:
            logger.error(f"Validation error in analyze_dependencies: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "tool": "analyze_dependencies",
            }
        except Exception as e:
            logger.error(
                f"Unexpected error in analyze_dependencies: {e}", exc_info=True
            )
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tool": "analyze_dependencies",
            }

