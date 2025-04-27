import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- Page Config ---
st.set_page_config(page_title="Family Tree OrgChart", page_icon="🌳", layout="wide")

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
    person = family_dict.get(int(uid))
    if person is not None:
        st.sidebar.write(f"✅ Found person: {person['Name']} (ID: {uid})")
    else:
        st.sidebar.write(f"❌ Person with ID {uid} not found.")
    return person

def build_orgchart_nodes(uid, level, max_level, visited):
    st.sidebar.write(f"🔵 Building OrgChart node for ID {uid}, Level {level}")
    if level > max_level:
        return []

    if uid in visited:
        return []

    person = get_person(uid)
    if person is None:
        return []

    visited.add(uid)

    nodes = [{
        "id": str(uid),
        "name": person['Name'],
        "title": f"Valavu: {person['Valavu']}" if pd.notna(person['Valavu']) else "Unknown Valavu",
        "pid": str(person['Father ID']) if pd.notna(person['Father ID']) else None
    }]

    for cid in person['Children Ids']:
        nodes += build_orgchart_nodes(cid, level+1, max_level, visited)

    return nodes

# --- Main App ---
st.title("🌳 Family Tree (OrgChart.js Style)")

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
        st.sidebar.write(f"🚀 Starting Tree Node Building for ID {person_id}")
        orgchart_nodes = build_orgchart_nodes(person_id, 0, user_level, visited)

        if not orgchart_nodes:
            st.error("❌ Could not generate tree nodes. No valid hierarchy.")
            st.stop()
        else:
            st.sidebar.success("✅ OrgChart Nodes Built Successfully.")

        nodes_json = json.dumps(orgchart_nodes)

        # --- OrgChart.js Embed (jsDelivr CDN) ---
        components.html(f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Family Tree</title>
    <script src="https://cdn.jsdelivr.net/npm/orgchart@2.1.9/dist/js/orgchart.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/orgchart@2.1.9/dist/css/orgchart.min.css" />
    <style>
      #tree {{
        width: 100%;
        height: 100%;
        overflow: auto;
      }}
      .orgchart {{
        background: white;
      }}
    </style>
  </head>
  <body>
    <div id="tree"></div>

    <script>
      document.addEventListener('DOMContentLoaded', function () {{
        const nodes = {nodes_json};
        console.log("📦 OrgChart Nodes:", nodes);

        const orgchart = new OrgChart(document.getElementById('tree'), {{
          nodes: nodes,
          nodeBinding: {{
            field_0: "name",
            field_1: "title"
          }},
          enableZoom: true,
          enablePan: true,
          scaleInitial: OrgChart.match.boundary
        }});

        console.log("✅ OrgChart Rendered Successfully!");
      }});
    </script>
  </body>
</html>
""", height=800, width=1500)

        st.success(f"✅ Showing {user_level} generation levels for {root_person['Name']} 👨‍👩‍👦")
    else:
        st.sidebar.error(f"❌ Person with ID {person_id} not found in dataset.")
        st.error("Person not found! Please check the ID.")
