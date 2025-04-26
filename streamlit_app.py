# streamlit_app.py

import streamlit as st
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config

# --- Page Config ---
st.set_page_config(page_title="Family Tree Explorer", page_icon="🌳", layout="wide")

# --- Load Family Tree Data ---
@st.cache_data
def load_data():
    df = pd.read_excel('Test_family_tree.xlsx')

    # Clean up spouse and children IDs
    df['Spouse Ids'] = df['Spouse Ids'].fillna('').apply(lambda x: [int(i.strip()) for i in str(x).split(';') if i.strip().isdigit()])
    df['Children Ids'] = df['Children Ids'].fillna('').apply(lambda x: [int(i.strip()) for i in str(x).split(';') if i.strip().isdigit()])
    return df

family_df = load_data()
family_dict = {int(row['Unique ID']): row for _, row in family_df.iterrows()}

# --- Helper Functions ---

def get_person(uid):
    return family_dict.get(int(uid))

def build_family_graph(uid, level, max_level, nodes, edges, visited):
    if level > max_level or uid in visited:
        return

    person = get_person(uid)
    if person is None:
        return

    visited.add(uid)

    label = person['Name']
    nodes.append(Node(id=str(uid), label=label, size=400, shape="box"))

    # Father
    father_id = person['Father ID']
    if pd.notna(father_id) and father_id in family_dict:
        father = family_dict[father_id]
        nodes.append(Node(id=str(father_id), label=father['Name'], size=300, shape="box", color="lightblue"))
        edges.append(Edge(source=str(father_id), target=str(uid), label="Father"))

    # Mother
    mother_id = person['Mother ID']
    if pd.notna(mother_id) and mother_id in family_dict:
        mother = family_dict[mother_id]
        nodes.append(Node(id=str(mother_id), label=mother['Name'], size=300, shape="box", color="pink"))
        edges.append(Edge(source=str(mother_id), target=str(uid), label="Mother"))

    # Spouse(s)
    for sid in person['Spouse Ids']:
        if sid in family_dict:
            spouse = family_dict[sid]
            nodes.append(Node(id=str(sid), label=spouse['Name'], size=300, shape="box", color="lightgreen"))
            edges.append(Edge(source=str(uid), target=str(sid), label="Spouse"))

    # Children
    for cid in person['Children Ids']:
        if cid in family_dict:
            child = family_dict[cid]
            nodes.append(Node(id=str(cid), label=child['Name'], size=300, shape="box"))
            edges.append(Edge(source=str(uid), target=str(cid), label="Child"))
            build_family_graph(cid, level+1, max_level, nodes, edges, visited)

# --- Main App UI ---

st.title("🌳 Family Tree Explorer")

# --- Get Parameters from URL ---
query_params = st.query_params

# Debug log: show raw query params
st.sidebar.markdown("### 🔍 Debug Logs")
st.sidebar.write("Received Query Parameters:", query_params)

# Initialize defaults
person_id = 0
max_level = 2

# Parse person_id correctly
if 'id' in query_params:
    try:
        id_list = query_params['id']
        if isinstance(id_list, list):
            person_id_str = ''.join(id_list)  # Join parts safely
        else:
            person_id_str = str(id_list)
        person_id = int(person_id_str)
    except Exception as e:
        st.sidebar.error(f"Error parsing person_id: {e}")

# Parse max_level correctly
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

# Final debug print
st.sidebar.write(f"Parsed ID: {person_id}")
st.sidebar.write(f"Parsed Level: {max_level}")

# --- Main Logic ---

if person_id == 0:
    st.info("No person selected. Please provide a person ID in the URL.")
else:
    root_person = get_person(person_id)
    if root_person is not None:
        st.sidebar.success(f"Found Person: {root_person['Name']}")
        st.header(f"Family Tree of {root_person['Name']}")

        # Display basic details
        if pd.notna(root_person['DOB']):
            st.markdown(f"**Date of Birth:** {root_person['DOB'].date()}")
        else:
            st.markdown(f"**Date of Birth:** Unknown")
        
        st.markdown(f"**Valavu:** {root_person['Valavu']}")
        
        alive_status = root_person['Is Alive?']
        status_text = '🟢 Alive' if isinstance(alive_status, str) and alive_status.strip().lower() == 'yes' else '🔴 Deceased'
        st.markdown(f"**Status:** {status_text}")

        # Let user pick tree depth
        user_level = st.slider('Select depth of family tree expansion', 1, 5, value=max_level)

        st.sidebar.info(f"Generating Tree with Depth Level: {user_level}")

        # Build Graph
        nodes = []
        edges = []
        visited = set()

        build_family_graph(person_id, 0, user_level, nodes, edges, visited)

        config = Config(width=1200,
                        height=700,
                        directed=True,
                        hierarchical=True,
                        physics=False,
                        nodeHighlightBehavior=True,
                        highlightColor="red")

        agraph(nodes=nodes, edges=edges, config=config)

        st.success(f"Showing {user_level} generation levels for {root_person['Name']} 👨‍👩‍👦")
    else:
        st.sidebar.error(f"Person with ID {person_id} not found in dataset.")
        st.error("Person not found! Please check the ID.")
