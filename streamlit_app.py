import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

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

def build_family_tree(uid, level, max_level, visited):
    if level > max_level or uid in visited:
        return None

    person = get_person(uid)
    if person is None:
        return None

    visited.add(uid)

    node = {
        "id": str(uid),
        "label": person['Name'],
        "children": []
    }

    for cid in person['Children Ids']:
        if cid in family_dict:
            child_subtree = build_family_tree(cid, level+1, max_level, visited)
            if child_subtree:
                node['children'].append(child_subtree)

    return node

# --- Main App ---
st.title("🌳 Family Tree Organizational Chart (React Look)")

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
    st.info("No person selected. Please provide a person ID in the URL (e.g., `?id=22`).")
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
        tree_data = build_family_tree(person_id, 0, user_level, visited)

        chart_json = json.dumps(tree_data)

        # --- React Organizational Chart Embed ---
        components.html(f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Family Tree</title>
    <style>
      .node {{
        border: 1px solid #ccc;
        padding: 8px 15px;
        border-radius: 8px;
        background: #e6f7ff;
        display: inline-block;
        font-family: Arial, sans-serif;
        font-size: 14px;
      }}
      .node:hover {{
        background: #cceeff;
        color: #000;
      }}
      .tree-container {{
        width: 100%;
        overflow: auto;
      }}
    </style>
  </head>
  <body>
    <div id="tree" class="tree-container"></div>

    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/react-organizational-chart/dist/index.js"></script>

    <script>
      const {{ OrganizationalChart, TreeNode }} = window['react-organizational-chart'];

      function generateTree(node) {{
        if (!node) return null;
        return React.createElement(
          TreeNode,
          {{ label: React.createElement('div', {{ className: 'node' }}, node.label) }},
          ...(node.children || []).map(child => generateTree(child))
        );
      }}

      const root = React.createElement(
        OrganizationalChart,
        {{ label: React.createElement('div', {{ className: 'node' }}, "{root_person['Name']}") }},
        generateTree({chart_json})
      );

      ReactDOM.createRoot(document.getElementById('tree')).render(root);
    </script>
  </body>
</html>
""", height=800, width=1500)

        st.success(f"Showing {user_level} generation levels for {root_person['Name']} 👨‍👩‍👦")
    else:
        st.sidebar.error(f"Person with ID {person_id} not found in dataset.")
        st.error("Person not found! Please check the ID.")
