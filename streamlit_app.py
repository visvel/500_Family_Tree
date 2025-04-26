# streamlit_app.py

import streamlit as st
import pandas as pd
import graphviz

# --- Page Config ---
st.set_page_config(page_title="Family Tree Explorer", page_icon="🌳", layout="wide")

# --- Load Family Tree Data ---
@st.cache_data
def load_data():
    # Replace 'family_tree.xlsx' with your actual file name
    df = pd.read_excel('family_tree.xlsx')

    # Clean up spouse and children IDs
    df['Spouse Ids'] = df['Spouse Ids'].fillna('').apply(lambda x: [int(i.strip()) for i in str(x).split(';') if i.strip().isdigit()])
    df['Children Ids'] = df['Children Ids'].fillna('').apply(lambda x: [int(i.strip()) for i in str(x).split(';') if i.strip().isdigit()])
    return df

family_df = load_data()
family_dict = {row['Unique ID']: row for _, row in family_df.iterrows()}

# --- Helper Functions ---

def get_person(uid):
    return family_dict.get(uid)

def draw_tree(dot, uid, level, max_level):
    person = get_person(uid)
    if not person or level > max_level:
        return

    label = person['Name']
    dot.node(str(uid), label)

    # Parents
    for parent_type in ['Father ID', 'Mother ID']:
        pid = person[parent_type]
        if pd.notna(pid) and pid in family_dict:
            parent = family_dict[pid]
            dot.node(str(pid), parent['Name'])
            dot.edge(str(pid), str(uid), label=parent_type.replace(' ID', ''))

    # Spouse(s)
    for sid in person['Spouse Ids']:
        if sid in family_dict:
            spouse = family_dict[sid]
            dot.node(str(sid), spouse['Name'])
            dot.edge(str(uid), str(sid), label="Spouse")

    # Children
    for cid in person['Children Ids']:
        if cid in family_dict:
            child = family_dict[cid]
            dot.node(str(cid), child['Name'])
            dot.edge(str(uid), str(cid), label="Child")
            draw_tree(dot, cid, level+1, max_level)

# --- Main App UI ---

st.title("🌳 Family Tree Explorer")

query_params = st.query_params
person_id = int(query_params.get('id', [0])[0])
max_level = int(query_params.get('level', [2])[0])

if person_id == 0:
    st.info("No person selected. Please provide a person ID in the URL.")
else:
    root_person = get_person(person_id)
    if root_person:
        # Show person mini-info
        st.header(f"Family Tree of {root_person['Name']}")
        st.markdown(f"**Date of Birth:** {root_person['DOB'].date() if pd.notna(root_person['DOB']) else 'Unknown'}")
        st.markdown(f"**Valavu:** {root_person['Valavu']}")
        alive_status = root_person['Is Alive?']
        st.markdown(f"**Status:** {'🟢 Alive' if alive_status.lower() == 'yes' else '🔴 Deceased'}")

        # Let user pick the tree depth
        user_level = st.slider('Select depth of family tree expansion', 1, 5, value=max_level)

        # Draw tree
        dot = graphviz.Digraph(comment=f"Family Tree of {root_person['Name']}")
        draw_tree(dot, person_id, 0, user_level)
        st.graphviz_chart(dot)

        st.success(f"Showing {user_level} generation levels for {root_person['Name']} 👨‍👩‍👦")
    else:
        st.error("Person not found! Please check the ID.")
