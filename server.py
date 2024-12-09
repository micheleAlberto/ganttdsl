from datetime import date
from ganttdsl.dsl import Task
from ganttdsl.streamlit import gant_planner



# Define tasks for the 3-tier project

# Web Client Tasks
task_design_web_client = Task(
    name="Design Web Client",
    description="Design the web client interface.",
    references=["https://example.com/web-client-design"],
    point_of_contact="Engineer A",
    effort=5,
    parallelization_factor=2,
    dependencies=set()
)

task_implement_web_client = Task(
    name="Implement Web Client",
    description="Implement the web client based on the design.",
    references=["https://example.com/web-client-implementation"],
    point_of_contact="Engineer B",
    effort=10,
    parallelization_factor=2,
    dependencies={task_design_web_client}
)

task_test_web_client = Task(
    name="Test Web Client",
    description="Test the web client implementation.",
    references=["https://example.com/web-client-testing"],
    point_of_contact="Engineer C",
    effort=5,
    parallelization_factor=1,
    dependencies={task_implement_web_client}
)

# Web Server Tasks
task_design_web_server = Task(
    name="Design Web Server",
    description="Design the web server architecture.",
    references=["https://example.com/web-server-design"],
    point_of_contact="Engineer D",
    effort=5,
    parallelization_factor=2,
    dependencies=set()
)

task_implement_web_server = Task(
    name="Implement Web Server",
    description="Implement the web server based on the design.",
    references=["https://example.com/web-server-implementation"],
    point_of_contact="Engineer E",
    effort=10,
    parallelization_factor=2,
    dependencies={task_design_web_server}
)

task_test_web_server = Task(
    name="Test Web Server",
    description="Test the web server implementation.",
    references=["https://example.com/web-server-testing"],
    point_of_contact="Engineer F",
    effort=5,
    parallelization_factor=1,
    dependencies={task_implement_web_server}
)

# Database Tasks
task_design_database = Task(
    name="Design Database",
    description="Design the database schema.",
    references=["https://example.com/database-design"],
    point_of_contact="Engineer G",
    effort=5,
    parallelization_factor=2,
    dependencies=set()
)

task_implement_database = Task(
    name="Implement Database",
    description="Implement the database based on the design.",
    references=["https://example.com/database-implementation"],
    point_of_contact="Engineer H",
    effort=10,
    parallelization_factor=2,
    dependencies={task_design_database}
)

task_test_database = Task(
    name="Test Database",
    description="Test the database implementation.",
    references=["https://example.com/database-testing"],
    point_of_contact="Engineer I",
    effort=5,
    parallelization_factor=1,
    dependencies={task_implement_database}
)

# Deployment Tasks
task_deploy_to_production = Task(
    name="Deploy to Production",
    description="Deploy the entire system to production.",
    references=["https://example.com/deployment"],
    point_of_contact="Engineer J",
    effort=5,
    parallelization_factor=2,
    dependencies={task_test_web_client, task_test_web_server, task_test_database}
)


start_date = date(2025, 1, 1)

# Schedule the tasks
tasks = [
    task_design_web_client, task_implement_web_client, task_test_web_client,
    task_design_web_server, task_implement_web_server, task_test_web_server,
    task_design_database, task_implement_database, task_test_database,
    task_deploy_to_production
]

gant_planner(tasks, start_date)