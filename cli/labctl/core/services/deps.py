"""
Service Dependency Graph and Resolver

This module provides functionality for resolving service dependencies,
detecting circular dependencies, and ordering services for deployment.
"""

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

from rich.console import Console

from .schema import ServiceSchema

console = Console()


class DependencyError(Exception):
    """Dependency resolution error"""

    pass


class CircularDependencyError(DependencyError):
    """Circular dependency detected"""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle + [cycle[0]])
        super().__init__(f"Circular dependency detected: {cycle_str}")


class MissingDependencyError(DependencyError):
    """Required dependency not found"""

    def __init__(self, service: str, missing_deps: List[str]):
        self.service = service
        self.missing_deps = missing_deps
        deps_str = ", ".join(missing_deps)
        super().__init__(
            f"Service '{service}' requires missing dependencies: {deps_str}"
        )


class DependencyGraph:
    """
    Service dependency graph with resolution and validation capabilities
    """

    def __init__(self, schemas: Dict[str, ServiceSchema]):
        """
        Initialize dependency graph from service schemas

        Args:
            schemas: Dictionary mapping service IDs to ServiceSchema objects
        """
        self.schemas = schemas
        self._graph = self._build_graph()
        self._reverse_graph = self._build_reverse_graph()

    def _build_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph (service -> dependencies)"""
        graph = {}
        for service_id, schema in self.schemas.items():
            graph[service_id] = set(schema.dependencies)
        return graph

    def _build_reverse_graph(self) -> Dict[str, Set[str]]:
        """Build reverse dependency graph (service -> dependents)"""
        reverse_graph = defaultdict(set)
        for service_id, deps in self._graph.items():
            for dep in deps:
                reverse_graph[dep].add(service_id)
        return dict(reverse_graph)

    def get_dependencies(self, service_id: str) -> Set[str]:
        """Get direct dependencies of a service"""
        return self._graph.get(service_id, set())

    def get_dependents(self, service_id: str) -> Set[str]:
        """Get services that depend on this service"""
        return self._reverse_graph.get(service_id, set())

    def validate_dependencies(self) -> List[str]:
        """
        Validate all dependencies exist and no cycles

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for missing dependencies
        for service_id, deps in self._graph.items():
            missing = deps - set(self.schemas.keys())
            if missing:
                errors.append(
                    f"Service '{service_id}' has missing dependencies: {', '.join(sorted(missing))}"
                )

        # Check for circular dependencies
        try:
            self._detect_cycles()
        except CircularDependencyError as e:
            errors.append(str(e))

        return errors

    def _detect_cycles(self) -> None:
        """
        Detect circular dependencies using DFS

        Raises:
            CircularDependencyError: If a cycle is detected
        """
        visited = set()
        rec_stack = set()
        path = []

        def visit(service: str):
            if service in rec_stack:
                # Found cycle - extract the cycle
                cycle_start = path.index(service)
                cycle = path[cycle_start:]
                raise CircularDependencyError(cycle)

            if service in visited:
                return

            visited.add(service)
            rec_stack.add(service)
            path.append(service)

            for dep in self._graph.get(service, set()):
                visit(dep)

            rec_stack.remove(service)
            path.pop()

        for service in self._graph:
            if service not in visited:
                visit(service)

    def resolve_dependencies(
        self, selected_services: List[str], include_dependents: bool = False
    ) -> List[str]:
        """
        Resolve dependencies and return topologically sorted order

        Args:
            selected_services: List of service IDs to include
            include_dependents: Whether to include services that depend on selected ones

        Returns:
            List of service IDs in dependency order (dependencies first)

        Raises:
            MissingDependencyError: If required dependencies are missing
            CircularDependencyError: If circular dependencies exist
        """
        # Validate selected services exist
        invalid_services = [s for s in selected_services if s not in self.schemas]
        if invalid_services:
            raise MissingDependencyError("selection", invalid_services)

        # Collect all required services
        required_services = set(selected_services)

        # Add dependencies
        to_process = deque(selected_services)
        while to_process:
            service = to_process.popleft()
            deps = self.get_dependencies(service)

            for dep in deps:
                if dep not in required_services:
                    required_services.add(dep)
                    to_process.append(dep)

        # Add dependents if requested
        if include_dependents:
            to_process = deque(selected_services)
            while to_process:
                service = to_process.popleft()
                dependents = self.get_dependents(service)

                for dependent in dependents:
                    if dependent not in required_services:
                        required_services.add(dependent)
                        to_process.append(dependent)

        # Validate all required services exist
        missing = required_services - set(self.schemas.keys())
        if missing:
            raise MissingDependencyError("resolution", list(missing))

        # Topological sort
        return self._topological_sort(required_services)

    def _topological_sort(self, services: Set[str]) -> List[str]:
        """
        Perform topological sort on subset of services

        Args:
            services: Set of service IDs to sort

        Returns:
            List of service IDs in topological order

        Raises:
            CircularDependencyError: If circular dependencies exist
        """
        # Build subgraph
        subgraph = {}
        in_degree = {}

        for service in services:
            deps = self._graph.get(service, set()) & services
            subgraph[service] = deps
            in_degree[service] = len(deps)

        # Kahn's algorithm
        queue = deque([s for s in services if in_degree[s] == 0])
        result = []

        while queue:
            service = queue.popleft()
            result.append(service)

            # Process dependents
            for dependent in services:
                if service in subgraph[dependent]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        # Check for cycles
        if len(result) != len(services):
            remaining = services - set(result)
            # Try to find a cycle in remaining services
            try:
                self._detect_cycles_in_subset(remaining, subgraph)
            except CircularDependencyError:
                raise
            # If no cycle found, there's an unknown issue
            raise DependencyError(
                f"Unable to resolve dependencies for: {', '.join(remaining)}"
            )

        return result

    def _detect_cycles_in_subset(
        self, services: Set[str], subgraph: Dict[str, Set[str]]
    ) -> None:
        """Detect cycles in a subset of services"""
        visited = set()
        rec_stack = set()
        path = []

        def visit(service: str):
            if service in rec_stack:
                cycle_start = path.index(service)
                cycle = path[cycle_start:]
                raise CircularDependencyError(cycle)

            if service in visited:
                return

            visited.add(service)
            rec_stack.add(service)
            path.append(service)

            for dep in subgraph.get(service, set()):
                if dep in services:
                    visit(dep)

            rec_stack.remove(service)
            path.pop()

        for service in services:
            if service not in visited:
                visit(service)

    def get_dependency_tree(self, service_id: str, max_depth: int = 10) -> Dict:
        """
        Get dependency tree for a service

        Args:
            service_id: Service to analyze
            max_depth: Maximum recursion depth

        Returns:
            Nested dictionary representing dependency tree
        """
        if service_id not in self.schemas:
            return {}

        def build_tree(svc_id: str, depth: int, visited: Set[str]) -> Dict:
            if depth >= max_depth or svc_id in visited:
                return {
                    "id": svc_id,
                    "name": self.schemas[svc_id].name,
                    "truncated": depth >= max_depth,
                }

            visited = visited | {svc_id}
            deps = self.get_dependencies(svc_id)

            return {
                "id": svc_id,
                "name": self.schemas[svc_id].name,
                "category": self.schemas[svc_id].category,
                "dependencies": [
                    build_tree(dep, depth + 1, visited)
                    for dep in sorted(deps)
                    if dep in self.schemas
                ],
            }

        return build_tree(service_id, 0, set())

    def suggest_removal_order(self, services_to_remove: List[str]) -> List[List[str]]:
        """
        Suggest order for removing services to avoid breaking dependencies

        Args:
            services_to_remove: Services to be removed

        Returns:
            List of lists, where each inner list contains services that can be
            removed together
        """
        if not services_to_remove:
            return []

        # Build removal graph (reverse of dependency graph for removal services)
        removal_set = set(services_to_remove)
        removal_graph = {}
        in_degree = {}

        for service in services_to_remove:
            # Dependencies that will NOT be removed (blockers)
            external_deps = self.get_dependencies(service) - removal_set
            removal_graph[service] = external_deps
            in_degree[service] = len(external_deps)

        # Group by removal phases
        phases = []
        remaining = set(services_to_remove)

        while remaining:
            # Find services with no external dependencies
            removable = [s for s in remaining if in_degree[s] == 0]

            if not removable:
                # All remaining services have external dependencies
                phases.append(list(remaining))
                break

            phases.append(removable)
            remaining -= set(removable)

            # Update in_degree for remaining services
            for service in remaining:
                # Recalculate dependencies that will still exist after this phase
                updated_external_deps = self.get_dependencies(
                    service
                ) - removal_set | set(removable)
                in_degree[service] = len(
                    updated_external_deps & set(self.schemas.keys()) - removal_set
                )

        return phases


def resolve_with_dependencies(
    schemas: Dict[str, ServiceSchema], selected_ids: List[str]
) -> List[str]:
    """
    Convenience function to resolve dependencies for selected services

    Args:
        schemas: Available service schemas
        selected_ids: Service IDs to resolve dependencies for

    Returns:
        List of service IDs in dependency order

    Raises:
        DependencyError: If dependencies cannot be resolved
    """
    graph = DependencyGraph(schemas)
    return graph.resolve_dependencies(selected_ids)


def validate_service_dependencies(schemas: Dict[str, ServiceSchema]) -> List[str]:
    """
    Validate all service dependencies

    Args:
        schemas: Service schemas to validate

    Returns:
        List of validation errors (empty if valid)
    """
    graph = DependencyGraph(schemas)
    return graph.validate_dependencies()


def get_dependency_info(schemas: Dict[str, ServiceSchema], service_id: str) -> Dict:
    """
    Get comprehensive dependency information for a service

    Args:
        schemas: Available service schemas
        service_id: Service to analyze

    Returns:
        Dictionary with dependency information
    """
    if service_id not in schemas:
        return {}

    graph = DependencyGraph(schemas)

    return {
        "service_id": service_id,
        "service_name": schemas[service_id].name,
        "direct_dependencies": list(graph.get_dependencies(service_id)),
        "direct_dependents": list(graph.get_dependents(service_id)),
        "dependency_tree": graph.get_dependency_tree(service_id),
        "required_services": graph.resolve_dependencies([service_id]),
    }
