from collections import defaultdict, deque
from  dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, List, Set, Optional, Callable, Dict
import cpmpy as cp
import pandas as pd
class Task:
    """
    Represents a task in the project.

    Attributes:
        name (str): The name of the task.
        description (str): Ad markdown formatted description of the task.
        references (List[str]): Links to references related to the task.
        point_of_contact (str): The engineer responsible for the task.
        effort (int): The number ofo days one engineer would take to complete the task.
        parallelization_factor (int): The number of engineers that can work concurrently on the task.
        dependencies (Optional[Set["Task"]]): A set of tasks that this task depends on.
    """
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
        """
        Returns a string representation of the task.
        """
        return (f"Task(name={self.name}, description={self.description}, "
                f"references={self.references}, point_of_contact={self.point_of_contact}, "
                f"effort={self.effort}, parallelization_factor={self.parallelization_factor}, "
                f"dependencies={[dep.name for dep in self.dependencies]})")

    def validate(self):
        """
        Validates the task attributes.
        """
        if self.effort <= 0:
            raise ValueError("Effort must be a positive integer")
        if self.parallelization_factor <= 0:
            raise ValueError("Parallelization factor must be a positive integer")

    def __hash__(self):
        """
        Returns the hash of the task based on its name.
        """
        return hash(self.name)

    def __eq__(self, other):
        """
        Checks if two tasks are equal based on their names.

        Args:
            other (Task): The other task to compare with.

        Returns:
            bool: True if the tasks have the same name, False otherwise.
        """
        return isinstance(other, Task) and self.name == other.name
    
    def optimistic_task_duration(self, max_available_engineers: int) -> int:
        """
        Calculates the optimistic duration of the task based on the maximum available engineers.

        Args:
            max_available_engineers (int): The maximum number of engineers available.

        Returns:
            int: The optimistic duration of the task in days.
        """
        # The duration is calculated by dividing the effort by the minimum of the available engineers and the parallelization factor.
        return self.effort // min(max_available_engineers, self.parallelization_factor)


class Team:
    """
    Represents a team of engineers.

    Attributes:
        name (str): The name of the team.
        size (int): The number of engineers in the team.
    """
    def __init__(self, name: str, size: int):
        if size <= 0:
            raise ValueError("Team size must be a positive integer")
        self.name = name
        self.size = size


class ScheduledTask:
    """
    Represents a scheduled task with start and end dates, and the allocation of engineers on each day.

    Attributes:
        task (Task): The task being scheduled.
        start_date (date|None): The start date of the task as an integer
        end_date (date|None): The end date of the task as an integer
        daily_engineer_allocation (Dict[int, int]): A dictionary tracking engineer allocation per day.
    """
    def __init__(self, task: Task) -> None:
        self.task = task
        # daily_engineer_allocation[t] == n means that n engineers are allocated to the task on day t
        self.daily_engineer_allocation: Dict[int, int] = defaultdict(int)
        self._days_to_date: Optional[Dict[int, date]] = None

    @property
    def start_day(self) -> int|None:
        start_date = None
        for day, engineers in self.daily_engineer_allocation.items():
            if (engineers > 0) and ((start_date is None) or (day < start_date)):
                start_date = day
        return start_date
    @property
    def end_day(self) -> int|None:
        end_date = None
        for day, engineers in self.daily_engineer_allocation.items():
            if (engineers > 0) and ((end_date is None) or (day > end_date)):
                end_date = day
        return end_date
    @property
    def start_date(self) -> date|None:
        if self._days_to_date is None:
            return None
        start_day = self.start_day
        if start_day is None:
            return None
        return self._days_to_date[start_day]
    @property
    def end_date(self) -> date|None:
        if self._days_to_date is None:
            return None
        end_day = self.end_day
        if end_day is None:
            return None
        return self._days_to_date[end_day]
    @property
    def date_engineer_allocation(self) -> dict[date, int]:
        if self._days_to_date is None:
            return {}
        return {self._days_to_date[day]: engineers for day, engineers in self.daily_engineer_allocation.items()}
    def _set_days_to_date_conversion(self, days_to_date: dict[int, date]) -> None:
        self._days_to_date = days_to_date
    def __repr__(self):
        return f"ScheduledTask(task={self.task.name})"


class Plan:
    """Represents the plan for the project, containing all scheduled tasks.

    Attributes:
        scheduled_tasks (List[ScheduledTask]): A list of scheduled tasks.
    """
    def __init__(self, scheduled_tasks: List[ScheduledTask], start_date: date, workday_filter: Callable[[date], bool]) -> None:
        self.scheduled_tasks = scheduled_tasks
        self.start_date = start_date
        total_days = max(scheduled_task.end_day or 0 for scheduled_task in scheduled_tasks)
        days_to_date :dict[int,date]= {}
        current_date = start_date
        for day in range(total_days+1):
            days_to_date[day] = current_date
            current_date += timedelta(days=1)
            while not workday_filter(current_date):
                current_date += timedelta(days=1)
        self.days_to_date = days_to_date
        for scheduled_task in self.scheduled_tasks:
            scheduled_task._set_days_to_date_conversion(days_to_date)

    def get_dependency_graph(self) -> str:
        """
        Returns a dependency graph representation of the plan.

        Returns:
            str: The dependency graph view of the plan.
        """
        graph = "digraph G {\n"
        for scheduled_task in self.scheduled_tasks:
            task = scheduled_task.task
            graph += f'"{task.name}" [label="{task.name}"];\n'
            for dep in task.dependencies:
                graph += f'"{dep.name}" -> "{task.name}";\n'
        graph += "}\n"
        return graph
    def get_markdown_view(self) -> str:
        """
        Returns a markdown representation of the plan.

        Returns:
            str: The markdown view of the plan.
        """
        markdown = "# Project Plan\n\n"
        for scheduled_task in self.scheduled_tasks:
            task = scheduled_task.task
            markdown += f"## `{task.name}`\n\n"
            markdown += f"{task.description}\n\n"
            markdown += f"**Effort**: {task.effort} days\n\n"
            markdown += f"**Parallelization Factor**: {task.parallelization_factor}\n\n"
            markdown += f"**Point of Contact**: {task.point_of_contact}\n\n"
            markdown += "**References**:\n\n"
            for reference in task.references:
                markdown += f"  - [{reference}]({reference})\n"
            markdown += "\n\n"
            markdown += "**Dependencies**:\n\n"
            for dep in task.dependencies:
                markdown += f"  - `{dep.name}`\n"
            markdown += "\n\n"
            markdown += f"### Schedule\n\n"
            markdown += "| Date | Engineers |\n"
            markdown += "|------|-----------|\n"
            for date, engineers in scheduled_task.date_engineer_allocation.items():
                markdown += f"| {date.strftime('%Y-%m-%d')} | {engineers} |\n"
        return markdown

    def get_gantt_chart(self) -> str:
        """
        Returns a Gantt chart representation of the plan.

        Returns:
            str: The Gantt chart view of the plan.
        """
        gantt_chart = "@startgantt\n"
        gantt_chart += f"Project starts {self.start_date.strftime('%Y-%m-%d')}\n" # date like 2025-01-01
        for scheduled_task in self.scheduled_tasks:
            task = scheduled_task.task
            gantt_chart += f"[{task.name}] starts {scheduled_task.start_date}\n"
            gantt_chart += f"[{task.name}] ends {scheduled_task.end_date}\n"
        gantt_chart += "@endgantt\n"
        return gantt_chart
    def get_engineer_use_table(self) -> pd.DataFrame:
        """
        Returns a table of engineer use over time.

        Returns:
            pd.DataFrame: The table of engineer use over time.
            
        Columns:
            Date: The date of the allocation.
            Total : The total number of engineers allocated on that date.
            T-$task_name: The number of engineers allocated to task $task_name on that date.
        """
        days = sorted(self.days_to_date.values())
        df = pd.DataFrame(dict(Date=days))
        df["Total"] = [0] * len(days)
        for scheduled_task in self.scheduled_tasks:
            df[f"T-{scheduled_task.task.name}"] = [0] * len(days)
            for date, engineers in scheduled_task.date_engineer_allocation.items():
                index = days.index(date)
                df.at[index, f"T-{scheduled_task.task.name}"] += engineers
            df["Total"] += df[f"T-{scheduled_task.task.name}"]
        return df
    def get_task_table(self) -> pd.DataFrame:
        """
        Returns a table of tasks and their scheduled start and end dates.

        Returns:
            pd.DataFrame: The table of tasks and their scheduled start and end dates.
        """
        data = []
        for scheduled_task in self.scheduled_tasks:
            data.append({
                "Task": scheduled_task.task.name,
                "Start Date": scheduled_task.start_date,
                "End Date": scheduled_task.end_date,
                "Effort": scheduled_task.task.effort,
                "Parallelization Factor": scheduled_task.task.parallelization_factor,
                "Point of Contact": scheduled_task.task.point_of_contact,
                "Dependencies": ", ".join(dep.name for dep in scheduled_task.task.dependencies)
            })
        return pd.DataFrame(data)

class Scheduler:
    """
    Base class for scheduling tasks.
    """
    def __init__(self, workday_filter: Callable[[date], bool] = lambda d: d.weekday() < 5):
        self.workday_filter = workday_filter
    def schedule(self, tasks: List[Task], team: Team, start_date: date) -> Plan:
        raise NotImplementedError("Subclasses must implement the scheduling algorithm")
    @classmethod
    def has_circular_dependencies(cls, tasks: List[Task]) -> bool:
        """
        Checks for circular dependencies among tasks.

        Args:
            tasks (List[Task]): A list of tasks to check.

        Returns:
            bool: True if there are circular dependencies, False otherwise.
        """
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
        

class CircularDependencyError(ValueError):
    pass

    
@dataclass
class ChunkOfWork:
    day_of_work : Any
    task : ScheduledTask
    identifier: int
    def key(self)->str:
        return f"{self.task.task.name}:{self.identifier}"
    

    
    
class CriticalPathScheduler(Scheduler):
    """
    A scheduler that always schedules the tasks on the critical path first.

    The CriticalPathScheduler prioritizes tasks that are on the critical path, which is the longest path from the start to the end of the project. This ensures that any delay in these tasks will directly impact the project's completion time.

    The cost function has 3 components:
    - time : number of days to complete the project
    - context : number of days a task is in active state beyond the minimum required to complete that task
    - procastination : penalizes doing things later by applying quadratic costs to the days of work
    Costs:
    - **Time Complexity**: The scheduling process involves topological sorting and resource allocation, which can be computationally intensive for large projects with many tasks and dependencies.
    - **Resource Utilization**: The scheduler aims to maximize the utilization of available engineering resources, which may lead to higher resource allocation in critical tasks, potentially leaving fewer resources for non-critical tasks.

    Methods:
        schedule(tasks: List[Task], team: Team, start_date: date) -> Plan: Schedules the tasks based on dependencies and resource availability.
    """
    def __init__(self, 
            max_days:int=100,
            cost_of_time:int=100,
            cost_of_context:int=1,
            cost_of_procastination:int=1,
            workday_filter: Callable[[date], bool] = lambda d: d.weekday() < 5
        ):
        super().__init__(workday_filter)
        self.max_days: int = max_days
        self.cost_of_context: int = cost_of_context
        self.cost_of_time: int = cost_of_time
        self.cost_of_procastination:int = cost_of_procastination
        self.debug_mode = False
        
    def schedule(self, tasks: List[Task], team: Team, start_date: date) -> Plan:
        """
        Schedules the tasks based on dependencies and resource availability.

        Args:
            tasks (List[Task]): A list of tasks to schedule.
            team (Team): The team of engineers.
            start_date (date): The start date of the project.

        Returns:
            Plan: The plan containing the scheduled tasks.
        """
        if self.has_circular_dependencies(tasks):
            raise CircularDependencyError("Tasks have circular dependencies")
        planned_tasks = [ScheduledTask(task) for task in tasks]
        plan_of : dict[Task, ScheduledTask] = {scheduled_task.task: scheduled_task for scheduled_task in planned_tasks}
        
        dependents_of : dict[ScheduledTask, list[ScheduledTask]] = defaultdict(list)
        dependencies_of : dict[ScheduledTask, list[ScheduledTask]] = defaultdict(list)
        for dependent in planned_tasks:
            for dependency in dependent.task.dependencies:
                dependents_of[plan_of[dependency]].append(dependent)
                dependencies_of[dependent].append(plan_of[dependency])
        m = cp.Model()
        chunks_by_task: dict[ScheduledTask, list[ChunkOfWork]] = {}
        all_chunks : list[ChunkOfWork]= []
        for scheduled_task in planned_tasks:
            task_chunks = [
                ChunkOfWork(
                    day_of_work=cp.intvar(lb=0,ub=self.max_days),
                    task=scheduled_task,
                    identifier=identifier)
                for identifier in range(scheduled_task.task.effort)
            ]
            chunks_by_task[scheduled_task] = task_chunks
            all_chunks.extend(task_chunks)
            for chunk_a, chunk_b in zip(task_chunks[:-1], task_chunks[1:]):
                m += chunk_a.day_of_work <= chunk_b.day_of_work
                if self.debug_mode:
                    print(f"{chunk_a.key()}.day <= {chunk_b.key()}.day")
        # Add constraints 1: Each task must be scheduled after its dependencies
        for dependency_task in planned_tasks:
            for dependent_task in dependents_of[dependency_task]:
                for dependency_chunk in chunks_by_task[dependency_task]:
                    for dependent_chunk in chunks_by_task[dependent_task]:
                        m += dependent_chunk.day_of_work >= dependency_chunk.day_of_work + 1
                        if self.debug_mode:
                            print(f"{dependent_chunk.key()}.day >= {dependency_chunk.key()}.day + 1")
        # Add constraints 2: Each task must be scheduled before its dependents
        for dependent_task in planned_tasks:
            for dependency_task in dependencies_of[dependent_task]:
                for dependent_chunk in chunks_by_task[dependent_task]:
                    for dependency_chunk in chunks_by_task[dependency_task]:
                        m += dependent_chunk.day_of_work >= dependency_chunk.day_of_work - 1
                        if self.debug_mode:
                            print(f"{dependent_chunk.key()}.day >= {dependency_chunk.key()}.day - 1")
        # Add constraints 3: the work being done on each task on a day by day basis is capped 
        # by the parallelization factor and the team size
        for scheduled_task, chunks in chunks_by_task.items():    
            max_parallel = min(scheduled_task.task.parallelization_factor, team.size)
            for day in range(self.max_days):
                m += cp.Count([chunk.day_of_work for chunk in chunks], day) <= max_parallel
                if self.debug_mode:
                    print(f"Count({[chunk.key() for chunk in chunks]}, {day}) <= {max_parallel}")
        for day in range(self.max_days):
            m += cp.Count([chunk.day_of_work for chunk in all_chunks], day) <= team.size
            if self.debug_mode:
                print(
                    f"Count(*, {day}) <= {team.size}"
                )
        # compute the cost function as the last day of work of the last task
        cost_function = self.cost_of_time * cp.Maximum([chunk.day_of_work for chunk in all_chunks]) 
        # bias the cost function by penalizing context switching and keeping many tasks active concurrently
        for scheduled_task, chunks in chunks_by_task.items():
            cost_function += self.cost_of_context * (
                cp.Maximum([chunk.day_of_work for chunk in chunks])
                -
                cp.Minimum([chunk.day_of_work for chunk in chunks])
                -
                scheduled_task.task.optimistic_task_duration(team.size)
            )
        # bias the cost function by penalizing doing things later
        for chunk in all_chunks:
            cost_function += self.cost_of_procastination * chunk.day_of_work
        m.minimize(cost_function)
        hassol = m.solve()
        if not hassol:
            raise ValueError("No solution found")
        for chunk in all_chunks:
            chunk.task.daily_engineer_allocation[int(chunk.day_of_work.value())]+=1
        return Plan(planned_tasks, start_date, self.workday_filter)
    
    
