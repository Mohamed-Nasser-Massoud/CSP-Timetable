"""
GUI Module - Graphical User Interface for Timetable Generator
Uses Tkinter for cross-platform GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import queue
from typing import List

from data_loader import DataLoader
from problem_builder import ProblemBuilder
from constraints import TimetableConstraints
from solver import TimetableSolver
from soft_constraints import SoftConstraints


class TimetableGUI:
    """Main GUI application for timetable generation"""

    def __init__(self, root):
        self.root = root
        self.root.title("🎓 Timetable Generator - CSP Solver")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Data
        self.loader = None
        self.solution = None
        self.lectures = None
        self.solver = None
        self.quality_score = None

        # Threading
        self.solver_thread = None
        self.message_queue = queue.Queue()

        # Create GUI
        self.create_widgets()

        # Load data automatically
        self.load_data()

    def create_widgets(self):
        """Create all GUI widgets"""

        # ===== Title =====
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🎓 Automated Timetable Generator",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)

        # ===== Main Container =====
        main_container = tk.Frame(self.root, bg="#ecf0f1")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== Left Panel (Configuration) =====
        left_panel = tk.LabelFrame(
            main_container,
            text="⚙️ Configuration",
            font=("Arial", 12, "bold"),
            bg="#ecf0f1",
            padx=10,
            pady=10
        )
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))

        # Data Status
        self.data_status_label = tk.Label(
            left_panel,
            text="📂 Status: Not Loaded",
            font=("Arial", 10),
            bg="#ecf0f1",
            anchor="w"
        )
        self.data_status_label.pack(fill=tk.X, pady=5)

        tk.Button(
            left_panel,
            text="🔄 Reload Data",
            command=self.load_data,
            bg="#3498db",
            fg="white",
            font=("Arial", 10),
            cursor="hand2"
        ).pack(fill=tk.X, pady=5)

        # Section Selection
        tk.Label(
            left_panel,
            text="📚 Select Sections:",
            font=("Arial", 11, "bold"),
            bg="#ecf0f1",
            anchor="w"
        ).pack(fill=tk.X, pady=(15, 5))

        # Preset buttons
        preset_frame = tk.Frame(left_panel, bg="#ecf0f1")
        preset_frame.pack(fill=tk.X, pady=5)

        tk.Button(
            preset_frame,
            text="Test (2)",
            command=lambda: self.select_preset("test"),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        tk.Button(
            preset_frame,
            text="Level 1 (12)",
            command=lambda: self.select_preset("level1"),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        tk.Button(
            preset_frame,
            text="All (38)",
            command=lambda: self.select_preset("all"),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        # Listbox for section selection
        listbox_frame = tk.Frame(left_panel, bg="#ecf0f1")
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.section_listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=scrollbar.set,
            font=("Courier", 9),
            height=15
        )
        self.section_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.section_listbox.yview)

        # Timeout setting
        tk.Label(
            left_panel,
            text="⏱️ Timeout (seconds):",
            font=("Arial", 10),
            bg="#ecf0f1",
            anchor="w"
        ).pack(fill=tk.X, pady=(10, 2))

        self.timeout_var = tk.IntVar(value=300)
        timeout_spinbox = tk.Spinbox(
            left_panel,
            from_=60,
            to=3600,
            increment=60,
            textvariable=self.timeout_var,
            font=("Arial", 10),
            width=10
        )
        timeout_spinbox.pack(fill=tk.X)

        # Generate Button
        self.generate_btn = tk.Button(
            left_panel,
            text="🚀 Generate Timetable",
            command=self.start_generation,
            bg="#27ae60",
            fg="white",
            font=("Arial", 12, "bold"),
            cursor="hand2",
            height=2
        )
        self.generate_btn.pack(fill=tk.X, pady=(20, 5))

        # Stop Button
        self.stop_btn = tk.Button(
            left_panel,
            text="⏹️ Stop",
            command=self.stop_generation,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10),
            cursor="hand2",
            state=tk.DISABLED
        )
        self.stop_btn.pack(fill=tk.X, pady=5)

        # Export Button
        self.export_btn = tk.Button(
            left_panel,
            text="💾 Export to CSV",
            command=self.export_timetable,
            bg="#f39c12",
            fg="white",
            font=("Arial", 10),
            cursor="hand2",
            state=tk.DISABLED
        )
        self.export_btn.pack(fill=tk.X, pady=5)

        # ===== Right Panel (Output) =====
        right_panel = tk.Frame(main_container, bg="#ecf0f1")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Tabs
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Console Output
        console_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(console_tab, text="📟 Console")

        self.console = scrolledtext.ScrolledText(
            console_tab,
            font=("Courier", 9),
            bg="#1e1e1e",
            fg="#00ff00",
            wrap=tk.WORD
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 2: Timetable View
        timetable_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(timetable_tab, text="📅 Timetable")

        self.timetable_text = scrolledtext.ScrolledText(
            timetable_tab,
            font=("Courier", 9),
            wrap=tk.WORD
        )
        self.timetable_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 3: Statistics
        stats_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(stats_tab, text="📊 Statistics")

        self.stats_text = scrolledtext.ScrolledText(
            stats_tab,
            font=("Courier", 10),
            wrap=tk.WORD
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== Status Bar =====
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#34495e",
            fg="white",
            font=("Arial", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            mode='indeterminate',
            length=200
        )

        # Start checking queue
        self.check_queue()

    def log(self, message: str):
        """Log message to console"""
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.root.update_idletasks()

    def load_data(self):
        """Load CSV data"""
        self.log("📂 Loading data files...")
        self.loader = DataLoader()

        if self.loader.load_all_data():
            self.log("✅ Data loaded successfully!")
            self.data_status_label.config(
                text=f"📂 Status: ✅ Loaded ({len(self.loader.sections)} sections)",
                fg="green"
            )
            self.populate_sections()
        else:
            self.log("❌ Failed to load data!")
            self.data_status_label.config(
                text="📂 Status: ❌ Error",
                fg="red"
            )
            messagebox.showerror("Error", "Failed to load data files!")

    def populate_sections(self):
        """Populate section listbox"""
        self.section_listbox.delete(0, tk.END)

        if self.loader and self.loader.sections is not None:
            sections = self.loader.sections['SectionID'].tolist()
            for section in sections:
                self.section_listbox.insert(tk.END, section)

    def select_preset(self, preset: str):
        """Select preset sections"""
        self.section_listbox.selection_clear(0, tk.END)

        if preset == "test":
            sections = ['S1_L1', 'S2_L1']
        elif preset == "level1":
            sections = [f'S{i}_L1' for i in range(1, 13)]
        elif preset == "all":
            sections = self.loader.sections['SectionID'].tolist() if self.loader else []
        else:
            return

        # Select in listbox
        for i, section in enumerate(self.section_listbox.get(0, tk.END)):
            if section in sections:
                self.section_listbox.selection_set(i)

        self.log(f"✓ Selected {len(sections)} sections: {preset}")

    def get_selected_sections(self) -> List[str]:
        """Get selected sections from listbox"""
        indices = self.section_listbox.curselection()
        return [self.section_listbox.get(i) for i in indices]

    def start_generation(self):
        """Start timetable generation in background thread"""
        sections = self.get_selected_sections()

        if not sections:
            messagebox.showwarning("Warning", "Please select at least one section!")
            return

        if not self.loader:
            messagebox.showerror("Error", "Data not loaded!")
            return

        # Disable buttons
        self.generate_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)

        # Clear outputs
        self.console.delete(1.0, tk.END)
        self.timetable_text.delete(1.0, tk.END)
        self.stats_text.delete(1.0, tk.END)

        # Start progress
        self.progress.pack(side=tk.BOTTOM, before=self.status_bar, fill=tk.X)
        self.progress.start(10)

        self.status_bar.config(text=f"🔄 Generating timetable for {len(sections)} sections...")

        # Start solver thread
        timeout = self.timeout_var.get()
        self.solver_thread = threading.Thread(
            target=self.run_solver,
            args=(sections, timeout),
            daemon=True
        )
        self.solver_thread.start()

    def run_solver(self, sections: List[str], timeout: int):
        """Run solver in background thread"""
        try:
            # Build problem
            self.message_queue.put(("log", f"\n🔨 Building CSP problem for {len(sections)} sections..."))

            builder = ProblemBuilder(self.loader)
            lectures = builder.build_lectures_for_sections(sections)
            domains = builder.build_domains()

            self.message_queue.put(("log", f"✅ Created {len(lectures)} lectures"))
            self.message_queue.put(("log", f"✅ Built {len(domains)} domains\n"))

            # Create constraints
            constraints = TimetableConstraints()

            # Solve
            self.message_queue.put(("log", f"🚀 Starting solver (timeout: {timeout}s)...\n"))

            solver = TimetableSolver(lectures, domains, constraints)
            solution = solver.solve(timeout=timeout)

            self.lectures = lectures
            self.solver = solver
            self.solution = solution

            if solution:
                self.message_queue.put(("log", "\n✅ SOLUTION FOUND!"))
                self.message_queue.put(("success", None))
            else:
                self.message_queue.put(("log", "\n❌ NO SOLUTION FOUND"))
                self.message_queue.put(("failure", None))

        except Exception as e:
            self.message_queue.put(("log", f"\n❌ Error: {str(e)}"))
            self.message_queue.put(("error", str(e)))

    def stop_generation(self):
        """Stop solver (not perfectly implemented, would need better thread control)"""
        self.log("\n⚠️ Stopping solver...")
        self.status_bar.config(text="Stopped by user")
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def check_queue(self):
        """Check message queue from solver thread"""
        try:
            while True:
                msg_type, msg_data = self.message_queue.get_nowait()

                if msg_type == "log":
                    self.log(msg_data)
                elif msg_type == "success":
                    self.on_solution_found()
                elif msg_type == "failure":
                    self.on_solution_failed()
                elif msg_type == "error":
                    self.on_error(msg_data)

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.check_queue)

    def on_solution_found(self):
        """Handle successful solution"""
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.NORMAL)

        self.status_bar.config(text="✅ Timetable generated successfully!")

        # Show timetable
        self.display_timetable()

        # Show statistics
        self.display_statistics()

        # Calculate quality score
        self.calculate_quality()

        # Switch to timetable tab
        self.notebook.select(1)

        messagebox.showinfo("Success", "✅ Timetable generated successfully!")

    def on_solution_failed(self):
        """Handle failed solution"""
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        self.status_bar.config(text="❌ Failed to generate timetable")

        messagebox.showwarning(
            "No Solution",
            "Could not find a valid timetable.\n\nTry:\n- Fewer sections\n- Longer timeout\n- Check data constraints"
        )

    def on_error(self, error_msg: str):
        """Handle error"""
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        self.status_bar.config(text="❌ Error occurred")

        messagebox.showerror("Error", f"An error occurred:\n\n{error_msg}")

    def display_timetable(self):
        """Display generated timetable"""
        self.timetable_text.delete(1.0, tk.END)

        if not self.solution:
            return

        # Group by section
        by_section = {}
        for var_name, (timeslot, room, instructor) in self.solution.items():
            lecture = next((l for l in self.lectures if l.get_variable_name() == var_name), None)
            if not lecture:
                continue

            if lecture.section_id not in by_section:
                by_section[lecture.section_id] = []

            by_section[lecture.section_id].append((lecture, timeslot, room, instructor))

        # Display each section
        for section_id in sorted(by_section.keys()):
            self.timetable_text.insert(tk.END, "=" * 80 + "\n")
            self.timetable_text.insert(tk.END, f" SECTION: {section_id}\n")
            self.timetable_text.insert(tk.END, "=" * 80 + "\n\n")

            lectures = by_section[section_id]

            # Sort by day and time
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

            # Print header
            self.timetable_text.insert(tk.END,
                                       f"{'Day':<12} {'Time':<18} {'Room':<8} {'Course':<12} {'Instructor':<30}\n")
            self.timetable_text.insert(tk.END, "-" * 80 + "\n")

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
                    time_str = f"{start_time}-{end_time}"
                else:
                    day = timeslot
                    time_str = ""

                # Get instructor info
                inst_info = self.loader.instructors[
                    self.loader.instructors['InstructorID'] == instructor
                    ]
                instructor_name = inst_info.iloc[0]['Name'] if not inst_info.empty else instructor

                self.timetable_text.insert(
                    tk.END,
                    f"{day:<12} {time_str:<18} {room:<8} {lecture.course_id:<12} {instructor_name:<30}\n"
                )

            self.timetable_text.insert(tk.END, "\n")

    def display_statistics(self):
        """Display statistics"""
        self.stats_text.delete(1.0, tk.END)

        if not self.solution or not self.solver:
            return

        stats = self.solver.get_solution_statistics()

        self.stats_text.insert(tk.END, "=" * 60 + "\n")
        self.stats_text.insert(tk.END, " TIMETABLE STATISTICS\n")
        self.stats_text.insert(tk.END, "=" * 60 + "\n\n")

        self.stats_text.insert(tk.END, f"📚 Total lectures scheduled: {stats['total_assigned']}\n")
        self.stats_text.insert(tk.END, f"⏰ Timeslots used: {len(stats['timeslot_usage'])}/20\n")
        self.stats_text.insert(tk.END, f"👨‍🏫 Instructors used: {len(stats['instructor_load'])}\n")
        self.stats_text.insert(tk.END, f"🏫 Rooms used: {len(stats['room_usage'])}\n\n")

        # Most used timeslots
        self.stats_text.insert(tk.END, "Most used timeslots:\n")
        self.stats_text.insert(tk.END, "-" * 40 + "\n")
        sorted_ts = sorted(stats['timeslot_usage'].items(),
                           key=lambda x: x[1], reverse=True)[:5]
        for ts, count in sorted_ts:
            self.stats_text.insert(tk.END, f"  {ts}: {count} lectures\n")

        # Instructor load
        self.stats_text.insert(tk.END, "\nInstructor load (top 10):\n")
        self.stats_text.insert(tk.END, "-" * 40 + "\n")
        sorted_inst = sorted(stats['instructor_load'].items(),
                             key=lambda x: x[1], reverse=True)[:10]
        for instructor, count in sorted_inst:
            inst_info = self.loader.instructors[
                self.loader.instructors['InstructorID'] == instructor
                ]
            name = inst_info.iloc[0]['Name'] if not inst_info.empty else instructor
            self.stats_text.insert(tk.END, f"  {name}: {count} lectures\n")

        self.stats_text.insert(tk.END, "\n" + "=" * 60 + "\n")

    def calculate_quality(self):
        """Calculate and display quality score"""
        if not self.solution or not self.lectures:
            return

        soft = SoftConstraints(self.loader)

        self.stats_text.insert(tk.END, "\n\n")
        self.stats_text.insert(tk.END, "=" * 60 + "\n")
        self.stats_text.insert(tk.END, " QUALITY ANALYSIS\n")
        self.stats_text.insert(tk.END, "=" * 60 + "\n\n")

        total_score = soft.calculate_quality_score(self.solution, self.lectures)

        gap_penalty = soft._calculate_gap_penalty(self.solution, self.lectures)
        balance_bonus = soft._calculate_balance_bonus(self.solution, self.lectures)
        time_penalty = soft._calculate_time_preference_penalty(self.solution)
        room_penalty = soft._calculate_room_distance_penalty(self.solution, self.lectures)

        self.stats_text.insert(tk.END, f"📊 Overall Quality Score: {total_score:.2f}/1000\n\n")
        self.stats_text.insert(tk.END, "Breakdown:\n")
        self.stats_text.insert(tk.END, f"  Base Score:              1000.00\n")
        self.stats_text.insert(tk.END, f"  - Gap Penalty:          -{gap_penalty:.2f}\n")
        self.stats_text.insert(tk.END, f"  + Balance Bonus:        +{balance_bonus:.2f}\n")
        self.stats_text.insert(tk.END, f"  - Time Preference:      -{time_penalty:.2f}\n")
        self.stats_text.insert(tk.END, f"  - Room Distance:        -{room_penalty:.2f}\n")
        self.stats_text.insert(tk.END, f"  {'=' * 40}\n")
        self.stats_text.insert(tk.END, f"  Final Score:            {total_score:.2f}\n\n")

        # Quality rating
        if total_score >= 900:
            rating = "⭐⭐⭐⭐⭐ Excellent"
            color = "green"
        elif total_score >= 800:
            rating = "⭐⭐⭐⭐ Good"
            color = "blue"
        elif total_score >= 700:
            rating = "⭐⭐⭐ Fair"
            color = "orange"
        elif total_score >= 600:
            rating = "⭐⭐ Acceptable"
            color = "orange"
        else:
            rating = "⭐ Needs Improvement"
            color = "red"

        self.stats_text.insert(tk.END, f"🏆 Rating: {rating}\n")
        self.stats_text.insert(tk.END, "=" * 60 + "\n")

        self.quality_score = total_score

    def export_timetable(self):
        """Export timetable to CSV"""
        if not self.solution:
            messagebox.showwarning("Warning", "No timetable to export!")
            return

        # Ask for filename
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="timetable.csv"
        )

        if not filename:
            return

        try:
            import pandas as pd

            rows = []

            for var_name, (timeslot, room, instructor) in self.solution.items():
                lecture = next((l for l in self.lectures if l.get_variable_name() == var_name), None)
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
                    'Instructor': instructor_name,
                    'Quality Score': self.quality_score if self.quality_score else 'N/A'
                })

            # Create DataFrame and sort
            df = pd.DataFrame(rows)
            df = df.sort_values(['Section', 'Day', 'Start Time'])

            # Save to CSV
            df.to_csv(filename, index=False)

            self.log(f"\n✅ Exported {len(rows)} lectures to {filename}")
            messagebox.showinfo("Success", f"Timetable exported to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{str(e)}")


def main():
    """Main entry point for GUI"""
    root = tk.Tk()
    app = TimetableGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()