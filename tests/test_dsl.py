import pytest
from datetime import date
from ganttdsl.dsl import Task, Team, CriticalPathScheduler, Scheduler, Plan, ScheduledTask
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
    with pytest.raises(ValueError, match="Circular dependencies detected in tasks"):
        scheduler.schedule([task_a, task_b], Team(name="Team", size=3), date(2025, 1, 1))


def test_scheduler_topological_sort():
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
    task_c = Task(
        name="Task C",
        description="Independent task.",
        references=[],
        point_of_contact="Engineer C",
        effort=3,
        parallelization_factor=1
    )

    scheduler = CriticalPathScheduler()
    # Test that Task A comes before Task B in the sorted list
    # by trying all permutations of the tasks
    tasks = [task_a, task_b, task_c]
    for perm in permutations(tasks):
        sorted_tasks = scheduler.topological_sort(list(perm))
        assert sorted_tasks.index(task_a) < sorted_tasks.index(task_b)


def test_schedule_tasks():
    task_a = Task(
        name="Prototype Design",
        description="Design the prototype.",
        references=[],
        point_of_contact="Engineer A",
        effort=10,
        parallelization_factor=2
    )
    task_b = Task(
        name="Build Prototype",
        description="Build the prototype, depends on Task A.",
        references=[],
        point_of_contact="Engineer B",
        effort=8,
        parallelization_factor=1,
        dependencies={task_a}
    )
    team = Team(name="Engineering Team", size=3)
    scheduler = CriticalPathScheduler()
    start_date = date(2025, 1, 1)

    plan = scheduler.schedule([task_a, task_b], team, start_date)
    assert isinstance(plan, Plan)
    assert len(plan.scheduled_tasks) == 2

    scheduled_task_a = plan.scheduled_tasks[0]
    assert scheduled_task_a.task == task_a
    assert scheduled_task_a.start_date == date(2025, 1, 1)
    assert scheduled_task_a.end_date == date(2025, 1, 7)
    assert scheduled_task_a.daily_engineer_allocation == {
        date(2025, 1, 1): 2,
        date(2025, 1, 2): 2,
        date(2025, 1, 3): 2,
        date(2025, 1, 4): 2,
        date(2025, 1, 5): 2
    }

    scheduled_task_b = plan.scheduled_tasks[1]
    assert scheduled_task_b.task == task_b
    assert scheduled_task_b.start_date == date(2025, 1, 8)
    assert scheduled_task_b.end_date == date(2025, 1, 15)
    assert scheduled_task_b.daily_engineer_allocation == {
        date(2025, 1, 8): 1,
        date(2025, 1, 9): 1,
        date(2025, 1, 10): 1,
        date(2025, 1, 11): 1,
        date(2025, 1, 12): 1,
        date(2025, 1, 13): 1,
        date(2025, 1, 14): 1,
        date(2025, 1, 15): 1
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
    assert "### Prototype Design" in markdown
    assert "**Effort:** 10 engineer-days" in markdown
    assert "**Dependencies:** " in markdown  # Task A has no dependencies
    assert "### Build Prototype" in markdown
    assert "**Dependencies:** Prototype Design" in markdown


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
    assert "[Prototype Design] requires 10 days" in gantt_chart
    assert "[Build Prototype] starts 2025-01-08" in gantt_chart
    assert "@endgantt" in gantt_chart
