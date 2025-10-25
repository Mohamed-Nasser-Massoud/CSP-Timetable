"""
Constraints Module
Implements hard constraints for timetable CSP
"""

from typing import Dict, Tuple, List
from models import Lecture


class TimetableConstraints:
    """Implements all hard constraints for timetable generation"""

    def __init__(self):
        pass

    def check_all_constraints(self,
                              assignment: Dict[str, Tuple[str, str, str]],
                              lectures: List[Lecture]) -> bool:
        """
        Check if current assignment satisfies all hard constraints

        Args:
            assignment: Dict mapping lecture_var_name -> (timeslot, room, instructor)
            lectures: List of all Lecture objects

        Returns:
            True if all constraints satisfied, False otherwise
        """
        return (self.no_instructor_conflict(assignment) and
                self.no_room_conflict(assignment) and
                self.no_student_conflict(assignment, lectures))

    def no_instructor_conflict(self, assignment: Dict[str, Tuple[str, str, str]]) -> bool:
        """
        HARD CONSTRAINT 1: No instructor teaches two classes at same time

        Args:
            assignment: Current variable assignments

        Returns:
            True if no instructor conflicts, False otherwise
        """
        # Group by instructor and timeslot
        instructor_schedule = {}

        for var_name, (timeslot, room, instructor) in assignment.items():
            key = (instructor, timeslot)
            if key not in instructor_schedule:
                instructor_schedule[key] = []
            instructor_schedule[key].append(var_name)

        # Check for conflicts
        for (instructor, timeslot), lectures in instructor_schedule.items():
            if len(lectures) > 1:
                # Conflict found!
                return False

        return True

    def no_room_conflict(self, assignment: Dict[str, Tuple[str, str, str]]) -> bool:
        """
        HARD CONSTRAINT 2: No room hosts two classes at same time

        Args:
            assignment: Current variable assignments

        Returns:
            True if no room conflicts, False otherwise
        """
        # Group by room and timeslot
        room_schedule = {}

        for var_name, (timeslot, room, instructor) in assignment.items():
            key = (room, timeslot)
            if key not in room_schedule:
                room_schedule[key] = []
            room_schedule[key].append(var_name)

        # Check for conflicts
        for (room, timeslot), lectures in room_schedule.items():
            if len(lectures) > 1:
                # Conflict found!
                return False

        return True

    def no_student_conflict(self,
                            assignment: Dict[str, Tuple[str, str, str]],
                            lectures: List[Lecture]) -> bool:
        """
        HARD CONSTRAINT 3: Students in same section can't have two classes at same time

        Args:
            assignment: Current variable assignments
            lectures: List of all Lecture objects

        Returns:
            True if no student conflicts, False otherwise
        """
        # Build a map of var_name -> section_id
        var_to_section = {}
        for lecture in lectures:
            var_name = lecture.get_variable_name()
            var_to_section[var_name] = lecture.section_id

        # Group by section and timeslot
        section_schedule = {}

        for var_name, (timeslot, room, instructor) in assignment.items():
            section_id = var_to_section.get(var_name)
            if section_id is None:
                continue

            key = (section_id, timeslot)
            if key not in section_schedule:
                section_schedule[key] = []
            section_schedule[key].append(var_name)

        # Check for conflicts
        for (section_id, timeslot), lectures_list in section_schedule.items():
            if len(lectures_list) > 1:
                # Student conflict!
                return False

        return True

    def is_consistent(self,
                      var_name: str,
                      value: Tuple[str, str, str],
                      assignment: Dict[str, Tuple[str, str, str]],
                      lectures: List[Lecture]) -> bool:
        """
        Check if assigning 'value' to 'var_name' is consistent with current assignment
        This is used during search to prune early

        Args:
            var_name: Variable being assigned
            value: The value (timeslot, room, instructor) to assign
            assignment: Current partial assignment
            lectures: List of all Lecture objects

        Returns:
            True if assignment is consistent, False otherwise
        """
        # Create temporary assignment with new value
        temp_assignment = assignment.copy()
        temp_assignment[var_name] = value

        # Check all constraints
        return self.check_all_constraints(temp_assignment, lectures)

    def get_conflicts(self,
                      assignment: Dict[str, Tuple[str, str, str]],
                      lectures: List[Lecture]) -> List[str]:
        """
        Get list of constraint violations (for debugging)

        Returns:
            List of conflict descriptions
        """
        conflicts = []

        # Check instructor conflicts
        instructor_schedule = {}
        for var_name, (timeslot, room, instructor) in assignment.items():
            key = (instructor, timeslot)
            if key not in instructor_schedule:
                instructor_schedule[key] = []
            instructor_schedule[key].append(var_name)

        for (instructor, timeslot), lectures_list in instructor_schedule.items():
            if len(lectures_list) > 1:
                conflicts.append(
                    f"Instructor {instructor} has conflict at {timeslot}: {lectures_list}"
                )

        # Check room conflicts
        room_schedule = {}
        for var_name, (timeslot, room, instructor) in assignment.items():
            key = (room, timeslot)
            if key not in room_schedule:
                room_schedule[key] = []
            room_schedule[key].append(var_name)

        for (room, timeslot), lectures_list in room_schedule.items():
            if len(lectures_list) > 1:
                conflicts.append(
                    f"Room {room} has conflict at {timeslot}: {lectures_list}"
                )

        # Check student conflicts
        var_to_section = {}
        for lecture in lectures:
            var_name = lecture.get_variable_name()
            var_to_section[var_name] = lecture.section_id

        section_schedule = {}
        for var_name, (timeslot, room, instructor) in assignment.items():
            section_id = var_to_section.get(var_name)
            if section_id:
                key = (section_id, timeslot)
                if key not in section_schedule:
                    section_schedule[key] = []
                section_schedule[key].append(var_name)

        for (section_id, timeslot), lectures_list in section_schedule.items():
            if len(lectures_list) > 1:
                conflicts.append(
                    f"Section {section_id} has conflict at {timeslot}: {lectures_list}"
                )

        return conflicts


# Test the constraints
if __name__ == "__main__":
    print("Testing Constraints Module\n")

    from models import Lecture

    # Create some test lectures
    lecture1 = Lecture("AID312", "S1_L1", 1)
    lecture2 = Lecture("PHY113", "S1_L1", 1)
    lecture3 = Lecture("AID312", "S2_L1", 1)

    lectures = [lecture1, lecture2, lecture3]

    # Create test assignments
    print("Test 1: Valid assignment (no conflicts)")
    assignment1 = {
        lecture1.get_variable_name(): ("TS0", "L1", "PROF11"),
        lecture2.get_variable_name(): ("TS1", "L2", "PROF03"),
        lecture3.get_variable_name(): ("TS0", "L3", "PROF11"),
    }

    constraints = TimetableConstraints()
    is_valid = constraints.check_all_constraints(assignment1, lectures)
    print(f"  Valid: {is_valid}")
    print(f"  Conflicts: {constraints.get_conflicts(assignment1, lectures)}\n")

    # Test 2: Instructor conflict
    print("Test 2: Instructor conflict (same instructor, same time)")
    assignment2 = {
        lecture1.get_variable_name(): ("TS0", "L1", "PROF11"),
        lecture2.get_variable_name(): ("TS1", "L2", "PROF03"),
        lecture3.get_variable_name(): ("TS0", "L3", "PROF11"),  # Same as lecture1!
    }

    # But both are different sections, so actually OK...
    # Let's make a real conflict:
    assignment2_conflict = {
        lecture1.get_variable_name(): ("TS0", "L1", "PROF11"),
        lecture2.get_variable_name(): ("TS0", "L2", "PROF11"),  # Same time, same instructor!
    }

    is_valid = constraints.check_all_constraints(assignment2_conflict, lectures)
    print(f"  Valid: {is_valid}")
    conflicts = constraints.get_conflicts(assignment2_conflict, lectures)
    print(f"  Conflicts found: {len(conflicts)}")
    for c in conflicts:
        print(f"    - {c}\n")

    # Test 3: Room conflict
    print("Test 3: Room conflict (same room, same time)")
    assignment3 = {
        lecture1.get_variable_name(): ("TS0", "L1", "PROF11"),
        lecture2.get_variable_name(): ("TS0", "L1", "PROF03"),  # Same room, same time!
    }

    is_valid = constraints.check_all_constraints(assignment3, lectures)
    print(f"  Valid: {is_valid}")
    conflicts = constraints.get_conflicts(assignment3, lectures)
    print(f"  Conflicts found: {len(conflicts)}")
    for c in conflicts:
        print(f"    - {c}\n")

    # Test 4: Student conflict
    print("Test 4: Student conflict (same section, same time)")
    assignment4 = {
        lecture1.get_variable_name(): ("TS0", "L1", "PROF11"),  # S1_L1
        lecture2.get_variable_name(): ("TS0", "L2", "PROF03"),  # S1_L1, same time!
    }

    is_valid = constraints.check_all_constraints(assignment4, lectures)
    print(f"  Valid: {is_valid}")
    conflicts = constraints.get_conflicts(assignment4, lectures)
    print(f"  Conflicts found: {len(conflicts)}")
    for c in conflicts:
        print(f"    - {c}")

    print("\n✅ Constraint testing complete!")