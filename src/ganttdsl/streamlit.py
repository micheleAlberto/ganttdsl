import streamlit as st

from datetime import date
import io
from ganttdsl.dsl import Plan, Task, Team, CriticalPathScheduler
import altair as alt

def gant_planner(tasks:list[Task], start_date:date):
    st.title("Gantt Chart Scheduler")
    st.write("This is a simple Gantt chart scheduler that uses the critical path method to schedule tasks.")
    number_of_engineers = st.number_input("Number of Engineers", min_value=1, max_value=15, value=5)
    with st.expander("Solver options"):
        cost_of_time:int= st.number_input("Cost of Time", min_value=1, max_value=1000, value=100)
        cost_of_context:int= st.number_input("Cost of Context Switching", min_value=-100, max_value=100, value=1)
        cost_of_procastination:int= st.number_input("Cost of Procastination", min_value=-100, max_value=100, value=1)
        max_days = st.number_input("Max Days", min_value=1, max_value=100, value=30)
    scheduler = CriticalPathScheduler(
        max_days = max_days,
        cost_of_time=cost_of_time,
        cost_of_context=cost_of_context,
        cost_of_procastination=cost_of_procastination
    )
    with st.spinner("Scheduling Tasks"):
        plan = scheduler.schedule(tasks, Team(name="Engineering Team", size=number_of_engineers), start_date)
    tab_plan, tab_engineer_use, tab_tasks = st.tabs(["Plan", "Engineer Use", "Tasks"])
    with tab_plan:
        c = alt.Chart(plan.get_task_table().sort_values(by="Start Date")).mark_bar().encode(
            x="Start Date",
            x2='End Date',
            y='Task'
        )
        st.altair_chart(c, use_container_width=True)
        st.code(plan.get_gantt_chart())
    with tab_engineer_use:
        engineer_use_df = plan.get_engineer_use_table()
        st.write(engineer_use_df)
        # stacked plot of engineer use
        engineer_use_df.drop(columns="Total", inplace=True)
        c = alt.Chart(engineer_use_df.melt(id_vars="Date")).mark_area(interpolate="step", point=True).encode(
            x="Date",
            y="value",
            color="variable"
        )
        st.altair_chart(c, use_container_width=True)
    with tab_tasks:
        st.graphviz_chart(plan.get_dependency_graph())
        st.write(plan.get_task_table())
        st.markdown(plan.get_markdown_view())
    
