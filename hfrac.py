import streamlit as st
import requests
import re

def is_orcid(query):
    # Regex to check if string looks like an ORCID (e.g., 0000-0002-1825-0097)
    orcid_pattern = r'^\d{4}-\d{4}-\d{4}-(\d{3}[\dX])$'
    return re.match(orcid_pattern, query.strip())

st.title("🔎 Smart h-frac Calculator")
st.write("Enter a **Researcher Name** OR an **ORCID iD**.")

# 1. Single Input Box for both Name or ORCID
user_query = st.text_input("Search Researcher", placeholder="e.g. 'Jorge Hirsch' or '0000-0001-7175-3497'")

selected_id = None

if user_query:
    # 2. Determine search strategy
    if is_orcid(user_query):
        # Direct lookup by ORCID
        url = f"https://api.openalex.org/authors/{user_query}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Confirm identity to user
            st.success(f"Found: **{data['display_name']}** ({data.get('last_known_institution', {}).get('display_name', 'No Affiliation')})")
            selected_id = data['id']
        else:
            st.error("ORCID not found in OpenAlex.")
            
    else:
        # Fuzzy search by Name
        url = f"https://api.openalex.org/authors?search={user_query}"
        response = requests.get(url)
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            st.error("No authors found.")
        else:
            # Create a "Select" dropdown for disambiguation
            author_options = {}
            for r in results[:5]: # Top 5 results
                
                # --- FIX STARTS HERE ---
                # safely get the first affiliation from the list
                affiliations = r.get('affiliations', [])
                if affiliations:
                    # Get the institution name from the first item in the list
                    institution = affiliations[0].get('institution', {}).get('display_name', 'No Affiliation')
                else:
                    institution = 'No Affiliation'
                # --- FIX ENDS HERE ---

                label = f"{r['display_name']} | {institution} | 📄 {r['works_count']} papers"
                author_options[label] = r['id']
            
            selected_label = st.selectbox("Is this the researcher you mean?", list(author_options.keys()))
            selected_id = author_options[selected_label]

# 3. Calculate h-frac (Only runs if we have a valid selected_id)
if selected_id and st.button("Calculate h-frac"):
    with st.spinner("Analyzing papers... (this may take a moment)"):
        # Fetch works (paging logic would go here for production)
        works_url = f"https://api.openalex.org/works?filter=author.id:{selected_id}&per-page=200&sort=cited_by_count:desc"
        works_res = requests.get(works_url)
        
        if works_res.status_code == 200:
            works = works_res.json().get('results', [])
            
            fractional_citations = []
            for work in works:
                citations = work['cited_by_count']
                author_count = len(work.get('authorships', []))
                
                # Avoid division by zero
                if author_count > 0:
                    fractional_citations.append(citations / author_count)
            
            fractional_citations.sort(reverse=True)
            
            h_frac = 0
            for i, val in enumerate(fractional_citations):
                if val >= (i + 1):
                    h_frac = i + 1
                else:
                    break
            
            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("h-frac Index", h_frac)
            col2.metric("Papers Analyzed", len(works))
            
            st.info(f"**Explanation:** An h-frac of {h_frac} means this author has {h_frac} papers where their *fractional contribution* (citations ÷ author count) is at least {h_frac}.")
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        color: grey;
        text-align: center;
        padding: 10px;
        border-top: 1px solid #eaeaea;
    }
    </style>
    <div class="footer">
        Based on the method from <a href='https://doi.org/10.1002/asi.20845' target="_blank">Egghe (2008)</a>.
        Inspect underlying <a href='https://github.com/derpostbote22/hfrac' target="_blank">code</a>. 
        By <a href='https://jacob-energy.me/' target="_blank">Jacob Thrän</a>
    </div>
    """,
    unsafe_allow_html=True
)



