import streamlit as st
import pandas as pd
import os
import bcrypt

# File paths
USERS_FILE = "users.csv"
DATA_FILE_TEMPLATE = "{}_goals.csv"  # User-specific data files

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# User management functions
def load_users():
    return pd.read_csv(USERS_FILE) if os.path.exists(USERS_FILE) else pd.DataFrame(columns=["Username", "Password"])

def save_user(username, password):
    users_df = load_users()
    if username in users_df["Username"].values:
        return False
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user = pd.DataFrame([[username, hashed]], columns=["Username", "Password"])
    users_df = pd.concat([users_df, new_user], ignore_index=True)
    users_df.to_csv(USERS_FILE, index=False)
    return True

def verify_user(username, password):
    users_df = load_users()
    user_row = users_df[users_df["Username"] == username]
    if not user_row.empty:
        stored_hash = user_row["Password"].values[0]
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    return False

# Data management functions
def load_data(username):
    data_file = DATA_FILE_TEMPLATE.format(username)
    return pd.read_csv(data_file) if os.path.exists(data_file) else pd.DataFrame(columns=["Goal", "Target", "Saved"])

def save_data(username, df):
    data_file = DATA_FILE_TEMPLATE.format(username)
    df.to_csv(data_file, index=False)

# Authentication UI
def auth_interface():
    st.title("🔐 Login/Sign Up")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("Login"):
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if verify_user(login_user, login_pass):
                    st.session_state.logged_in = True
                    st.session_state.current_user = login_user
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("Sign Up"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            if st.form_submit_button("Create Account"):
                if save_user(new_user, new_pass):
                    st.success("Account created! Please login")
                else:
                    st.error("Username already exists")

# Main App
if not st.session_state.logged_in:
    auth_interface()
else:
    # Main application
    st.title(f"💰 {st.session_state.current_user}'s Savings Tracker")
    
    with st.sidebar:
        st.subheader(f"Welcome, {st.session_state.current_user}!")
        menu = st.radio("Navigate", ["Add Goal", "View Goals", "Edit Goal", "Delete Goal", "Update Savings"])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

    data = load_data(st.session_state.current_user)

    if menu == "Add Goal":
        st.subheader("➕ Add a New Goal")
        goal = st.text_input("Goal Name")
        target = st.number_input("Target Amount (PHP)", min_value=0.0)  # ₱ Changed
        saved = st.number_input("Already Saved (PHP)", min_value=0.0)   # ₱ Changed
        if st.button("Add Goal"):
            new_entry = pd.DataFrame([[goal, target, saved]], columns=["Goal", "Target", "Saved"])
            data = pd.concat([data, new_entry], ignore_index=True)
            save_data(st.session_state.current_user, data)
            st.success("Goal added!")

    elif menu == "View Goals":
        st.subheader("📋 All Savings Goals")
        if data.empty:
            st.info("No goals yet.")
        else:
            data["Progress (%)"] = (data["Saved"] / data["Target"] * 100).round(2)
            st.dataframe(data)
            st.metric("Total Goals", len(data))
            st.metric("Total Saved", f"₱{data['Saved'].sum():,.2f}")              # ₱ Changed
            st.metric("Remaining", f"₱{data['Target'].sum() - data['Saved'].sum():,.2f}")  # ₱ Changed

    elif menu == "Edit Goal":
        st.subheader("✏️ Edit a Goal")
        if data.empty:
            st.info("No goals to edit.")
        else:
            goal_list = data["Goal"].tolist()
            selected_goal = st.selectbox("Select a goal to edit", goal_list)
            goal_row = data[data["Goal"] == selected_goal].index[0]
            new_name = st.text_input("Goal Name", value=data.at[goal_row, "Goal"])
            new_target = st.number_input("Target Amount (PHP)", value=float(data.at[goal_row, "Target"]))  # ₱ Changed
            new_saved = st.number_input("Amount Saved (PHP)", value=float(data.at[goal_row, "Saved"]))     # ₱ Changed
            if st.button("Update Goal"):
                data.at[goal_row, "Goal"] = new_name
                data.at[goal_row, "Target"] = new_target
                data.at[goal_row, "Saved"] = new_saved
                save_data(st.session_state.current_user, data)
                st.success("Goal updated!")

    elif menu == "Delete Goal":
        st.subheader("🗑️ Delete a Goal")
        if data.empty:
            st.info("No goals to delete.")
        else:
            selected_goal = st.selectbox("Select goal to delete", data["Goal"].tolist())
            if st.button("Delete"):
                data = data[data["Goal"] != selected_goal]
                save_data(st.session_state.current_user, data)
                st.warning(f"Deleted goal: {selected_goal}")

    elif menu == "Update Savings":
        st.subheader("💸 Update Saved Amount")
        if data.empty:
            st.info("No goals available.")
        else:
            selected_goal = st.selectbox("Select goal", data["Goal"].tolist())
            goal_row = data[data["Goal"] == selected_goal].index[0]
            new_saved = st.number_input("New saved amount (PHP)", value=float(data.at[goal_row, "Saved"]))  # ₱ Changed
            if st.button("Update Savings"):
                data.at[goal_row, "Saved"] = new_saved
                save_data(st.session_state.current_user, data)
                st.success("Savings updated!")