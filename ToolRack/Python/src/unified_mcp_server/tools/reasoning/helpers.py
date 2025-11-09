"""Shared helper functions for reasoning tools."""

from typing import Any, Dict, List, Optional


def generate_thinking_steps(approach: str) -> List[str]:
    """Generate thinking steps based on approach."""
    base_steps = {
        "systematic": [
            "Define the problem clearly",
            "Gather all relevant information",
            "Break down into components",
            "Analyze each component",
            "Identify dependencies and constraints",
            "Develop solution approach",
            "Validate solution",
            "Plan implementation steps",
        ],
        "creative": [
            "Understand the creative challenge",
            "Explore existing solutions",
            "Brainstorm alternative approaches",
            "Evaluate feasibility of ideas",
            "Combine best elements",
            "Prototype solution",
            "Refine based on feedback",
            "Finalize creative output",
        ],
        "analytical": [
            "Define analysis objectives",
            "Collect relevant data",
            "Clean and validate data",
            "Apply analytical methods",
            "Interpret results",
            "Identify patterns and insights",
            "Draw conclusions",
            "Recommend next steps",
        ],
        "practical": [
            "Assess immediate needs",
            "Identify available resources",
            "Find quickest viable solution",
            "Test solution rapidly",
            "Implement core functionality",
            "Monitor results",
            "Iterate if needed",
            "Document lessons learned",
        ],
    }
    return base_steps.get(approach, base_steps["systematic"])


def estimate_completion_time(approach: str, num_steps: int) -> str:
    """Estimate completion time based on approach and number of steps."""
    base_time_per_step = {
        "systematic": 20,  # minutes
        "creative": 30,
        "analytical": 25,
        "practical": 15,
    }

    time_minutes = base_time_per_step.get(approach, 20) * num_steps
    if time_minutes < 60:
        return f"{time_minutes} minutes"
    else:
        hours = time_minutes / 60
        return f"{hours:.1f} hours"


def get_domain_dimensions(domain: str) -> List[str]:
    """Get decomposition dimensions for a domain."""
    dimensions = {
        "technical": [
            "Architecture & Design",
            "Data & Storage",
            "Processing & Logic",
            "Interfaces & APIs",
            "Security & Validation",
            "Testing & Quality",
            "Deployment & Operations",
            "Performance & Scalability",
        ],
        "analytical": [
            "Data Collection",
            "Data Cleaning & Validation",
            "Exploratory Analysis",
            "Statistical Modeling",
            "Results Validation",
            "Reporting & Visualization",
            "Interpretation & Insights",
            "Recommendations",
        ],
        "creative": [
            "Research & Inspiration",
            "Ideation & Concepts",
            "Design & Prototyping",
            "Feedback & Iteration",
            "Refinement & Polish",
            "Production & Implementation",
            "Launch & Promotion",
            "Evaluation & Learning",
        ],
        "general": [
            "Understanding & Research",
            "Planning & Strategy",
            "Resource Assessment",
            "Implementation Approach",
            "Quality & Testing",
            "Integration & Dependencies",
            "Review & Validation",
            "Documentation & Handoff",
        ],
    }
    return dimensions.get(domain, dimensions["general"])


def calculate_subproblem_count(target_size: str, max_dimensions: int) -> int:
    """Calculate number of sub-problems based on target size."""
    size_mapping = {
        "small": min(max_dimensions, 8),
        "medium": min(max_dimensions, 5),
        "large": min(max_dimensions, 3),
    }
    return size_mapping.get(target_size, 5)


def generate_focus_questions(dimension: str, problem: str) -> List[str]:
    """Generate focus questions for a dimension."""
    return [
        f"What {dimension.lower()} aspects need attention?",
        f"What are the key challenges in {dimension.lower()}?",
        f"How does {dimension.lower()} impact the overall solution?",
        f"What resources are needed for {dimension.lower()}?",
    ]


def calculate_priority(dimension: str, domain: str) -> str:
    """Calculate priority for a dimension in a domain."""
    high_priority_dims = {
        "technical": ["Architecture & Design", "Security & Validation"],
        "analytical": ["Data Collection", "Data Cleaning & Validation"],
        "creative": ["Research & Inspiration", "Ideation & Concepts"],
        "general": ["Understanding & Research", "Planning & Strategy"],
    }

    domain_priorities = high_priority_dims.get(domain, [])
    return "high" if dimension in domain_priorities else "medium"


def analyze_dependencies(dimensions: List[str]) -> List[Dict[str, str]]:
    """Analyze dependencies between dimensions."""
    dependencies = []
    for i, dim in enumerate(dimensions):
        if i > 0:
            dependencies.append(
                {"from": dimensions[i - 1], "to": dim, "type": "enables"}
            )
    return dependencies


def suggest_execution_order(dimensions: List[str]) -> List[str]:
    """Suggest execution order for dimensions."""
    return dimensions


def estimate_complexity(problem: str, num_dimensions: int) -> str:
    """Estimate problem complexity."""
    if num_dimensions <= 3:
        return "low"
    elif num_dimensions <= 6:
        return "medium"
    else:
        return "high"


def build_dependency_graph(
    components: List[str], relationships: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Build dependency graph from components and relationships."""
    graph = {
        comp: {"depends_on": [], "enables": [], "blocks": [], "integrates_with": []}
        for comp in components
    }

    for rel in relationships:
        from_comp = rel["from"]
        to_comp = rel["to"]
        rel_type = rel["type"]

        if rel_type == "depends_on":
            graph[from_comp]["depends_on"].append(to_comp)
        elif rel_type == "enables":
            graph[from_comp]["enables"].append(to_comp)
        elif rel_type == "blocks":
            graph[from_comp]["blocks"].append(to_comp)
        elif rel_type == "integrates_with":
            graph[from_comp]["integrates_with"].append(to_comp)

    return graph


def detect_circular_dependencies(graph: Dict[str, Any]) -> List[List[str]]:
    """Detect circular dependencies in the graph using DFS.

    Returns:
        List of cycles found (each cycle is a list of component names)
    """
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(comp: str) -> None:
        if comp in rec_stack:
            # Found a cycle
            cycle_start = path.index(comp)
            cycles.append(path[cycle_start:] + [comp])
            return
        if comp in visited:
            return

        visited.add(comp)
        rec_stack.add(comp)
        path.append(comp)

        # Check all dependency types
        for dep_type in ["depends_on", "blocks"]:
            for dep in graph[comp].get(dep_type, []):
                if dep in graph:
                    dfs(dep)

        path.pop()
        rec_stack.remove(comp)

    for comp in graph:
        if comp not in visited:
            dfs(comp)

    return cycles


def find_critical_path(graph: Dict[str, Any]) -> List[str]:
    """Find critical path in dependency graph using topological sort.

    Returns components in order of execution based on dependencies.
    """
    if not graph:
        return []

    # Calculate in-degree for each component
    in_degree = {comp: 0 for comp in graph}
    for comp in graph:
        for dep_type in ["depends_on", "blocks"]:
            for dep in graph[comp].get(dep_type, []):
                if dep in in_degree:
                    in_degree[dep] += 1

    # Topological sort
    queue = [comp for comp in graph if in_degree[comp] == 0]
    critical_path = []

    while queue:
        comp = queue.pop(0)
        critical_path.append(comp)

        for dep_type in ["depends_on", "blocks"]:
            for dep in graph[comp].get(dep_type, []):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

    # If there are remaining components, they form cycles
    remaining = [comp for comp in graph if comp not in critical_path]
    if remaining:
        critical_path.extend(remaining)

    return critical_path


def determine_dependency_levels(graph: Dict[str, Any]) -> Dict[str, int]:
    """Determine dependency levels for components."""
    levels = {}
    for comp in graph:
        levels[comp] = len(graph[comp]["depends_on"])
    return levels


def identify_bottlenecks(graph: Dict[str, Any]) -> List[str]:
    """Identify bottleneck components."""
    dependents = {}
    for comp in graph:
        dependents[comp] = 0
        for other_comp in graph:
            if comp in graph[other_comp]["depends_on"]:
                dependents[comp] += 1

    sorted_bottlenecks = sorted(dependents.items(), key=lambda x: x[1], reverse=True)
    return [comp for comp, count in sorted_bottlenecks[:3] if count > 0]


def generate_dependency_recommendations(
    graph: Dict[str, Any], cycles: Optional[List[List[str]]] = None
) -> List[str]:
    """Generate recommendations based on dependency analysis.

    Args:
        graph: Dependency graph
        cycles: Optional list of detected cycles

    Returns:
        List of recommendations
    """
    recommendations = [
        "Start with components that have no dependencies",
        "Address bottlenecks early to avoid delays",
        "Plan parallel work streams where possible",
        "Build in buffer time for critical path items",
    ]

    if cycles:
        recommendations.insert(
            0,
            f"⚠️ WARNING: {len(cycles)} circular dependency cycle(s) detected. "
            "These must be resolved before implementation.",
        )

    return recommendations


def calculate_graph_complexity(graph: Dict[str, Any]) -> str:
    """Calculate graph complexity."""
    total_relationships = sum(
        len(graph[comp]["depends_on"])
        + len(graph[comp]["enables"])
        + len(graph[comp]["blocks"])
        + len(graph[comp].get("integrates_with", []))
        for comp in graph
    )

    if total_relationships <= 5:
        return "low"
    elif total_relationships <= 15:
        return "medium"
    else:
        return "high"


def calculate_max_depth(graph: Dict[str, Any]) -> int:
    """Calculate maximum dependency depth."""
    max_depth = 0
    for comp in graph:
        depth = len(graph[comp]["depends_on"])
        max_depth = max(max_depth, depth)
    return max_depth
