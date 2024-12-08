from datetime import date, timedelta
from typing import List, Set, Optional, Callable


class Task:
    def __init__(self, name: str, description: str, references: List[str], point_of_contact: str,
                 effort: int, parallelization_factor: int, dependencies: Optional[Set["Task"]] = None):
        if not name:
            raise ValueError("Task name must not be empty")
        self.name = name
        self.description = description
        self.references = references
        self.point_of_contact = point_of_contact
        self.effort = effort
        self.parallelization_factor = parallelization_factor
        self.dependencies = dependencies or set()
        self.validate()

    def validate(self):
        if self.effort <= 0:
            raise ValueError("Effort must be a positive integer")
        if self.parallelization_factor <= 0:
            raise ValueError("Parallelization factor must be a positive integer")

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Task) and self.name == other.name


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
    def __init__(self, task: Task, start_date: date, end_date: date):
        self.task = task
        self.start_date = start_date
        self.end_date = end_date

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

    def calculate_absolute_dates(self, start_date: date, planned_task: PlannedTask) -> ScheduledTask:
        current_date = start_date
        workdays_passed = 0

        # Calculate start_date
        while workdays_passed < planned_task.start_day:
            current_date += timedelta(days=1)
            if self.workday_filter(current_date):
                workdays_passed += 1
        start_date_absolute = current_date

        # Calculate end_date
        while workdays_passed < planned_task.end_day:
            current_date += timedelta(days=1)
            if self.workday_filter(current_date):
                workdays_passed += 1
        end_date_absolute = current_date

        return ScheduledTask(
            task=planned_task.task,
            start_date=start_date_absolute,
            end_date=end_date_absolute
        )


class CriticalPathScheduler(Scheduler):
    def schedule(self, tasks: List[Task], team: Team, start_date: date) -> Plan:
        # Detect circular dependencies
        if self.has_circular_dependencies(tasks):
            raise ValueError("Circular dependencies detected in tasks")

        # Topologically sort tasks
        sorted_tasks = self.topological_sort(tasks)

        planned_tasks = []
        task_start_times = {}
        task_end_times = {}
        available_engineers = team.size

        for task in sorted_tasks:
            # Calculate start time based on dependencies
            start_day = max(task_end_times.get(dep, 0) for dep in task.dependencies)
            required_days = -(-task.effort // min(task.parallelization_factor, available_engineers))  # Ceiling division
            end_day = start_day + required_days

            # Schedule task
            planned_task = PlannedTask(task, start_day, end_day)
            planned_tasks.append(planned_task)

            # Record start and end times
            task_start_times[task] = start_day
            task_end_times[task] = end_day

        # Convert planned tasks to scheduled tasks with absolute dates
        scheduled_tasks = [
            self.calculate_absolute_dates(start_date, pt) for pt in planned_tasks
        ]
        return Plan(scheduled_tasks)

    def topological_sort(self, tasks: List[Task]) -> List[Task]:
        visited = set()
        stack = []
        temporary = set()

        def visit(task: Task):
            if task in temporary:
                raise ValueError(f"Circular dependency detected with task {task.name}")
            if task not in visited:
                temporary.add(task)
                for dep in task.dependencies:
                    visit(dep)
                temporary.remove(task)
                visited.add(task)
                stack.append(task)

        for task in tasks:
            visit(task)

        return stack[::-1]  # Reverse for correct order

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
