"""
Soft Constraints Module
Implements preferences and quality metrics for timetable optimization
These are "nice to have" but not required like hard constraints
"""

from typing import Dict, Tuple, List
from models import Lecture
from data_loader import DataLoader


class SoftConstraints:
    """Evaluates timetable quality based on soft constraints"""

    def __init__(self, loader: DataLoader):
        self.loader = loader

        # Weight for each soft constraint (adjust these!)
        self.weights = {
            'no_gaps': 10,  # Penalty for gaps in student schedule
            'balanced_days': 5,  # Bonus for evenly distributed schedule
            'avoid_early': 3,  # Penalty for 9am classes
            'avoid_late': 3,  # Penalty for last slot
            'consecutive_rooms': 8,  # Penalty for distant consecutive classes
        }

    def calculate_quality_score(self,
                                assignment: Dict[str, Tuple[str, str, str]],
                                lectures: List[Lecture]) -> float:
        """
        Calculate overall quality score (higher is better)

        Args:
            assignment: Current timetable assignment
            lectures: List of all Lecture objects

        Returns:
            Quality score (higher = better timetable)
        """
        score = 1000.0  # Start with base score

        # Calculate each soft constraint
        score -= self._calculate_gap_penalty(assignment, lectures)
        score += self._calculate_balance_bonus(assignment, lectures)
        score -= self._calculate_time_preference_penalty(assignment)
        score -= self._calculate_room_distance_penalty(assignment, lectures)

        return score

    def _calculate_gap_penalty(self,
                               assignment: Dict[str, Tuple[str, str, str]],
                               lectures: List[Lecture]) -> float:
        """
        Penalty for gaps in student schedules
        Students prefer no free periods between classes
        """
        penalty = 0.0

        # Group by section and day
        section_schedules = self._group_by_section_and_day(assignment, lectures)

        for (section_id, day), timeslots in section_schedules.items():
            # Sort timeslots
            sorted_slots = sorted(timeslots)

            # Count gaps (empty slots between classes)
            if len(sorted_slots) > 1:
                # Get all timeslots for this day
                day_slots = self.loader.get_available_timeslots_for_day(day)

                # Find gaps
                for i in range(len(sorted_slots) - 1):
                    current_idx = day_slots.index(sorted_slots[i])
                    next_idx = day_slots.index(sorted_slots[i + 1])

                    gap_size = next_idx - current_idx - 1
                    if gap_size > 0:
                        penalty += gap_size * self.weights['no_gaps']

        return penalty

    def _calculate_balance_bonus(self,
                                 assignment: Dict[str, Tuple[str, str, str]],
                                 lectures: List[Lecture]) -> float:
        """
        Bonus for evenly distributing classes across the week
        Avoid having all classes on 2-3 days
        """
        bonus = 0.0

        # Group by section
        section_schedules = {}
        for var_name, (timeslot, room, instructor) in assignment.items():
            lecture = next((l for l in lectures if l.get_variable_name() == var_name), None)
            if not lecture:
                continue

            if lecture.section_id not in section_schedules:
                section_schedules[lecture.section_id] = {}

            # Get day
            ts_info = self.loader.timeslots[
                self.loader.timeslots['TimeSlotID'] == timeslot
                ]
            if not ts_info.empty:
                day = ts_info.iloc[0]['Day']
                if day not in section_schedules[lecture.section_id]:
                    section_schedules[lecture.section_id][day] = 0
                section_schedules[lecture.section_id][day] += 1

        # Calculate distribution for each section
        for section_id, day_counts in section_schedules.items():
            if not day_counts:
                continue

            # Calculate standard deviation
            values = list(day_counts.values())
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5

            # Lower std dev = more balanced = higher bonus
            balance_score = max(0, 5 - std_dev)
            bonus += balance_score * self.weights['balanced_days']

        return bonus

    def _calculate_time_preference_penalty(self,
                                           assignment: Dict[str, Tuple[str, str, str]]) -> float:
        """
        Penalty for undesirable time slots
        Most students don't like 9am or late afternoon
        """
        penalty = 0.0

        # Define undesirable slots
        early_slots = ['TS0', 'TS4', 'TS8', 'TS12', 'TS16']  # 9:00 AM slots
        late_slots = ['TS3', 'TS7', 'TS11', 'TS15', 'TS19']  # 2:15 PM slots

        for var_name, (timeslot, room, instructor) in assignment.items():
            if timeslot in early_slots:
                penalty += self.weights['avoid_early']
            if timeslot in late_slots:
                penalty += self.weights['avoid_late']

        return penalty

    def _calculate_room_distance_penalty(self,
                                         assignment: Dict[str, Tuple[str, str, str]],
                                         lectures: List[Lecture]) -> float:
        """
        Penalty for consecutive classes in distant rooms
        Students/instructors prefer nearby rooms for back-to-back classes
        """
        penalty = 0.0

        # Group by section and instructor
        section_schedules = self._group_by_section_and_day(assignment, lectures)
        instructor_schedules = self._group_by_instructor_and_day(assignment)

        # Check section schedules
        for (section_id, day), schedule in section_schedules.items():
            penalty += self._check_consecutive_room_distance(schedule, assignment)

        # Check instructor schedules
        for (instructor_id, day), schedule in instructor_schedules.items():
            penalty += self._check_consecutive_room_distance(schedule, assignment)

        return penalty

    def _check_consecutive_room_distance(self,
                                         timeslots: List[str],
                                         assignment: Dict[str, Tuple[str, str, str]]) -> float:
        """Check if consecutive classes are in distant rooms"""
        penalty = 0.0

        if len(timeslots) < 2:
            return 0.0

        sorted_slots = sorted(timeslots)

        # Get all timeslot IDs in order
        all_slots = [f'TS{i}' for i in range(20)]

        # Check each pair of consecutive classes
        for i in range(len(sorted_slots) - 1):
            current_idx = all_slots.index(sorted_slots[i])
            next_idx = all_slots.index(sorted_slots[i + 1])

            # If classes are consecutive (no gap)
            if next_idx == current_idx + 1:
                # Get rooms
                current_room = None
                next_room = None

                for var_name, (ts, room, inst) in assignment.items():
                    if ts == sorted_slots[i]:
                        current_room = room
                    if ts == sorted_slots[i + 1]:
                        next_room = room

                if current_room and next_room:
                    distance = self._calculate_room_distance(current_room, next_room)
                    if distance > 2:  # If rooms are "far"
                        penalty += distance * self.weights['consecutive_rooms']

        return penalty

    def _calculate_room_distance(self, room1: str, room2: str) -> int:
        """
        Calculate abstract distance between rooms
        Simple heuristic: same building = 0, different = 3
        """
        if room1 == room2:
            return 0

        # Extract room type/number
        r1_type = room1[0]  # 'R' or 'L'
        r2_type = room2[0]

        if r1_type == r2_type:
            # Same type (both labs or both rooms)
            try:
                r1_num = int(room1[1:])
                r2_num = int(room2[1:])
                return abs(r1_num - r2_num) // 5  # Nearby rooms
            except:
                return 1
        else:
            # Different types (lab vs room)
            return 3

    def _group_by_section_and_day(self,
                                  assignment: Dict[str, Tuple[str, str, str]],
                                  lectures: List[Lecture]) -> Dict[Tuple[str, str], List[str]]:
        """Group timeslots by section and day"""
        grouped = {}

        for var_name, (timeslot, room, instructor) in assignment.items():
            lecture = next((l for l in lectures if l.get_variable_name() == var_name), None)
            if not lecture:
                continue

            # Get day
            ts_info = self.loader.timeslots[
                self.loader.timeslots['TimeSlotID'] == timeslot
                ]
            if not ts_info.empty:
                day = ts_info.iloc[0]['Day']
                key = (lecture.section_id, day)

                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(timeslot)

        return grouped

    def _group_by_instructor_and_day(self,
                                     assignment: Dict[str, Tuple[str, str, str]]) -> Dict[Tuple[str, str], List[str]]:
        """Group timeslots by instructor and day"""
        grouped = {}

        for var_name, (timeslot, room, instructor) in assignment.items():
            # Get day
            ts_info = self.loader.timeslots[
                self.loader.timeslots['TimeSlotID'] == timeslot
                ]
            if not ts_info.empty:
                day = ts_info.iloc[0]['Day']
                key = (instructor, day)

                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(timeslot)

        return grouped

    def print_quality_report(self,
                             assignment: Dict[str, Tuple[str, str, str]],
                             lectures: List[Lecture]):
        """Print detailed quality report"""
        print("\n" + "=" * 70)
        print(" TIMETABLE QUALITY REPORT")
        print("=" * 70)

        total_score = self.calculate_quality_score(assignment, lectures)

        gap_penalty = self._calculate_gap_penalty(assignment, lectures)
        balance_bonus = self._calculate_balance_bonus(assignment, lectures)
        time_penalty = self._calculate_time_preference_penalty(assignment)
        room_penalty = self._calculate_room_distance_penalty(assignment, lectures)

        print(f"\n📊 Overall Quality Score: {total_score:.2f}/1000")
        print(f"\nBreakdown:")
        print(f"  Base Score:              1000.00")
        print(f"  - Gap Penalty:          -{gap_penalty:.2f}")
        print(f"  + Balance Bonus:        +{balance_bonus:.2f}")
        print(f"  - Time Preference:      -{time_penalty:.2f}")
        print(f"  - Room Distance:        -{room_penalty:.2f}")
        print(f"  {'=' * 40}")
        print(f"  Final Score:            {total_score:.2f}")

        # Quality rating
        if total_score >= 900:
            rating = "⭐⭐⭐⭐⭐ Excellent"
        elif total_score >= 800:
            rating = "⭐⭐⭐⭐ Good"
        elif total_score >= 700:
            rating = "⭐⭐⭐ Fair"
        elif total_score >= 600:
            rating = "⭐⭐ Acceptable"
        else:
            rating = "⭐ Needs Improvement"

        print(f"\n🏆 Rating: {rating}")
        print("=" * 70 + "\n")


# Test soft constraints
if __name__ == "__main__":
    print("Testing Soft Constraints\n")

    from data_loader import DataLoader
    from models import Lecture

    # Load data
    loader = DataLoader()
    if not loader.load_all_data():
        exit(1)

    # Create test assignment
    lecture1 = Lecture("AID312", "S1_L1", 1)
    lecture2 = Lecture("PHY113", "S1_L1", 1)
    lecture3 = Lecture("LRA101", "S1_L1", 1)

    lectures = [lecture1, lecture2, lecture3]

    # Assignment with gaps
    assignment_with_gaps = {
        lecture1.get_variable_name(): ("TS0", "L1", "PROF11"),  # Sunday 9am
        lecture2.get_variable_name(): ("TS2", "L2", "PROF03"),  # Sunday 12:30pm (gap!)
        lecture3.get_variable_name(): ("TS1", "R101", "PROF04"),  # Sunday 10:45am
    }

    # Better assignment (no gaps)
    assignment_no_gaps = {
        lecture1.get_variable_name(): ("TS0", "L1", "PROF11"),  # Sunday 9am
        lecture2.get_variable_name(): ("TS1", "L2", "PROF03"),  # Sunday 10:45am
        lecture3.get_variable_name(): ("TS4", "R101", "PROF04"),  # Monday 9am
    }

    # Test
    soft = SoftConstraints(loader)

    print("Test 1: Assignment with gaps")
    soft.print_quality_report(assignment_with_gaps, lectures)

    print("\nTest 2: Better assignment (no gaps)")
    soft.print_quality_report(assignment_no_gaps, lectures)