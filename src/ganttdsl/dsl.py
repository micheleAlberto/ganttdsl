from datetime import date, timedelta
from typing import List, Set, Optional, Callable, Dict


class Task:
    def __init__(self, name: str, description: str, references: List[str], point_of_contact: str,
                 effort: int, parallelization_factor: int, dependencies: Optional[Set["Task"]] = None):
        if not name:
            raise ValueError("Task name must not be empty")
        if parallelization_factor <= 0:
            raise ValueError("Parallelization factor must be a positive integer")
        self.name = name
        self.description = description
        self.references = references
        self.point_of_contact = point_of_contact
        self.effort = effort
        self.parallelization_factor = parallelization_factor
        self.dependencies = dependencies or set()
        self.validate()
    def __repr__(self):
        return (f"Task(name={self.name}, description={self.description}, "
                f"references={self.references}, point_of_contact={self.point_of_contact}, "
                f"effort={self.effort}, parallelization_factor={self.parallelization_factor}, "
                f"dependencies={[dep.name for dep in self.dependencies]})")
    def validate(self):
        if self.effort <= 0:
            raise ValueError("Effort must be a positive integer")
        if self.parallelization_factor <= 0:
            raise ValueError("Parallelization factor must be a positive integer")

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Task) and self.name == other.name
    
    def minimum_task_duration(self, max_available_engineers:int) -> int:
        return self.effort // min(max_available_engineers, self.parallelization_factor)


class Team:
    def __init__(self, name: str, size: int):
        if size <= 0:
            raise ValueError("Team size must be a positive integer")
        self.name = name
        self.size = size

class PlannedTask:
    def __init__(self, task: Task, start_day: int, end_day: int):
        self.task = task
        self.start_day = start_day
        self.end_day = end_day

    def __repr__(self):
        return f"PlannedTask(task={self.task.name}, start_day={self.start_day}, end_day={self.end_day})"


class ScheduledTask:
    def __init__(self, task: Task, start_date: date, end_date: date, daily_engineer_allocation: Dict[date, int]):
        self.task = task
        self.start_date = start_date
        self.end_date = end_date
        self.daily_engineer_allocation = daily_engineer_allocation

    def __repr__(self):
        return f"ScheduledTask(task={self.task.name}, start_date={self.start_date}, end_date={self.end_date})"


class Plan:
    def __init__(self, scheduled_tasks: List[ScheduledTask]):
        self.scheduled_tasks = scheduled_tasks

    def get_markdown_view(self) -> str:
        output = []
        for scheduled_task in self.scheduled_tasks:
            task = scheduled_task.task
            output.append(f"### {task.name}")
            output.append(f"**Description:** {task.description}")
            output.append(f"**References:** {' '.join(task.references)}")
            output.append(f"**Point of Contact:** {task.point_of_contact}")
            output.append(f"**Effort:** {task.effort} engineer-days")
            output.append(f"**Parallelization Factor:** {task.parallelization_factor}")
            output.append(f"**Dependencies:** {', '.join(dep.name for dep in task.dependencies)}")
            output.append(f"**Planned Start Date:** {scheduled_task.start_date}")
            output.append(f"**Planned End Date:** {scheduled_task.end_date}")
            output.append(f"**Daily Engineer Allocation:**")
            for day, engineers in scheduled_task.daily_engineer_allocation.items():
                output.append(f"  - {day}: {engineers} engineers")
            output.append("\n")
        return "\n".join(output)

    def get_gantt_chart(self) -> str:
        gantt = ["@startgantt"]
        for scheduled_task in self.scheduled_tasks:
            gantt.append(f"[{scheduled_task.task.name}] requires {scheduled_task.task.effort} days")
            gantt.append(f"[{scheduled_task.task.name}] starts {scheduled_task.start_date}")
        gantt.append("@endgantt")
        return "\n".join(gantt)


class Scheduler:
    def __init__(self):
        self.workday_filter: Callable[[date], bool] = lambda d: d.weekday() < 5  # Default: Monday-Friday

    def schedule(self, tasks: List[Task], team: Team, start_date: date) -> Plan:
        raise NotImplementedError("Subclasses must implement the scheduling algorithm")

    def calculate_absolute_dates(self, start_date: date, total_days_of_work:int) -> dict[int, date]:
        absolute_dates = {}
        current_date = start_date
        days_of_work = 0
        while days_of_work < total_days_of_work:
            if self.workday_filter(current_date):
                days_of_work += 1
            absolute_dates[days_of_work] = current_date
            current_date += timedelta(days=1)
        return absolute_dates
        


class CriticalPathScheduler(Scheduler):
    def schedule(self, tasks: List[Task], team: Team, start_date: date) -> Plan:
        # Initialize variables
        planned_tasks = []
        task_start_times = {}
        task_end_times = {}
        available_engineers = team.size
        current_day = 0

        # Create a dictionary to track the remaining effort for each task
        remaining_effort = {task: task.effort for task in tasks}

        # Create a dictionary to track the daily engineer allocation for each task
        daily_engineer_allocation = {task: {} for task in tasks}

        # Create a set to track completed tasks
        completed_tasks = set()

        while remaining_effort:
            # Allocate engineers to tasks each day
            for task in tasks:
                if task in completed_tasks:
                    continue

                # Check if all dependencies are completed
                if all(dep in completed_tasks for dep in task.dependencies):
                    # Allocate engineers to the task
                    engineers_allocated = min(task.parallelization_factor, available_engineers, remaining_effort[task])
                    if engineers_allocated > 0:
                        daily_engineer_allocation[task][start_date + timedelta(days=current_day)] = engineers_allocated
                        remaining_effort[task] -= engineers_allocated
                        available_engineers -= engineers_allocated

                        # If the task is completed, mark it as completed and reset available engineers
                        if remaining_effort[task] <= 0:
                            completed_tasks.add(task)
                            available_engineers = team.size

            # Move to the next day
            current_day += 1
            available_engineers = team.size

        # Create ScheduledTask objects
        for task in tasks:
            start_day = min(daily_engineer_allocation[task].keys())
            end_day = max(daily_engineer_allocation[task].keys())
            scheduled_task = ScheduledTask(
                task,
                start_day,
                end_day,
                daily_engineer_allocation[task]
            )
            planned_tasks.append(scheduled_task)

        return Plan(planned_tasks)

    

    @staticmethod
    def has_circular_dependencies(tasks: List[Task]) -> bool:
        visited = set()

        def dfs(task, ancestors):
            if task in ancestors:
                return True
            if task in visited:
                return False
            visited.add(task)
            ancestors.add(task)
            for dep in task.dependencies:
                if dfs(dep, ancestors):
                    return True
            ancestors.remove(task)
            return False

        for task in tasks:
            if dfs(task, set()):
                return True

        return False
