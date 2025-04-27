import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="Family Tree Org Chart", page_icon="🌳", layout="wide")

# --- Load Family Tree Data ---
@st.cache_data
def load_data():
    df = pd.read_excel('Test_family_tree.xlsx')
    df['Spouse Ids'] = df['Spouse Ids'].fillna('').apply(lambda x: [int(i.strip()) for i in str(x).split(';') if i.strip().isdigit()])
    df['Children Ids'] = df['Children Ids'].fillna('').apply(lambda x: [int(i.strip()) for i in str(x).split(';') if i.strip().isdigit()])
    return df

family_df = load_data()
family_dict = {int(row['Unique ID']): row for _, row in family_df.iterrows()}

# --- Helper Functions ---
def get_person(uid):
    return family_dict.get(int(uid))

def get_hover_info(person):
    dob = person['DOB'].date() if pd.notna(person['DOB']) else 'Unknown'
    valavu = person['Valavu'] if pd.notna(person['Valavu']) else 'Unknown'
    alive = 'Alive' if isinstance(person['Is Alive?'], str) and person['Is Alive?'].strip().lower() == 'yes' else 'Deceased'
    return f"Name: {person['Name']}<br>DOB: {dob}<br>Valavu: {valavu}<br>Status: {alive}"

def build_html_tree(uid, level, max_level, visited):
    if level > max_level or uid in visited:
        return ""

    person = get_person(uid)
    if person is None:
        return ""

    visited.add(uid)
    hover_info = get_hover_info(person)

    html = f"<li><a title='{hover_info}' href='#'>{person['Name']}</a>"

    children = []
    for cid in person['Children Ids']:
        if cid in family_dict:
            children.append(cid)

    if children:
        html += "<ul>"
        for child_id in children:
            html += build_html_tree(child_id, level + 1, max_level, visited)
        html += "</ul>"

    html += "</li>"

    return html

# --- Main App UI ---
st.title("🌳 Family Tree Organizational Chart")

query_params = st.query_params
st.sidebar.markdown("### 🔍 Debug Logs")
st.sidebar.write("Received Query Parameters:", query_params)

person_id = 0
max_level = 2

if 'id' in query_params:
    try:
        id_list = query_params['id']
        if isinstance(id_list, list):
            person_id_str = ''.join(id_list)
        else:
            person_id_str = str(id_list)
        person_id = int(person_id_str)
    except Exception as e:
        st.sidebar.error(f"Error parsing person_id: {e}")

if 'level' in query_params:
    try:
        level_list = query_params['level']
        if isinstance(level_list, list):
            level_str = ''.join(level_list)
        else:
            level_str = str(level_list)
        max_level = int(level_str)
    except Exception as e:
        st.sidebar.error(f"Error parsing level: {e}")

st.sidebar.write(f"Parsed ID: {person_id}")
st.sidebar.write(f"Parsed Level: {max_level}")

if person_id == 0:
    st.info("No person selected. Please provide a person ID in the URL.")
else:
    root_person = get_person(person_id)
    if root_person is not None:
        st.sidebar.success(f"Found Person: {root_person['Name']}")
        st.header(f"Family Tree of {root_person['Name']}")

        if pd.notna(root_person['DOB']):
            st.markdown(f"**Date of Birth:** {root_person['DOB'].date()}")
        else:
            st.markdown(f"**Date of Birth:** Unknown")
        
        st.markdown(f"**Valavu:** {root_person['Valavu']}")
        
        alive_status = root_person['Is Alive?']
        status_text = '🟢 Alive' if isinstance(alive_status, str) and alive_status.strip().lower() == 'yes' else '🔴 Deceased'
        st.markdown(f"**Status:** {status_text}")

        user_level = st.slider('Select depth of family tree expansion', 1, 5, value=max_level)
        st.sidebar.info(f"Generating Tree with Depth Level: {user_level}")

        visited = set()

        # --- Build OrgChart Style HTML ---
        tree_html = """
        <style>
        .tree * {margin:0; padding:0;}
        .tree ul {
            padding-top: 20px; position: relative;
            display: flex;
            justify-content: center;
        }
        .tree li {
            list-style-type: none;
            text-align: center;
            position: relative;
            padding: 20px 5px 0 5px;
        }
        .tree li::before, .tree li::after {
            content: '';
            position: absolute; 
            top: 0; 
            border-top: 1px solid #ccc;
        }
        .tree li::before {
            left: 50%;
            border-left: 1px solid #ccc;
            height: 20px;
        }
        .tree li::after {
            right: 50%;
            border-right: 1px solid #ccc;
            height: 20px;
        }
        .tree li:only-child::before, .tree li:only-child::after {
            display: none;
        }
        .tree li a {
            display: inline-block;
            padding: 8px 15px;
            border: 1px solid #ccc;
            border-radius: 8px;
            background: #e6f7ff;
            text-decoration: none;
            color: #333;
            font-family: Arial, sans-serif;
        }
        .tree li a:hover {
            background: #cceeff;
            color: #000;
        }
        </style>

        <div class="tree">
            <ul>
        """

        tree_html += build_html_tree(person_id, 0, user_level, visited)
        tree_html += "</ul></div>"

        st.markdown(tree_html, unsafe_allow_html=True)

        st.success(f"Showing {user_level} generation levels for {root_person['Name']} 👨‍👩‍👦")
    else:
        st.sidebar.error(f"Person with ID {person_id} not found in dataset.")
        st.error("Person not found! Please check the ID.")
