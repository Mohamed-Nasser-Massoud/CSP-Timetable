"""
Data Loader Module
Loads CSV files and prepares data for the timetable CSP solver
"""

import pandas as pd
from typing import Dict, List


class DataLoader:
    """Loads and processes all CSV data files"""

    def __init__(self, data_folder='data'):
        self.data_folder = data_folder
        self.courses = None
        self.instructors = None
        self.rooms = None
        self.timeslots = None
        self.sections = None

    def load_all_data(self) -> bool:
        """Load all CSV files"""
        try:
            print("Loading data files...")

            # Load Courses
            self.courses = pd.read_csv(f'{self.data_folder}/Courses (1).csv')
            self.courses.columns = self.courses.columns.str.strip()
            print(f"✓ Loaded {len(self.courses)} courses")

            # Load Instructors
            self.instructors = pd.read_csv(f'{self.data_folder}/Instructor (1).csv')
            self.instructors.columns = self.instructors.columns.str.strip()
            print(f"✓ Loaded {len(self.instructors)} instructors")

            # Load Rooms
            self.rooms = pd.read_csv(f'{self.data_folder}/Rooms.csv')
            self.rooms.columns = self.rooms.columns.str.strip()
            print(f"✓ Loaded {len(self.rooms)} rooms")

            # Load TimeSlots
            self.timeslots = pd.read_csv(f'{self.data_folder}/TimeSlots (1).csv')
            self.timeslots.columns = self.timeslots.columns.str.strip()
            print(f"✓ Loaded {len(self.timeslots)} timeslots")

            # Load Sections
            self.sections = pd.read_csv(f'{self.data_folder}/Sections.csv')
            self.sections.columns = self.sections.columns.str.strip()
            print(f"✓ Loaded {len(self.sections)} sections")

            return True

        except FileNotFoundError as e:
            print(f"❌ Error: Could not find file - {e}")
            print(f"\nMake sure all CSV files are in the '{self.data_folder}/' folder!")
            return False
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def get_course_info(self, course_id: str) -> Dict:
        """Get information about a specific course"""
        course = self.courses[self.courses['CourseID'] == course_id]
        if course.empty:
            return None
        return course.iloc[0].to_dict()

    def get_qualified_instructors(self, course_id: str) -> List[str]:
        """Get list of instructors qualified to teach a course"""
        qualified = []
        for _, instructor in self.instructors.iterrows():
            qualified_courses = str(instructor['QualifiedCourses']).split(',')
            qualified_courses = [c.strip() for c in qualified_courses]
            if course_id in qualified_courses:
                qualified.append(instructor['InstructorID'])
        return qualified

    def get_instructor_unavailable_day(self, instructor_id: str) -> str:
        """Get the day when instructor is not available"""
        instructor = self.instructors[
            self.instructors['InstructorID'] == instructor_id
        ]
        if instructor.empty:
            return None
        pref = str(instructor.iloc[0]['PreferredSlots'])
        if 'Not on' in pref:
            return pref.replace('Not on ', '').strip()
        return None

    def get_available_timeslots_for_day(self, day: str) -> List[str]:
        """Get all timeslot IDs for a specific day"""
        day_slots = self.timeslots[self.timeslots['Day'] == day]
        return day_slots['TimeSlotID'].tolist()

    def get_rooms_by_type(self, room_type: str) -> List[str]:
        """Get all rooms of a specific type (Lab/Lecture)"""
        filtered = self.rooms[self.rooms['Type'] == room_type]
        return filtered['RoomID'].tolist()

    def get_section_courses(self, section_id: str) -> List[str]:
        """Get list of courses for a section"""
        section = self.sections[self.sections['SectionID'] == section_id]
        if section.empty:
            return []
        courses_str = str(section.iloc[0]['Courses'])
        return [c.strip() for c in courses_str.split(',')]

    def print_summary(self):
        """Print a summary of loaded data"""
        if self.courses is None:
            print("No data loaded yet!")
            return

        print("\n" + "="*50)
        print("DATA SUMMARY")
        print("="*50)
        print(f"Total Courses: {len(self.courses)}")
        print(f"Total Instructors: {len(self.instructors)}")
        print(f"Total Rooms: {len(self.rooms)}")
        print(f"  - Lecture Rooms: {len(self.rooms[self.rooms['Type']=='Lecture'])}")
        print(f"  - Lab Rooms: {len(self.rooms[self.rooms['Type']=='Lab'])}")
        print(f"Total Time Slots: {len(self.timeslots)}")
        print(f"Total Sections: {len(self.sections)}")
        print("="*50 + "\n")


# Test the loader
if __name__ == "__main__":
    loader = DataLoader()
    if loader.load_all_data():
        loader.print_summary()

        # Test some queries
        print("\nTest Queries:")
        print(f"AID312 info: {loader.get_course_info('AID312')}")
        print(f"Instructors for AID312: {loader.get_qualified_instructors('AID312')}")
        print(f"Sunday timeslots: {loader.get_available_timeslots_for_day('Sunday')}")
