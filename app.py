from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Priority, Recurrence, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant. Add tasks, then generate a prioritized daily plan.")

PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}
RECURRENCE_MAP = {
    "once": Recurrence.ONCE,
    "daily": Recurrence.DAILY,
    "weekly": Recurrence.WEEKLY,
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --- Owner + pet -----------------------------------------------------------

st.subheader("Owner & pet")
col_a, col_b, col_c = st.columns(3)
with col_a:
    owner_name = st.text_input("Owner name", value="Jordan")
with col_b:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_c:
    species = st.selectbox("Species", ["dog", "cat", "other"])

# --- Add tasks -------------------------------------------------------------

st.subheader("Tasks")
st.caption("Add a few care tasks. These feed into the scheduler below.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

with st.form("add_task", clear_on_submit=True):
    row1 = st.columns(3)
    with row1[0]:
        task_title = st.text_input("Task title", value="Morning walk")
    with row1[1]:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with row1[2]:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    row2 = st.columns(3)
    with row2[0]:
        recurrence = st.selectbox("Recurrence", ["daily", "once", "weekly"], index=0)
    with row2[1]:
        weekday = st.selectbox("Weekly day", WEEKDAYS, index=0,
                               help="Only used when recurrence is 'weekly'.")
    with row2[2]:
        use_pref = st.checkbox("Set preferred time")
        pref_time = st.time_input("Preferred time", value=time(8, 0)) if use_pref else None

    submitted = st.form_submit_button("Add task")
    if submitted:
        st.session_state.tasks.append(
            {
                "title": task_title,
                "duration_minutes": int(duration),
                "priority": priority,
                "recurrence": recurrence,
                "day_of_week": WEEKDAYS.index(weekday),
                "preferred_time": pref_time.strftime("%H:%M") if pref_time else None,
            }
        )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
    if st.button("Clear tasks"):
        st.session_state.tasks = []
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Generate schedule -----------------------------------------------------

st.subheader("Build schedule")
plan_cols = st.columns(3)
with plan_cols[0]:
    plan_day = st.date_input("Plan for", value=date.today())
with plan_cols[1]:
    day_start = st.time_input("Day starts at", value=time(8, 0))
with plan_cols[2]:
    available = st.number_input("Available minutes", min_value=15, max_value=1440, value=90, step=15)

if st.button("Generate schedule", type="primary"):
    if not st.session_state.tasks:
        st.warning("Add at least one task first.")
    else:
        owner = Owner(owner_name)
        pet = Pet(pet_name, species=species)
        for t in st.session_state.tasks:
            pref = t.get("preferred_time")
            owner.add_task(
                pet,
                Task(
                    title=t["title"],
                    duration_minutes=t["duration_minutes"],
                    priority=PRIORITY_MAP[t["priority"]],
                    recurrence=RECURRENCE_MAP[t["recurrence"]],
                    day_of_week=t.get("day_of_week"),
                    preferred_time=time.fromisoformat(pref) if pref else None,
                ),
            )

        scheduler = Scheduler(available_minutes=int(available), day_start=day_start)
        plan = scheduler.plan_for_owner(owner, plan_day)

        st.markdown(f"### Plan for {pet_name} — {plan_day:%A, %B %d}")
        if plan.items:
            st.table(
                [
                    {
                        "start": item.start.strftime("%H:%M"),
                        "end": item.end.strftime("%H:%M"),
                        "task": item.task.title,
                        "min": item.task.duration_minutes,
                        "priority": item.task.priority.name.lower(),
                    }
                    for item in plan.items
                ]
            )
            st.success(f"{plan.total_minutes} min scheduled across {len(plan.items)} task(s).")
        else:
            st.info("Nothing could be scheduled for this day.")

        if plan.skipped:
            st.warning(
                "Skipped (not enough time): "
                + ", ".join(f"{t.title} ({t.duration_minutes} min)" for t in plan.skipped)
            )

        with st.expander("Why this plan?"):
            st.code(scheduler.explain_plan(plan), language="text")
