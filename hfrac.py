import streamlit as st
import requests
import pandas as pd

st.title("🛡️ OpenAlex h-frac Calculator")
st.write("This tool uses the **OpenAlex API** (no scraping required) to calculate the h-frac index.")

# 1. User inputs name to search
name_query = st.text_input("Enter Researcher Name", "Timnit Gebru")

if name_query:
    # 2. Search for the author
    url = f"https://api.openalex.org/authors?search={name_query}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            st.error("No authors found.")
        else:
            # 3. Let user select the correct author (Disambiguation)
            author_options = {f"{r['display_name']} ({r.get('last_known_institution', {}).get('display_name', 'No Affiliation')})": r['id'] for r in results[:5]}
            selected_label = st.selectbox("Select the correct author:", list(author_options.keys()))
            selected_id = author_options[selected_label]
            
            if st.button("Calculate h-frac"):
                with st.spinner("Fetching publication data..."):
                    # 4. Fetch all works for this author
                    # OpenAlex paginates, but for simplicity we fetch the first 200 (usually enough for h-index calc)
                    # For a production app, you would loop through pages.
                    works_url = f"https://api.openalex.org/works?filter=author.id:{selected_id}&per-page=200&sort=cited_by_count:desc"
                    works_res = requests.get(works_url)
                    
                    if works_res.status_code == 200:
                        works = works_res.json().get('results', [])
                        
                        # 5. Calculate h-frac
                        fractional_citations_list = []
                        
                        for work in works:
                            citations = work['cited_by_count']
                            # Count authors for this specific paper
                            author_count = len(work.get('authorships', []))
                            if author_count > 0:
                                frac_cit = citations / author_count
                                fractional_citations_list.append(frac_cit)
                        
                        # Sort descending
                        fractional_citations_list.sort(reverse=True)
                        
                        # Compute h-frac
                        h_frac = 0
                        for i, val in enumerate(fractional_citations_list):
                            if val >= (i + 1):
                                h_frac = i + 1
                            else:
                                break
                        
                        st.success(f"Calculated h-frac: **{h_frac}**")
                        st.metric("Analyzed Papers", len(works))
                    else:
                        st.error("Failed to fetch works.")