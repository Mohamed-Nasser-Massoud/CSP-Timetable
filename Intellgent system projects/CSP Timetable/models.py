"""
Data Models for Timetable CSP
Defines classes to represent courses, instructors, rooms, etc.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Course:
    """Represents a course"""
    course_id: str
    course_name: str
    credits: int
    type: str  # 'Lecture' or 'Lecture and Lab'

    def needs_lab(self) -> bool:
        """Check if course needs a lab room"""
        return 'Lab' in self.type


@dataclass
class Instructor:
    """Represents an instructor"""
    instructor_id: str
    name: str
    role: str
    unavailable_day: Optional[str]
    qualified_courses: List[str]

    def can_teach(self, course_id: str) -> bool:
        """Check if instructor can teach a course"""
        return course_id in self.qualified_courses

    def is_available_on_day(self, day: str) -> bool:
        """Check if instructor is available on a given day"""
        if self.unavailable_day is None:
            return True
        return self.unavailable_day != day


@dataclass
class Room:
    """Represents a classroom or lab"""
    room_id: str
    type: str  # 'Lecture' or 'Lab'
    capacity: int


@dataclass
class TimeSlot:
    """Represents a time slot"""
    timeslot_id: str
    day: str
    start_time: str
    end_time: str

    def __str__(self):
        return f"{self.day} {self.start_time}-{self.end_time}"


@dataclass
class Section:
    """Represents a student section"""
    section_id: str
    student_count: int
    courses: List[str]


@dataclass
class Lecture:
    """Represents a scheduled lecture (CSP Variable)"""
    course_id: str
    section_id: str
    lecture_number: int  # 1st, 2nd, 3rd lecture of the week

    # Assignment (CSP solution)
    timeslot_id: Optional[str] = None
    room_id: Optional[str] = None
    instructor_id: Optional[str] = None

    def is_assigned(self) -> bool:
        """Check if lecture has been scheduled"""
        return all([
            self.timeslot_id is not None,
            self.room_id is not None,
            self.instructor_id is not None
        ])

    def get_variable_name(self) -> str:
        """Get unique identifier for this lecture"""
        return f"{self.section_id}_{self.course_id}_L{self.lecture_number}"

    def __str__(self):
        if self.is_assigned():
            return (f"{self.section_id} - {self.course_id} "
                    f"[{self.timeslot_id}, {self.room_id}, {self.instructor_id}]")
        return f"{self.section_id} - {self.course_id} (unassigned)"


@dataclass
class TimetableEntry:
    """Represents one entry in the final timetable"""
    section_id: str
    course_id: str
    course_name: str
    instructor_name: str
    room_id: str
    day: str
    start_time: str
    end_time: str

    def __str__(self):
        return (f"{self.day} {self.start_time}-{self.end_time} | "
                f"{self.course_name} | {self.instructor_name} | {self.room_id}")


if __name__ == "__main__":
    # Test creating objects
    course = Course("AID312", "Intelligent Systems", 3, "Lecture and Lab")
    print(f"Course needs lab: {course.needs_lab()}")

    instructor = Instructor("PROF01", "Dr. Reda", "Professor",
                            "Tuesday", ["AID312", "ECE223"])
    print(f"Can teach AID312: {instructor.can_teach('AID312')}")
    print(f"Available Monday: {instructor.is_available_on_day('Monday')}")
    print(f"Available Tuesday: {instructor.is_available_on_day('Tuesday')}")

    lecture = Lecture("AID312", "S1_AID_L3", 1)
    print(f"Lecture assigned: {lecture.is_assigned()}")
    print(f"Variable name: {lecture.get_variable_name()}")