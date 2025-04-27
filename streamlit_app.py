import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- Page Config ---
st.set_page_config(page_title="Family Tree Explorer", page_icon="🌳", layout="wide")

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

def build_html_tree(uid, level, max_level, visited):
    if level > max_level or uid in visited:
        return ""

    person = get_person(uid)
    if person is None:
        return ""

    visited.add(uid)

    html = f"<li><span>{person['Name']}</span>"

    children_html = ""
    for cid in person['Children Ids']:
        children_html += build_html_tree(cid, level+1, max_level, visited)

    if children_html:
        html += f"<ul>{children_html}</ul>"

    html += "</li>"
    return html

# --- Main App ---
st.title("🌳 Family Tree Explorer (Pure HTML Tree)")

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
        st.sidebar.error(f"❌ Error parsing person_id: {e}")

if 'level' in query_params:
    try:
        level_list = query_params['level']
        if isinstance(level_list, list):
            level_str = ''.join(level_list)
        else:
            level_str = str(level_list)
        max_level = int(level_str)
    except Exception as e:
        st.sidebar.error(f"❌ Error parsing level: {e}")

st.sidebar.write(f"Parsed ID: {person_id}")
st.sidebar.write(f"Parsed Level: {max_level}")

if person_id == 0:
    st.info("No person selected. Please provide a person ID in the URL (e.g., `?id=22`).")
else:
    root_person = get_person(person_id)
    if root_person is not None:
        st.sidebar.success(f"🎯 Found Root Person: {root_person['Name']}")
        st.header(f"Family Tree of {root_person['Name']}")

        user_level = st.slider('Select depth of family tree expansion', 1, 5, value=max_level)
        st.sidebar.info(f"Generating Tree with Depth Level: {user_level}")

        visited = set()
        tree_html = build_html_tree(person_id, 0, user_level, visited)

        if not tree_html:
            st.error("❌ Could not generate tree structure.")
            st.stop()

        final_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
.tree ul {{
  padding-top: 20px;
  position: relative;
  transition: all 0.5s;
  display: table;
  margin: 0 auto;
}}

.tree li {{
  display: table-cell;
  text-align: center;
  position: relative;
  padding: 20px 5px 0 5px;
  vertical-align: top;
}}

.tree li::before, .tree li::after {{
  content: '';
  position: absolute;
  top: 0;
  border-top: 2px solid #ccc;
  width: 50%;
  height: 20px;
}}

.tree li::before {{
  left: 50%;
  border-left: 2px solid #ccc;
}}

.tree li::after {{
  right: 50%;
  border-right: 2px solid #ccc;
}}

.tree li:only-child::before, .tree li:only-child::after {{
  display: none;
}}

.tree li:only-child {{
  padding-top: 0;
}}

.tree li span {{
  border: 2px solid #4CAF50;
  padding: 5px 10px;
  border-radius: 8px;
  display: inline-block;
  background: #e6ffe6;
  font-family: Arial;
  font-size: 14px;
  color: #333;
  position: relative;
  top: 0;
}}

</style>
</head>
<body>
<div class="tree">
<ul>
{tree_html}
</ul>
</div>
</body>
</html>
"""

        components.html(final_html, height=800, scrolling=True)
        st.success(f"✅ Showing {user_level} generation levels for {root_person['Name']} 👨‍👩‍👦")
    else:
        st.sidebar.error(f"❌ Person with ID {person_id} not found in dataset.")
        st.error("Person not found! Please check the ID.")
