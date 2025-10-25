"""
Problem Builder Module
Creates CSP variables and domains for timetable generation
"""

from data_loader import DataLoader
from models import Course, Instructor, Room, TimeSlot, Section, Lecture
from typing import List, Dict, Tuple
import pandas as pd


class ProblemBuilder:
    """Builds the CSP problem: variables, domains, and constraints"""

    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self.lectures = []  # List of all Lecture objects (CSP variables)
        self.domains = {}  # Dict: lecture_id -> list of (timeslot, room, instructor)

    def build_lectures_for_sections(self, section_ids: List[str]) -> List[Lecture]:
        """
        Create lecture variables for given sections
        Each course needs multiple lectures per week based on credits
        """
        print(f"\n🔨 Building lectures for {len(section_ids)} sections...")
        all_lectures = []

        for section_id in section_ids:
            print(f"\n  Section: {section_id}")

            # Get courses for this section
            course_ids = self.loader.get_section_courses(section_id)
            print(f"    Courses: {', '.join(course_ids)}")

            for course_id in course_ids:
                course_info = self.loader.get_course_info(course_id)
                if course_info is None:
                    print(f"    ⚠️  Warning: Course {course_id} not found")
                    continue

                # Calculate number of lectures needed per week
                credits = course_info['Credits']
                # Typically: 1 credit = 1 lecture, 3 credits = 2 lectures
                num_lectures = self._calculate_lectures_per_week(credits)

                # Create lecture objects
                for lec_num in range(1, num_lectures + 1):
                    lecture = Lecture(
                        course_id=course_id,
                        section_id=section_id,
                        lecture_number=lec_num
                    )
                    all_lectures.append(lecture)

                print(f"    ✓ {course_id}: {num_lectures} lectures/week")

        print(f"\n✅ Created {len(all_lectures)} total lectures")
        self.lectures = all_lectures
        return all_lectures

    def _calculate_lectures_per_week(self, credits: int) -> int:
        """Calculate number of lectures per week based on credits"""
        if credits == 1:
            return 1
        elif credits == 2:
            return 1
        elif credits == 3:
            return 2  # Most 3-credit courses have 2 sessions/week
        elif credits == 4:
            return 2
        elif credits == 5:
            return 3
        else:
            return 2  # Default

    def build_domains(self) -> Dict:
        """
        Build domains for each lecture
        Domain = all possible (timeslot, room, instructor) combinations
        """
        print("\n🎯 Building domains for lectures...")

        for lecture in self.lectures:
            domain = []

            # Get course information
            course_info = self.loader.get_course_info(lecture.course_id)
            if course_info is None:
                continue

            course_type = course_info['Type']

            # Determine room type needed
            if 'Lab' in course_type:
                room_type = 'Lab'
            else:
                room_type = 'Lecture'

            # Get qualified instructors
            qualified_instructors = self.loader.get_qualified_instructors(lecture.course_id)

            if not qualified_instructors:
                print(f"  ⚠️  No instructors for {lecture.course_id}")
                continue

            # Get available rooms
            available_rooms = self.loader.get_rooms_by_type(room_type)

            # Get all timeslots
            timeslots = self.loader.timeslots['TimeSlotID'].tolist()

            # Build domain: all combinations that make sense
            for timeslot_id in timeslots:
                # Get day for this timeslot
                ts_info = self.loader.timeslots[
                    self.loader.timeslots['TimeSlotID'] == timeslot_id
                    ]
                if ts_info.empty:
                    continue
                day = ts_info.iloc[0]['Day']

                for room_id in available_rooms:
                    for instructor_id in qualified_instructors:
                        # Check if instructor is available on this day
                        unavailable_day = self.loader.get_instructor_unavailable_day(instructor_id)
                        if unavailable_day and unavailable_day == day:
                            continue  # Instructor not available

                        # Add to domain
                        domain.append((timeslot_id, room_id, instructor_id))

            # Store domain
            var_name = lecture.get_variable_name()
            self.domains[var_name] = domain

            print(f"  ✓ {var_name}: {len(domain)} possible assignments")

        print(f"\n✅ Domains built for {len(self.domains)} lectures")
        return self.domains

    def get_lecture_by_name(self, var_name: str) -> Lecture:
        """Get lecture object by variable name"""
        for lecture in self.lectures:
            if lecture.get_variable_name() == var_name:
                return lecture
        return None

    def print_problem_summary(self):
        """Print summary of the CSP problem"""
        print("\n" + "=" * 60)
        print("CSP PROBLEM SUMMARY")
        print("=" * 60)
        print(f"Total Variables (Lectures): {len(self.lectures)}")
        print(f"Total Domains Created: {len(self.domains)}")

        if self.domains:
            avg_domain_size = sum(len(d) for d in self.domains.values()) / len(self.domains)
            print(f"Average Domain Size: {avg_domain_size:.0f} assignments")

            min_domain = min(len(d) for d in self.domains.values())
            max_domain = max(len(d) for d in self.domains.values())
            print(f"Domain Size Range: {min_domain} to {max_domain}")

        # Count by section
        sections = {}
        for lecture in self.lectures:
            if lecture.section_id not in sections:
                sections[lecture.section_id] = 0
            sections[lecture.section_id] += 1

        print(f"\nLectures per Section:")
        for section_id, count in sorted(sections.items()):
            print(f"  {section_id}: {count} lectures")

        print("=" * 60 + "\n")


# Test the problem builder
if __name__ == "__main__":
    print("Testing Problem Builder\n")

    # Load data
    loader = DataLoader()
    if not loader.load_all_data():
        print("Failed to load data!")
        exit(1)

    # Create problem builder
    builder = ProblemBuilder(loader)

    # Test with just 2 sections (small test)
    test_sections = ['S1_L1', 'S2_L1']
    print(f"Testing with sections: {test_sections}\n")

    # Build lectures
    lectures = builder.build_lectures_for_sections(test_sections)

    # Build domains
    domains = builder.build_domains()

    # Print summary
    builder.print_problem_summary()

    # Show some example domains
    print("\n📋 Example Domains (first 3 lectures):")
    for i, lecture in enumerate(lectures[:3]):
        var_name = lecture.get_variable_name()
        domain = domains.get(var_name, [])
        print(f"\n{i + 1}. {var_name}")
        print(f"   Domain size: {len(domain)}")
        if domain:
            print(f"   First 3 options:")
            for ts, room, inst in domain[:3]:
                print(f"     - {ts}, {room}, {inst}")