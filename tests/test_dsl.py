import pytest
from datetime import date
from ganttdsl.dsl import CircularDependencyError, Task, Team, CriticalPathScheduler, Scheduler, Plan, ScheduledTask
from itertools import permutations


def test_task_creation():
    task = Task(
        name="Prototype Design",
        description="Design the prototype.",
        references=["https://example.com/design-doc"],
        point_of_contact="Engineer A",
        effort=10,
        parallelization_factor=2
    )
    assert task.name == "Prototype Design"
    assert task.effort == 10
    assert task.parallelization_factor == 2
    assert task.dependencies == set()


def test_task_with_dependencies():
    task_a = Task(
        name="Task A",
        description="First task.",
        references=[],
        point_of_contact="Engineer A",
        effort=5,
        parallelization_factor=1
    )
    task_b = Task(
        name="Task B",
        description="Second task, depends on Task A.",
        references=[],
        point_of_contact="Engineer B",
        effort=8,
        parallelization_factor=2,
        dependencies={task_a}
    )
    assert task_a in task_b.dependencies
    assert len(task_b.dependencies) == 1


def test_team_creation():
    team = Team(name="Engineering Team", size=3)
    assert team.name == "Engineering Team"
    assert team.size == 3


def test_scheduler_detects_circular_dependencies():
    task_a = Task(
        name="Task A",
        description="Task A.",
        references=[],
        point_of_contact="Engineer A",
        effort=5,
        parallelization_factor=1
    )
    task_b = Task(
        name="Task B",
        description="Task B, depends on Task A.",
        references=[],
        point_of_contact="Engineer B",
        effort=8,
        parallelization_factor=2,
        dependencies={task_a}
    )
    task_a.dependencies.add(task_b)  # Create a circular dependency

    scheduler = CriticalPathScheduler()
    with pytest.raises(CircularDependencyError):
        scheduler.schedule([task_a, task_b], Team(name="Team", size=3), date(2025, 1, 1))




def test_schedule_tasks():
    task_a = Task(
        name="A",
        description="Design the prototype.",
        references=[],
        point_of_contact="Engineer A",
        effort=3,
        parallelization_factor=2
    )
    task_b = Task(
        name="B",
        description="Build the prototype, depends on Task A.",
        references=[],
        point_of_contact="Engineer B",
        effort=2,
        parallelization_factor=1,
        dependencies={task_a}
    )
    team = Team(name="Engineering Team", size=3)
    scheduler = CriticalPathScheduler(cost_of_procastination=1)
    start_date = date(2025, 1, 1)

    plan = scheduler.schedule([task_a, task_b], team, start_date)
    assert isinstance(plan, Plan)
    assert len(plan.scheduled_tasks) == 2

    scheduled_task_a = plan.scheduled_tasks[0]
    assert scheduled_task_a.task == task_a
    assert scheduled_task_a.start_date == date(2025, 1, 1)
    assert scheduled_task_a.end_date == date(2025, 1, 2)
    assert scheduled_task_a.date_engineer_allocation == {
        date(2025, 1, 1): 2,
        date(2025, 1, 2): 1,
    }

    scheduled_task_b = plan.scheduled_tasks[1]
    assert scheduled_task_b.task == task_b
    assert scheduled_task_b.start_date == date(2025, 1, 3)
    #because 4 and 5 are weekends
    assert scheduled_task_b.end_date == date(2025, 1, 6)
    assert scheduled_task_b.date_engineer_allocation == {
        date(2025, 1, 3): 1,
        date(2025, 1, 6): 1,
    }


def test_markdown_view():
    task_a = Task(
        name="Prototype Design",
        description="Design the prototype.",
        references=["https://example.com/design-doc"],
        point_of_contact="Engineer A",
        effort=10,
        parallelization_factor=2
    )
    task_b = Task(
        name="Build Prototype",
        description="Build the prototype, depends on Task A.",
        references=["https://example.com/build-doc"],
        point_of_contact="Engineer B",
        effort=8,
        parallelization_factor=1,
        dependencies={task_a}
    )
    team = Team(name="Engineering Team", size=3)
    scheduler = CriticalPathScheduler()
    start_date = date(2025, 1, 1)

    plan = scheduler.schedule([task_a, task_b], team, start_date)
    markdown = plan.get_markdown_view()
    assert markdown =="""# Project Plan

## `Prototype Design`

Design the prototype.

**Effort**: 10 days

**Parallelization Factor**: 2

**Point of Contact**: Engineer A

**References**:

  - [https://example.com/design-doc](https://example.com/design-doc)


**Dependencies**:



### Schedule

| Date | Engineers |
|------|-----------|
| 2025-01-01 | 2 |
| 2025-01-02 | 2 |
| 2025-01-03 | 2 |
| 2025-01-06 | 2 |
| 2025-01-07 | 2 |
## `Build Prototype`

Build the prototype, depends on Task A.

**Effort**: 8 days

**Parallelization Factor**: 1

**Point of Contact**: Engineer B

**References**:

  - [https://example.com/build-doc](https://example.com/build-doc)


**Dependencies**:

  - `Prototype Design`


### Schedule

| Date | Engineers |
|------|-----------|
| 2025-01-08 | 1 |
| 2025-01-09 | 1 |
| 2025-01-10 | 1 |
| 2025-01-13 | 1 |
| 2025-01-14 | 1 |
| 2025-01-15 | 1 |
| 2025-01-16 | 1 |
| 2025-01-17 | 1 |
"""


def test_gantt_chart_view():
    task_a = Task(
        name="Prototype Design",
        description="Design the prototype.",
        references=["https://example.com/design-doc"],
        point_of_contact="Engineer A",
        effort=10,
        parallelization_factor=2
    )
    task_b = Task(
        name="Build Prototype",
        description="Build the prototype, depends on Task A.",
        references=["https://example.com/build-doc"],
        point_of_contact="Engineer B",
        effort=8,
        parallelization_factor=1,
        dependencies={task_a}
    )
    team = Team(name="Engineering Team", size=3)
    scheduler = CriticalPathScheduler()
    start_date = date(2025, 1, 1)

    plan = scheduler.schedule([task_a, task_b], team, start_date)
    gantt_chart = plan.get_gantt_chart()
    assert "@startgantt" in gantt_chart
    assert "Project starts 2025-01-01" in gantt_chart
    assert "[Build Prototype] ends 2025-01-17" in gantt_chart
    assert "[Build Prototype] starts 2025-01-08" in gantt_chart
    assert "@endgantt" in gantt_chart
