# --- import statements ---
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import yaml
import sqlite3

from streamlit_extras.grid import grid
from yaml.loader import SafeLoader


# --- sqlite3 db ---
def admin_insert_data(assigned_to, tasks, date):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    query = "insert into task (assigned_to, tasks, date, progress) values (?, ?, ?, ?);"
    data = (f"{assigned_to}", f"{tasks}", f"{date}", "Not Started")
    cursor.execute(query, data)
    conn.commit()
    cursor.close()


def admin_fetch_data():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    data_keys = ["S.No", "command", "Task", "Dead Line", "Progress", "Commit ID"]
    query = "select * from task"
    cursor.execute(query)
    rows = cursor.fetchall()

    data_list = [dict(zip(data_keys, row)) for row in rows]
    cursor.close()
    return data_list
def user_update_data(commit_id, progress, serial_number):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    query = "UPDATE task SET commit_id = ?, progress = ? WHERE tasks = ?"
    # query = "UPDATE task SET commit_id = ?, progress = ? WHERE serial_number = ?"
    cursor.execute(query, (commit_id, progress, serial_number))
    conn.commit()
    conn.close()
def user_fetch_data(username):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    data_keys = ["S.No", "command", "Task", "Dead Line", "Progress", "Commit ID"]

    # --- query ---
    assigned_query = "select * from task where assigned_to = ? and progress <> 'Completed'"
    task_query = "select tasks, serial_number from task where assigned_to = ? and progress <> 'Not Started'"
    completed = "select * from task where assigned_to = ? and progress = 'Completed'"

    # --- data fetch ---
    cursor.execute(assigned_query, (username,))
    assigned_data = cursor.fetchall()

    cursor.execute(task_query, (username,))
    task_data = cursor.fetchall()

    cursor.execute(completed, (username,))
    completed_data = cursor.fetchall()

    data_list = [dict(zip(data_keys, row)) for row in assigned_data]
    completed_data_list = [dict(zip(data_keys, row)) for row in completed_data]

    cursor.close()

    return data_list, task_data, completed_data_list

# --- page configuration ---
st.set_page_config(layout='wide')

# --- removing page whitespace in top ---
st.markdown("""
        <style>
               .block-container {
                    padding-top: 25px;
                }
        </style>
        """, unsafe_allow_html=True)

# --- file read ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# --- authentication init ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

if st.session_state["authentication_status"] is None:
    st.sidebar.title('Welcome to iamdev')

# --- login page ---
name, auth_status, username = authenticator.login('Login', 'sidebar')

# --- login validation ---
if st.session_state["authentication_status"]:
    st.sidebar.subheader(f'Welcome *{st.session_state["name"]}*')

    # --- admin page
    if username == "dharani":

        # --- Data fetching ---
        df = pd.DataFrame(admin_fetch_data())

        st.subheader('Add Task')
        my_grid = grid([4, 1, 1, 1], 1, [1, 1], vertical_align='bottom')
        task = my_grid.text_input("Task")
        date = my_grid.date_input("Select Date", format="DD.MM.YYYY")
        assign_to = my_grid.selectbox("Assign to", ['Dharani', 'Gowtham', 'Bharani'])
        if my_grid.button('Add', use_container_width=True):
            admin_insert_data(assign_to, task, date)

        # data_keys = ["S.No", "command", "Task", "Dead Line", "Progress", "Commit ID"]
        my_grid.data_editor(
            df,
            height=420,
            column_config={
                "S.No": st.column_config.NumberColumn("S.No", width="small"),
                "Task": st.column_config.TextColumn("Task", width='large'),
                "command": st.column_config.TextColumn("Assigned to", width='small'),
                "rating": st.column_config.NumberColumn(
                    "Your rating",
                    help="How much do you like this command (1-5)?",
                    min_value=1,
                    max_value=5,
                    step=1,
                    format="%d ⭐",
                    width='small',
                ),
                "Git commit": st.column_config.SelectboxColumn(
                    "Progress",
                    options=[
                        "Not Started",
                        "Started",
                        "Completed",
                        "Raise Ticket"
                    ],
                    width="small",
                    required=True,
                ),
                "Commit ID": st.column_config.TextColumn("Commit ID", width='small')
            },
            disabled=["command", "is_widget", "Task"],
            hide_index=True,
            use_container_width=True
        )
        #
        # my_grid.write("Hello 1")
        # my_grid.write("Hello 2")

    # --- user page
    else:
        # --- Data Fetching ---
        list_task, uncomplete_task, completed_task = user_fetch_data('Dharani')
        un_task = [item[0] for item in uncomplete_task]

        # --- Task Update ---
        st.subheader('Update Task')
        my_grid = grid([4, 1, 1, 1], 1, [1, 1], vertical_align='bottom')
        task_update = my_grid.selectbox("Next Task to be completed", un_task)
        # task = my_grid.text_input("Task")
        commit_id = my_grid.text_input("Commit ID")
        progress = my_grid.selectbox("Progress", ('Not Started', 'Started', 'Completed'))
        if my_grid.button('Update', use_container_width=True):
            user_update_data(commit_id, progress, task_update)

        # --- Assigned Works ---
        tab1, tab2 = st.tabs(['Assigned', 'Completed'])
        with tab1:
            st.subheader('Assigned works')
            df = pd.DataFrame(list_task)
            st.data_editor(
                df,
                height=420,
                column_config={
                    "S.No": st.column_config.NumberColumn("S.No", width="small"),
                    "Image": st.column_config.ImageColumn(
                        "Profile",
                        width="small"
                    ),
                    "Task": st.column_config.TextColumn("Task", width='large'),
                    "command": st.column_config.TextColumn("Assigned to", width='small'),
                    "rating": st.column_config.NumberColumn(
                        "Your rating",
                        help="How much do you like this command (1-5)?",
                        min_value=1,
                        max_value=5,
                        step=1,
                        format="%d ⭐",
                        width='small',
                    ),
                    "is_widget": "Widget ?",
                    "Git commit": st.column_config.SelectboxColumn(
                        "Progress",
                        options=[
                            "Not Started",
                            "Started",
                            "Completed",
                            "Raise Ticket"
                        ],
                        width="small",
                        required=True,
                    ),
                    "Commit ID": st.column_config.TextColumn("Commit ID", width='small')
                },
                hide_index=True,
                use_container_width=True,
            )
        with tab2:
            st.subheader('Completed works')
            df = pd.DataFrame(completed_task)
            st.data_editor(
                df,
                height=420,
                column_config={
                    "S.No": st.column_config.NumberColumn("S.No", width="small"),
                    "Image": st.column_config.ImageColumn(
                        "Profile",
                        width="small"
                    ),
                    "Task": st.column_config.TextColumn("Task", width='large'),
                    "command": st.column_config.TextColumn("Assigned to", width='small'),
                    "rating": st.column_config.NumberColumn(
                        "Your rating",
                        help="How much do you like this command (1-5)?",
                        min_value=1,
                        max_value=5,
                        step=1,
                        format="%d ⭐",
                        width='small',
                    ),
                    "is_widget": "Widget ?",
                    "Git commit": st.column_config.SelectboxColumn(
                        "Progress",
                        options=[
                            "Not Started",
                            "Started",
                            "Completed",
                            "Raise Ticket"
                        ],
                        width="small",
                        required=True,
                    ),
                    "Commit ID": st.column_config.TextColumn("Commit ID", width='small')
                },
                hide_index=True,
                use_container_width=True,
                key='Tab2'
            )

    authenticator.logout('Logout', 'sidebar', key='unique_key')
elif st.session_state["authentication_status"] is False:
    st.sidebar.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.sidebar.warning('Please enter username and password')
