"""
CSP Solver Module
Implements backtracking search with heuristics for timetable generation
"""

from typing import Dict, List, Tuple, Optional
from models import Lecture
from constraints import TimetableConstraints
import time
import random


class TimetableSolver:
    """Solves the timetable CSP using backtracking search"""

    def __init__(self, lectures: List[Lecture],
                 domains: Dict[str, List[Tuple[str, str, str]]],
                 constraints: TimetableConstraints):
        self.lectures = lectures
        self.domains = domains
        self.constraints = constraints
        self.assignment = {}
        self.iterations = 0
        self.start_time = None

    def solve(self, timeout: int = 300) -> Optional[Dict[str, Tuple[str, str, str]]]:
        """
        Solve the CSP using backtracking search

        Args:
            timeout: Maximum time in seconds (default 5 minutes)

        Returns:
            Complete assignment if solution found, None otherwise
        """
        print("\n🚀 Starting CSP Solver...")
        print(f"   Variables: {len(self.lectures)}")
        print(f"   Timeout: {timeout} seconds\n")

        self.start_time = time.time()
        self.iterations = 0
        self.assignment = {}

        # Solve using backtracking
        result = self._backtrack(timeout)

        elapsed = time.time() - self.start_time
        print(f"\n{'=' * 60}")
        if result:
            print("✅ SOLUTION FOUND!")
        else:
            print("❌ NO SOLUTION FOUND")
        print(f"   Time: {elapsed:.2f} seconds")
        print(f"   Iterations: {self.iterations}")
        print(f"{'=' * 60}\n")

        return result

    def _backtrack(self, timeout: int) -> Optional[Dict[str, Tuple[str, str, str]]]:
        """
        Recursive backtracking search

        Args:
            timeout: Time limit in seconds

        Returns:
            Complete assignment or None
        """
        self.iterations += 1

        # Check timeout
        if time.time() - self.start_time > timeout:
            print("\n⏱️  Timeout reached!")
            return None

        # Progress update every 100 iterations
        if self.iterations % 100 == 0:
            assigned = len(self.assignment)
            total = len(self.lectures)
            print(f"   Progress: {assigned}/{total} assigned (iteration {self.iterations})")

        # Check if assignment is complete
        if len(self.assignment) == len(self.lectures):
            return self.assignment

        # Select unassigned variable (lecture)
        var_name = self._select_unassigned_variable()

        if var_name is None:
            return None

        # Try values from domain
        domain = self.domains.get(var_name, [])

        # Order domain values (try most promising first)
        ordered_values = self._order_domain_values(var_name, domain)

        for value in ordered_values:
            # Check if value is consistent with current assignment
            if self.constraints.is_consistent(var_name, value, self.assignment, self.lectures):
                # Make assignment
                self.assignment[var_name] = value

                # Recurse
                result = self._backtrack(timeout)

                if result is not None:
                    return result

                # Backtrack - remove assignment
                del self.assignment[var_name]

        # No solution found with this path
        return None

    def _select_unassigned_variable(self) -> Optional[str]:
        """
        Select next unassigned variable using MRV heuristic
        (Minimum Remaining Values - choose variable with smallest domain)

        Returns:
            Variable name to assign next
        """
        unassigned = []

        for lecture in self.lectures:
            var_name = lecture.get_variable_name()
            if var_name not in self.assignment:
                unassigned.append(var_name)

        if not unassigned:
            return None

        # MRV heuristic: choose variable with fewest legal values
        # Count how many values in domain are still consistent
        min_remaining = float('inf')
        best_var = None

        for var_name in unassigned:
            domain = self.domains.get(var_name, [])
            # Count consistent values
            remaining = sum(1 for value in domain
                            if self.constraints.is_consistent(var_name, value,
                                                              self.assignment, self.lectures))

            if remaining < min_remaining:
                min_remaining = remaining
                best_var = var_name

        return best_var

    def _order_domain_values(self, var_name: str,
                             domain: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
        """
        Order domain values (try most promising first)
        Uses Least Constraining Value heuristic

        Args:
            var_name: Variable being assigned
            domain: List of possible values

        Returns:
            Ordered list of domain values
        """
        # For now, just shuffle to add randomness
        # In advanced version, we could count how many options each value rules out
        ordered = domain.copy()
        random.shuffle(ordered)
        return ordered

    def get_solution_statistics(self) -> Dict:
        """Get statistics about the solution"""
        if not self.assignment:
            return {}

        # Count by day
        timeslot_usage = {}
        instructor_load = {}
        room_usage = {}

        for var_name, (timeslot, room, instructor) in self.assignment.items():
            # Count timeslots
            if timeslot not in timeslot_usage:
                timeslot_usage[timeslot] = 0
            timeslot_usage[timeslot] += 1

            # Count instructor load
            if instructor not in instructor_load:
                instructor_load[instructor] = 0
            instructor_load[instructor] += 1

            # Count room usage
            if room not in room_usage:
                room_usage[room] = 0
            room_usage[room] += 1

        return {
            'total_assigned': len(self.assignment),
            'timeslot_usage': timeslot_usage,
            'instructor_load': instructor_load,
            'room_usage': room_usage
        }


# Test the solver
if __name__ == "__main__":
    print("Testing CSP Solver\n")

    from data_loader import DataLoader
    from problem_builder import ProblemBuilder

    # Load data
    print("Loading data...")
    loader = DataLoader()
    if not loader.load_all_data():
        print("Failed to load data!")
        exit(1)

    # Build problem with small test case
    print("\nBuilding problem...")
    builder = ProblemBuilder(loader)

    # Start with just 1 section for quick test
    test_sections = ['S1_L1']
    print(f"Test sections: {test_sections}\n")

    lectures = builder.build_lectures_for_sections(test_sections)
    domains = builder.build_domains()
    builder.print_problem_summary()

    # Create constraints
    constraints = TimetableConstraints()

    # Solve!
    solver = TimetableSolver(lectures, domains, constraints)
    solution = solver.solve(timeout=60)  # 60 second timeout for test

    if solution:
        print("\n📋 SOLUTION:")
        for var_name, (timeslot, room, instructor) in sorted(solution.items()):
            print(f"  {var_name}")
            print(f"    Time: {timeslot}, Room: {room}, Instructor: {instructor}")

        # Verify solution
        print("\n🔍 Verifying solution...")
        is_valid = constraints.check_all_constraints(solution, lectures)
        print(f"  Valid: {is_valid}")

        if not is_valid:
            conflicts = constraints.get_conflicts(solution, lectures)
            print(f"  Conflicts found: {len(conflicts)}")
            for c in conflicts:
                print(f"    - {c}")

        # Statistics
        stats = solver.get_solution_statistics()
        print(f"\n📊 Statistics:")
        print(f"  Lectures assigned: {stats['total_assigned']}")
        print(f"  Timeslots used: {len(stats['timeslot_usage'])}")
        print(f"  Instructors used: {len(stats['instructor_load'])}")
        print(f"  Rooms used: {len(stats['room_usage'])}")
    else:
        print("\n❌ Could not find solution in time limit")
        print(f"   Assigned: {len(solver.assignment)}/{len(lectures)}")