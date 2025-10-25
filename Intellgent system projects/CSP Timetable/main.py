"""
Main Program
Timetable Generation using CSP
Now with GUI and Soft Constraints support!
"""

from data_loader import DataLoader
from problem_builder import ProblemBuilder
from constraints import TimetableConstraints
from solver import TimetableSolver
from soft_constraints import SoftConstraints
import pandas as pd
from typing import Dict, Tuple, List
import sys


class TimetableGenerator:
    """Main class for generating timetables"""

    def __init__(self):
        self.loader = DataLoader()
        self.builder = None
        self.solver = None
        self.solution = None
        self.soft_constraints = None

    def run(self, sections_to_schedule: List[str], timeout: int = 300):
        """
        Generate timetable for given sections

        Args:
            sections_to_schedule: List of section IDs
            timeout: Solver timeout in seconds
        """
        print("=" * 70)
        print(" TIMETABLE GENERATOR - CSP Solver with Soft Constraints")
        print("=" * 70)

        # Step 1: Load data
        print("\n📂 STEP 1: Loading data...")
        if not self.loader.load_all_data():
            print("❌ Failed to load data!")
            return False
        self.loader.print_summary()

        # Step 2: Build CSP problem
        print("\n🔨 STEP 2: Building CSP problem...")
        self.builder = ProblemBuilder(self.loader)
        lectures = self.builder.build_lectures_for_sections(sections_to_schedule)
        domains = self.builder.build_domains()
        self.builder.print_problem_summary()

        # Step 3: Create constraints
        print("\n🔒 STEP 3: Setting up constraints...")
        constraints = TimetableConstraints()
        print("  ✓ Hard constraints initialized")
        print("    - No instructor conflicts")
        print("    - No room conflicts")
        print("    - No student conflicts")

        # Step 4: Solve
        print(f"\n🚀 STEP 4: Solving CSP (timeout: {timeout}s)...")
        self.solver = TimetableSolver(lectures, domains, constraints)
        self.solution = self.solver.solve(timeout=timeout)

        if self.solution:
            print("\n✅ SUCCESS! Timetable generated.")

            # Calculate quality score
            print("\n📊 STEP 5: Evaluating timetable quality...")
            self.soft_constraints = SoftConstraints(self.loader)
            self.soft_constraints.print_quality_report(self.solution, lectures)

            return True
        else:
            print("\n❌ FAILED! Could not generate timetable.")
            return False

    def export_timetable(self, output_file: str = "timetable.csv"):
        """
        Export timetable to CSV file

        Args:
            output_file: Output filename
        """
        if not self.solution:
            print("❌ No solution to export!")
            return

        print(f"\n📊 Exporting timetable to {output_file}...")

        rows = []

        for var_name, (timeslot, room, instructor) in self.solution.items():
            # Parse variable name to get section and course
            lecture = self.builder.get_lecture_by_name(var_name)
            if not lecture:
                continue

            # Get course info
            course_info = self.loader.get_course_info(lecture.course_id)
            course_name = course_info['CourseName'] if course_info else lecture.course_id

            # Get timeslot info
            ts_info = self.loader.timeslots[
                self.loader.timeslots['TimeSlotID'] == timeslot
                ]
            if not ts_info.empty:
                day = ts_info.iloc[0]['Day']
                start_time = ts_info.iloc[0]['StartTime']
                end_time = ts_info.iloc[0]['EndTime']
            else:
                day = start_time = end_time = "Unknown"

            # Get instructor info
            inst_info = self.loader.instructors[
                self.loader.instructors['InstructorID'] == instructor
                ]
            instructor_name = inst_info.iloc[0]['Name'] if not inst_info.empty else instructor

            rows.append({
                'Section': lecture.section_id,
                'Course ID': lecture.course_id,
                'Course Name': course_name,
                'Lecture #': lecture.lecture_number,
                'Day': day,
                'Start Time': start_time,
                'End Time': end_time,
                'Room': room,
                'Instructor': instructor_name
            })

        # Create DataFrame and sort
        df = pd.DataFrame(rows)
        df = df.sort_values(['Section', 'Day', 'Start Time'])

        # Save to CSV
        df.to_csv(output_file, index=False)
        print(f"✅ Exported {len(rows)} lectures to {output_file}")

    def print_timetable_by_section(self):
        """Print timetable organized by section"""
        if not self.solution:
            print("❌ No solution to display!")
            return

        print("\n" + "=" * 70)
        print(" GENERATED TIMETABLE")
        print("=" * 70)

        # Group by section
        by_section = {}
        for var_name, (timeslot, room, instructor) in self.solution.items():
            lecture = self.builder.get_lecture_by_name(var_name)
            if not lecture:
                continue

            if lecture.section_id not in by_section:
                by_section[lecture.section_id] = []

            by_section[lecture.section_id].append((lecture, timeslot, room, instructor))

        # Print each section
        for section_id in sorted(by_section.keys()):
            print(f"\n{'=' * 70}")
            print(f" SECTION: {section_id}")
            print(f"{'=' * 70}")

            # Sort by day and time
            lectures = by_section[section_id]

            # Get timeslot info for sorting
            def get_sort_key(item):
                lecture, timeslot, room, instructor = item
                ts_info = self.loader.timeslots[
                    self.loader.timeslots['TimeSlotID'] == timeslot
                    ]
                if not ts_info.empty:
                    day_order = {'Sunday': 0, 'Monday': 1, 'Tuesday': 2,
                                 'Wednesday': 3, 'Thursday': 4}
                    day = ts_info.iloc[0]['Day']
                    return (day_order.get(day, 5), timeslot)
                return (5, timeslot)

            lectures.sort(key=get_sort_key)

            # Print lectures
            for lecture, timeslot, room, instructor in lectures:
                # Get course info
                course_info = self.loader.get_course_info(lecture.course_id)
                course_name = course_info['CourseName'] if course_info else lecture.course_id

                # Get timeslot info
                ts_info = self.loader.timeslots[
                    self.loader.timeslots['TimeSlotID'] == timeslot
                    ]
                if not ts_info.empty:
                    day = ts_info.iloc[0]['Day']
                    start_time = ts_info.iloc[0]['StartTime']
                    end_time = ts_info.iloc[0]['EndTime']
                    time_str = f"{day:10} {start_time:10} - {end_time:10}"
                else:
                    time_str = timeslot

                # Get instructor info
                inst_info = self.loader.instructors[
                    self.loader.instructors['InstructorID'] == instructor
                    ]
                instructor_name = inst_info.iloc[0]['Name'] if not inst_info.empty else instructor

                print(f"{time_str} | {room:6} | {lecture.course_id:10} | {instructor_name}")

        print("\n" + "=" * 70 + "\n")

    def print_statistics(self):
        """Print statistics about the generated timetable"""
        if not self.solution or not self.solver:
            return

        stats = self.solver.get_solution_statistics()

        print("\n" + "=" * 70)
        print(" STATISTICS")
        print("=" * 70)
        print(f"Total lectures scheduled: {stats['total_assigned']}")
        print(f"Timeslots used: {len(stats['timeslot_usage'])}/20")
        print(f"Instructors used: {len(stats['instructor_load'])}")
        print(f"Rooms used: {len(stats['room_usage'])}")

        # Most used timeslots
        print("\nMost used timeslots:")
        sorted_ts = sorted(stats['timeslot_usage'].items(),
                           key=lambda x: x[1], reverse=True)[:5]
        for ts, count in sorted_ts:
            print(f"  {ts}: {count} lectures")

        # Instructor load
        print("\nInstructor load (top 5):")
        sorted_inst = sorted(stats['instructor_load'].items(),
                             key=lambda x: x[1], reverse=True)[:5]
        for instructor, count in sorted_inst:
            inst_info = self.loader.instructors[
                self.loader.instructors['InstructorID'] == instructor
                ]
            name = inst_info.iloc[0]['Name'] if not inst_info.empty else instructor
            print(f"  {name}: {count} lectures")

        print("=" * 70 + "\n")


def main():
    """Main entry point"""

    # Ask user for interface preference
    print("\n" + "=" * 70)
    print(" TIMETABLE GENERATOR - Choose Interface")
    print("=" * 70)
    print("\nSelect interface:")
    print("  1. GUI (Graphical Interface) - Recommended ⭐")
    print("  2. CLI (Command Line Interface)")
    print("  3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        # Launch GUI
        print("\n🚀 Launching GUI...")
        try:
            from gui import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"\n❌ GUI not available: {e}")
            print("Make sure tkinter is installed.")
            print("Falling back to CLI...\n")
            run_cli()
        except Exception as e:
            print(f"\n❌ Error launching GUI: {e}")
            print("Falling back to CLI...\n")
            run_cli()

    elif choice == "2":
        # Run CLI
        run_cli()

    elif choice == "3":
        print("Goodbye!")
        return

    else:
        print("Invalid choice! Using CLI.")
        run_cli()


def run_cli():
    """Run command-line interface"""
    generator = TimetableGenerator()

    print("\n" + "=" * 70)
    print(" SELECT SECTIONS TO SCHEDULE")
    print("=" * 70)
    print("\nOptions:")
    print("  1. Level 1 only (12 sections)")
    print("  2. Level 1 + Level 2 (21 sections)")
    print("  3. Test mode (2 sections) ⭐")
    print("  4. Custom selection")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        sections = [f'S{i}_L1' for i in range(1, 13)]
        timeout = 600  # 10 minutes
    elif choice == "2":
        sections = [f'S{i}_L1' for i in range(1, 13)] + [f'S{i}_L2' for i in range(1, 10)]
        timeout = 900  # 15 minutes
    elif choice == "3":
        sections = ['S1_L1', 'S2_L1']
        timeout = 120  # 2 minutes
    elif choice == "4":
        sections_input = input("Enter section IDs (comma-separated): ").strip()
        sections = [s.strip() for s in sections_input.split(',')]
        timeout = 300  # 5 minutes
    else:
        print("Invalid choice! Using test mode.")
        sections = ['S1_L1', 'S2_L1']
        timeout = 120

    print(f"\n✓ Will schedule {len(sections)} sections: {', '.join(sections)}")
    print(f"✓ Timeout: {timeout} seconds")

    proceed = input("\nProceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Cancelled.")
        return

    # Run the generator
    success = generator.run(sections, timeout=timeout)

    if success:
        # Display results
        generator.print_timetable_by_section()
        generator.print_statistics()

        # Export
        export = input("\nExport to CSV? (y/n): ").strip().lower()
        if export == 'y':
            filename = input("Enter filename (default: timetable.csv): ").strip()
            if not filename:
                filename = "timetable.csv"
            generator.export_timetable(filename)

        print("\n✅ Done!")
    else:
        print("\n❌ Failed to generate timetable.")
        print("Tips:")
        print("  - Try fewer sections")
        print("  - Increase timeout")
        print("  - Check if data is correct")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)