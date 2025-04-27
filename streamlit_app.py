import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="Family Tree Org Chart", page_icon="🌳", layout="wide")

# --- Load Excel ---
@st.cache_data
def load_data():
    return pd.read_excel("Test_family_tree.xlsx")

df = load_data()

# --- Mapping ---
id_to_name = dict(zip(df['Unique ID'], df['Name']))

# --- Sidebar ---
st.sidebar.title("Family Tree Organizational Chart")
target_id = st.sidebar.number_input("Enter Unique ID:", min_value=1, step=1)

if target_id not in id_to_name:
    st.warning("Please enter a valid ID from the tree!")
    st.stop()

# --- Build Tree ---

def get_person_info(person_id):
    if person_id not in id_to_name:
        return None
    return id_to_name.get(person_id, f"Unknown {person_id}")

def build_html_tree(person_id, level_up=2, level_down=2):
    """Recursive HTML Tree"""
    person = df[df["Unique ID"] == person_id]
    if person.empty:
        return ""
    person = person.iloc[0]

    html = f'<li><a href="#">{get_person_info(person_id)}</a>'

    # Children
    children_html = ""
    if level_down > 0:
        children_ids = str(person.get("Children Ids") or "").split(";")
        valid_children = []
        for child_id in children_ids:
            child_id = child_id.strip()
            if child_id:
                child_id = int(float(child_id))
                if child_id in id_to_name:
                    valid_children.append(child_id)

        if valid_children:
            children_html += "<ul>"
            for child_id in valid_children:
                children_html += build_html_tree(child_id, level_up=0, level_down=level_down-1)
            children_html += "</ul>"

    html += children_html
    html += "</li>"

    return html

# --- Construct Top Level ---
html_code = """
<style>
.tree ul {
    padding-top: 20px; 
    position: relative;
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

.tree li:only-child {
    padding-top: 0;
}

.tree li a {
    display: inline-block;
    padding: 8px 15px;
    border: 1px solid #ccc;
    border-radius: 8px;
    text-decoration: none;
    background-color: #e6f7ff;
    color: #333;
    font-family: Arial;
}
</style>

<div class="tree">
<ul>
"""

# Add Ancestors first
def build_ancestor_tree(person_id, level_up):
    if level_up == 0 or person_id not in id_to_name:
        return f"<li><a href='#'>{get_person_info(person_id)}</a></li>"

    person = df[df["Unique ID"] == person_id]
    if person.empty:
        return ""

    person = person.iloc[0]
    father_id = person.get("Father ID")
    mother_id = person.get("Mother ID")

    html = "<li>"
    html += f"<a href='#'>{get_person_info(person_id)}</a>"

    if not pd.isna(father_id) or not pd.isna(mother_id):
        html += "<ul>"
        if not pd.isna(father_id):
            html += build_ancestor_tree(int(father_id), level_up-1)
        if not pd.isna(mother_id):
            html += build_ancestor_tree(int(mother_id), level_up-1)
        html += "</ul>"

    html += "</li>"

    return html

# Build the complete tree
html_code += build_ancestor_tree(target_id, level_up=2)
html_code += "<ul>" + build_html_tree(target_id, level_up=0, level_down=2) + "</ul>"
html_code += "</ul></div>"

# --- Render HTML ---
st.markdown(html_code, unsafe_allow_html=True)
