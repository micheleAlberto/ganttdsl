from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, List, Set, Optional, Callable, Dict
import cpmpy as cp



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
    
    def optimistic_task_duration(self, max_available_engineers:int) -> int:
        return self.effort // min(max_available_engineers, self.parallelization_factor)


class Team:
    def __init__(self, name: str, size: int):
        if size <= 0:
            raise ValueError("Team size must be a positive integer")
        self.name = name
        self.size = size


class ScheduledTask:
    def __init__(self, task: Task) -> None:
        self.task = task
        self.daily_engineer_allocation : dict[int, int] = defaultdict(int)
        # daily_engineer_allocation[t] == n means that n engineers are allocated to the task on day t
    @property
    def start_date(self) -> int|None:
        return min(self.daily_engineer_allocation.keys()) if self.daily_engineer_allocation else None
    @property
    def end_date(self) -> int|None:
        return max(self.daily_engineer_allocation.keys()) if self.daily_engineer_allocation else None
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
    def __init__(self, workday_filter: Callable[[date], bool] = lambda d: d.weekday() < 5):
        self.workday_filter = workday_filter
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
        

class CircularDependencyError(ValueError):
    pass

    
@dataclass
class ChunkOfWork:
    day_of_work : Any
    task : ScheduledTask 
    

    
    
class CriticalPathScheduler(Scheduler):
    def __init__(self, 
            max_days:int=100,
            cost_of_context:float=0,
            workday_filter: Callable[[date], bool] = lambda d: d.weekday() < 5
        ):
        super().__init__(workday_filter)
        self.max_days: int = max_days
        self.cost_of_context: float = cost_of_context
    def schedule(self, tasks: List[Task], team: Team, start_date: date) -> Plan:
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
                ChunkOfWork(day_of_work=cp.intvar(lb=0,ub=self.max_days), task=scheduled_task)
                for _ in range(scheduled_task.task.effort)
            ]
            chunks_by_task[scheduled_task] = task_chunks
            all_chunks.extend(task_chunks)
        # Add constraints 1: Each task must be scheduled after its dependencies
        for dependency_task in planned_tasks:
            for dependent_task in dependents_of[dependency_task]:
                for dependency_chunk in chunks_by_task[dependency_task]:
                    for dependent_chunk in chunks_by_task[dependent_task]:
                        m += dependent_chunk.day_of_work >= dependency_chunk.day_of_work + 1
        # Add constraints 2: Each task must be scheduled before its dependents
        for dependent_task in planned_tasks:
            for dependency_task in dependencies_of[dependent_task]:
                for dependent_chunk in chunks_by_task[dependent_task]:
                    for dependency_chunk in chunks_by_task[dependency_task]:
                        m += dependent_chunk.day_of_work <= dependency_chunk.day_of_work - 1
        # Add constraints 3: the work being done on each task on a day by day basis is capped 
        # by the parallelization factor and the team size
        for scheduled_task, chunks in chunks_by_task.items():    
            max_parallel = min(scheduled_task.task.parallelization_factor, team.size)
            for day in range(self.max_days):
                m += cp.Count([chunk.day_of_work for chunk in chunks], day) <= max_parallel
                
        # compute the cost function as the last day of work of the last task
        cost_function = cp.Maximum([chunk.day_of_work for chunk in all_chunks]) 
        # bias the cost function by penalizing context switching and keeping many tasks active concurrently
        for scheduled_task, chunks in chunks_by_task.items():
            cost_function += self.cost_of_context * (
                cp.Maximum([chunk.day_of_work for chunk in chunks])
                -
                cp.Minimum([chunk.day_of_work for chunk in chunks])
                -
                scheduled_task.task.optimistic_task_duration(team.size)
            )
        m.minimize(cost_function)
        hassol = m.solve()
        if not hassol:
            raise ValueError("No solution found")
        for chunk in all_chunks:
            chunk.task.daily_engineer_allocation[chunk.day_of_work.value]+=1
        return Plan(planned_tasks)
    
    @classmethod
    def has_circular_dependencies(cls, tasks: List[Task]) -> bool:
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
