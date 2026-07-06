from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Priority, Recurrence, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant. Add pets and tasks, then generate a prioritized daily plan.")

PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}
RECURRENCE_MAP = {
    "once": Recurrence.ONCE,
    "daily": Recurrence.DAILY,
    "weekly": Recurrence.WEEKLY,
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --- Application memory ----------------------------------------------------
# Streamlit reruns this whole script on every interaction, so we keep ONE
# Owner object in st.session_state. It (and every Pet/Task added to it) then
# survives across reruns instead of being recreated empty each time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
owner: Owner = st.session_state.owner

# --- Owner -----------------------------------------------------------------

st.subheader("Owner")
new_name = st.text_input("Owner name", value=owner.name)
if new_name and new_name != owner.name:
    owner.name = new_name

if st.button("Reset everything"):
    st.session_state.owner = Owner(new_name or "Jordan")
    st.rerun()

# --- Add a pet -------------------------------------------------------------

st.subheader("Add a pet")
with st.form("add_pet", clear_on_submit=True):
    p_cols = st.columns(4)
    with p_cols[0]:
        pet_name = st.text_input("Name", value="")
    with p_cols[1]:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with p_cols[2]:
        breed = st.text_input("Breed", value="")
    with p_cols[3]:
        age = st.number_input("Age (yrs)", min_value=0, max_value=40, value=1)

    if st.form_submit_button("Add pet"):
        if pet_name.strip():
            owner.add_pet(Pet(pet_name.strip(), species=species, breed=breed, age_years=int(age)))
            st.success(f"Added {pet_name.strip()}.")
        else:
            st.warning("Give the pet a name first.")

if owner.pets:
    st.caption(f"{owner.name} has {len(owner.pets)} pet(s): "
               + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above to start scheduling.")

# --- Add a task (requires a pet) -------------------------------------------

if owner.pets:
    st.subheader("Add a task")
    pet_idx = st.selectbox(
        "For which pet?",
        range(len(owner.pets)),
        format_func=lambda i: owner.pets[i].name,
    )
    selected_pet = owner.pets[pet_idx]

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

        if st.form_submit_button("Add task"):
            if task_title.strip():
                owner.add_task(
                    selected_pet,
                    Task(
                        title=task_title.strip(),
                        duration_minutes=int(duration),
                        priority=PRIORITY_MAP[priority],
                        recurrence=RECURRENCE_MAP[recurrence],
                        day_of_week=WEEKDAYS.index(weekday),
                        preferred_time=pref_time,
                    ),
                )
                st.success(f"Added '{task_title.strip()}' for {selected_pet.name}.")
            else:
                st.warning("Give the task a title first.")

# --- Current tasks ---------------------------------------------------------

all_tasks = owner.all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "pet": pet.name,
                "task": t.title,
                "min": t.duration_minutes,
                "priority": t.priority.name.lower(),
                "recurrence": t.recurrence.value,
                "preferred": t.preferred_time.strftime("%H:%M") if t.preferred_time else "—",
                "done": "✓" if t.completed else "",
            }
            for pet in owner.pets
            for t in pet.tasks
        ]
    )

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
    if not all_tasks:
        st.warning("Add at least one pet and task first.")
    else:
        scheduler = Scheduler(available_minutes=int(available), day_start=day_start)
        plan = scheduler.plan_for_owner(owner, plan_day)

        st.markdown(f"### Plan for {owner.name}'s pets — {plan_day:%A, %B %d}")
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
