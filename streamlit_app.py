# streamlit_app.py

import streamlit as st
import pandas as pd
import graphviz
from urllib.parse import parse_qs

st.set_page_config(page_title="Family Tree Viewer", page_icon="🌳", layout="wide")

# Load family tree data
@st.cache_data
def load_data():
    # Replace with your path or upload
    df = pd.read_excel('family_tree.xlsx')
    df['Spouse Ids'] = df['Spouse Ids'].fillna('').apply(lambda x: [int(i.strip()) for i in str(x).split(';') if i.strip().isdigit()])
    df['Children Ids'] = df['Children Ids'].fillna('').apply(lambda x: [int(i.strip()) for i in str(x).split(';') if i.strip().isdigit()])
    return df

family_df = load_data()
family_dict = {row['Unique ID']: row for _, row in family_df.iterrows()}

# Helper to get person details
def get_person(uid):
    return family_dict.get(uid)

# Draw family tree recursively
def draw_tree(dot, uid, level, max_level):
    person = get_person(uid)
    if not person or level > max_level:
        return
    label = person['Name']
    dot.node(str(uid), label)

    # Add father and mother
    for parent_type in ['Father ID', 'Mother ID']:
        pid = person[parent_type]
        if pd.notna(pid) and pid in family_dict:
            parent = family_dict[pid]
            dot.node(str(pid), parent['Name'])
            dot.edge(str(pid), str(uid), label=parent_type.replace(' ID', ''))

    # Add spouse(s)
    for sid in person['Spouse Ids']:
        if sid in family_dict:
            spouse = family_dict[sid]
            dot.node(str(sid), spouse['Name'])
            dot.edge(str(uid), str(sid), label="Spouse")

    # Add children
    for cid in person['Children Ids']:
        if cid in family_dict:
            child = family_dict[cid]
            dot.node(str(cid), child['Name'])
            dot.edge(str(uid), str(cid), label="Child")
            draw_tree(dot, cid, level+1, max_level)

# Main App
st.title("🌳 Family Tree Explorer")

# Get parameters from URL
query_params = st.experimental_get_query_params()
person_id = int(query_params.get('id', [0])[0])
max_level = int(query_params.get('level', [2])[0])

if person_id == 0:
    st.info("No person selected. Please provide an ID in the URL.")
else:
    root_person = get_person(person_id)
    if root_person:
        st.header(f"Family Tree of {root_person['Name']} (Level {max_level})")

        dot = graphviz.Digraph(comment=f"Family Tree of {root_person['Name']}")
        draw_tree(dot, person_id, 0, max_level)
        st.graphviz_chart(dot)
    else:
        st.error("Person not found.")
