"""
LanceDB Navigator - A Streamlit app for exploring and searching LanceDB tables
streamlit run backend/scripts/sandbox.py
"""
import streamlit as st
import lancedb
import pandas as pd
from test_lancedb import vector_search, fts_search

st.set_page_config(layout="wide", page_title="LanceDB Navigator")
st.title("📂 LanceDB Navigator")

# Path to your DB
DB_PATH = "backend/data/arxiv_lancedb"


def get_filterable_columns(df):
    """Extract columns that are good candidates for filtering"""
    filterable = {}
    for col in df.columns:
        if col == 'vector':
            continue
        
        dtype = df[col].dtype
        
        # Categorical/string columns
        if dtype == 'object' or dtype.name == 'category':
            unique_count = df[col].nunique()
            if unique_count < 50:  # Only if reasonable number of unique values
                filterable[col] = {
                    'type': 'categorical',
                    'values': sorted(df[col].dropna().unique().tolist())
                }
        
        # Numeric columns
        elif dtype in ['int64', 'float64', 'int32', 'float32']:
            filterable[col] = {
                'type': 'numeric',
                'min': float(df[col].min()),
                'max': float(df[col].max())
            }
        
        # Date columns
        elif dtype == 'datetime64[ns]':
            filterable[col] = {
                'type': 'date',
                'min': df[col].min(),
                'max': df[col].max()
            }
    
    return filterable


def apply_filters(df, filters):
    """Apply active filters to a dataframe"""
    if not filters:
        return df
    
    filtered_df = df.copy()
    
    for col_name, filter_info in filters.items():
        if col_name not in filtered_df.columns:
            continue
        
        if filter_info['type'] == 'categorical':
            filtered_df = filtered_df[filtered_df[col_name].isin(filter_info['values'])]
        
        elif filter_info['type'] == 'numeric':
            filtered_df = filtered_df[
                (filtered_df[col_name] >= filter_info['min']) & 
                (filtered_df[col_name] <= filter_info['max'])
            ]
        
        elif filter_info['type'] == 'date':
            filtered_df = filtered_df[
                (filtered_df[col_name] >= pd.to_datetime(filter_info['min'])) & 
                (filtered_df[col_name] <= pd.to_datetime(filter_info['max']))
            ]
    
    return filtered_df


try:
    db = lancedb.connect(DB_PATH)
    tables = db.table_names()
    
    # === SIDEBAR ===
    st.sidebar.header("Navigation")
    
    # Mode selector
    mode = st.sidebar.radio(
        "Select Mode",
        ["🔍 Search", "📋 Browse"],
        index=0
    )
    
    st.sidebar.divider()
    
    # Table selector
    selected_table = st.sidebar.selectbox("Select a Table", tables)
    
    if selected_table:
        tbl = db.open_table(selected_table)
        
        # Statistics
        total_rows = tbl.count_rows()
        st.sidebar.metric("Total Rows", total_rows)
        
        # Get a sample to detect vector dimension
        sample_df = tbl.head(1).to_pandas()
        if 'vector' in sample_df.columns:
            vector_dim = len(sample_df['vector'][0])
            st.sidebar.success(f"✅ Vector dim: {vector_dim}")
        
        # === SEARCH MODE ===
        if mode == "🔍 Search":
            st.header("🔍 Search")
            
            # Search input
            search_query = st.text_input(
                "Enter your search query", 
                placeholder="e.g., machine learning transformers"
            )
            
            # Search controls
            col1, col2 = st.columns([1, 1])
            
            with col1:
                search_mode = st.selectbox(
                    "Search Mode",
                    ["Vector Search", "Full-Text Search", "Both"]
                )
            
            with col2:
                result_limit = st.slider("Result Limit", min_value=1, max_value=10, value=5)
            
            # Additional controls
            col3, col4 = st.columns([1, 1])
            
            with col3:
                similarity_threshold = st.slider(
                    "Max Distance (Vector)", 
                    min_value=0, 
                    max_value=100, 
                    value=100, 
                    step=1,
                    help="Lower = more similar. Only applies to vector search."
                )
            
            with col4:
                st.write("")  # Spacing
                search_button = st.button("🔍 Search", type="primary", use_container_width=True)
            
            # Metadata filters (expandable)
            with st.expander("🔧 Advanced Filters (Optional)"):
                # Get sample data to determine filterable columns
                sample_size = min(1000, total_rows)
                sample_df = tbl.head(sample_size).to_pandas()
                filterable_cols = get_filterable_columns(sample_df)
                
                if filterable_cols:
                    st.caption(f"Analyzed {sample_size} rows to determine filter options")
                    
                    active_filters = {}
                    
                    for col_name, col_info in filterable_cols.items():
                        st.markdown(f"**{col_name}**")
                        
                        if col_info['type'] == 'categorical':
                            selected_values = st.multiselect(
                                f"Filter by {col_name}",
                                options=col_info['values'],
                                key=f"filter_{col_name}"
                            )
                            if selected_values:
                                active_filters[col_name] = {'type': 'categorical', 'values': selected_values}
                        
                        elif col_info['type'] == 'numeric':
                            col_min, col_max = st.slider(
                                f"Range for {col_name}",
                                min_value=col_info['min'],
                                max_value=col_info['max'],
                                value=(col_info['min'], col_info['max']),
                                key=f"filter_{col_name}"
                            )
                            if col_min != col_info['min'] or col_max != col_info['max']:
                                active_filters[col_name] = {'type': 'numeric', 'min': col_min, 'max': col_max}
                        
                        elif col_info['type'] == 'date':
                            date_min, date_max = st.date_input(
                                f"Date range for {col_name}",
                                value=(col_info['min'], col_info['max']),
                                key=f"filter_{col_name}"
                            )
                            if date_min != col_info['min'] or date_max != col_info['max']:
                                active_filters[col_name] = {'type': 'date', 'min': date_min, 'max': date_max}
                    
                    # Store filters in session state for use in search
                    st.session_state['active_filters'] = active_filters
                    
                    if active_filters:
                        st.success(f"✅ {len(active_filters)} filter(s) active")
                else:
                    st.info("No filterable columns detected in this table")
            
            # === SEARCH RESULTS ===
            if search_button and search_query:
                st.divider()
                
                if search_mode == "Vector Search":
                    st.subheader("📊 Vector Search Results")
                    
                    with st.spinner("Searching with vector similarity..."):
                        results = vector_search(search_query, limit=result_limit)
                    
                    if results is not None and len(results) > 0:
                        df_results = pd.DataFrame(results)
                        
                        if 'active_filters' in st.session_state and st.session_state['active_filters']:
                            pre_filter_count = len(df_results)
                            df_results = apply_filters(df_results, st.session_state['active_filters'])
                            st.info(f"Filters applied: {pre_filter_count} → {len(df_results)} results")

                        # Apply distance threshold if there's a distance/score column
                        distance_col = None
                        for col in ['_distance', 'distance', 'score', '_score']:
                            if col in df_results.columns:
                                distance_col = col
                                break
                        
                        if distance_col:
                            df_results = df_results[df_results[distance_col] <= similarity_threshold]
                            st.caption(f"Showing {len(df_results)} results within distance threshold of {similarity_threshold}")
                        
                        # Display results
                        for idx, row in df_results.iterrows():
                            with st.expander(f"Result #{idx + 1} - Distance: {row.get(distance_col, 'N/A'):.4f}" if distance_col else f"Result #{idx + 1}"):
                                # Show all columns except vector
                                display_dict = {k: v for k, v in row.items() if k != 'vector'}
                                st.json(display_dict)
                        
                        # Full table view
                        st.subheader("Table View")
                        display_df = df_results.drop(columns=['vector']) if 'vector' in df_results.columns else df_results
                        st.dataframe(display_df, use_container_width=True)
                    else:
                        st.warning("No results found")
                
                elif search_mode == "Full-Text Search":
                    st.subheader("📝 Full-Text Search Results")
                    
                    with st.spinner("Searching with full-text search..."):
                        results = fts_search(search_query, limit=result_limit)
                    
                    if results is not None and len(results) > 0:
                        df_results = pd.DataFrame(results)
                        
                        st.caption(f"Found {len(df_results)} results")
                        
                        # Display results
                        for idx, row in df_results.iterrows():
                            score = row.get('score', row.get('_score', 'N/A'))
                            with st.expander(f"Result #{idx + 1} - Score: {score}"):
                                display_dict = {k: v for k, v in row.items() if k != 'vector'}
                                st.json(display_dict)
                        
                        # Full table view
                        st.subheader("Table View")
                        display_df = df_results.drop(columns=['vector']) if 'vector' in df_results.columns else df_results
                        st.dataframe(display_df, use_container_width=True)
                    else:
                        st.warning("No results found")
                
                elif search_mode == "Both":
                    st.subheader("🔄 Side-by-Side Comparison")
                    
                    col_vec, col_fts = st.columns(2)
                    
                    with col_vec:
                        st.markdown("### 📊 Vector Search")
                        with st.spinner("Searching..."):
                            vector_results = vector_search(search_query, limit=result_limit)
                        
                        if vector_results is not None and len(vector_results) > 0:
                            df_vector = pd.DataFrame(vector_results)
                            
                            # Apply threshold
                            distance_col = None
                            for col in ['_distance', 'distance', 'score', '_score']:
                                if col in df_vector.columns:
                                    distance_col = col
                                    break
                            
                            if distance_col:
                                df_vector = df_vector[df_vector[distance_col] <= similarity_threshold]
                            
                            st.caption(f"{len(df_vector)} results")
                            
                            for idx, row in df_vector.iterrows():
                                dist = row.get(distance_col, 'N/A')
                                dist_str = f"{dist:.4f}" if isinstance(dist, (int, float)) else str(dist)
                                with st.expander(f"#{idx + 1} - Dist: {dist_str}"):
                                    display_dict = {k: v for k, v in row.items() if k != 'vector'}
                                    st.json(display_dict)
                        else:
                            st.warning("No vector results")
                    
                    with col_fts:
                        st.markdown("### 📝 Full-Text Search")
                        with st.spinner("Searching..."):
                            fts_results = fts_search(search_query, limit=result_limit)
                        
                        if fts_results is not None and len(fts_results) > 0:
                            df_fts = pd.DataFrame(fts_results)
                            st.caption(f"{len(df_fts)} results")
                            
                            for idx, row in df_fts.iterrows():
                                score = row.get('score', row.get('_score', 'N/A'))
                                with st.expander(f"#{idx + 1} - Score: {score}"):
                                    display_dict = {k: v for k, v in row.items() if k != 'vector'}
                                    st.json(display_dict)
                        else:
                            st.warning("No FTS results")
            
            elif search_button and not search_query:
                st.warning("⚠️ Please enter a search query")
        
        # === BROWSE MODE ===
        elif mode == "📋 Browse":
            st.header("📋 Browse Mode")
            
            limit = st.slider("Rows to preview", 10, 500, 50)
            
            with st.spinner(f"Loading {limit} rows..."):
                df = tbl.head(limit).to_pandas()
            
            st.subheader(f"Previewing first {limit} rows")
            display_df = df.drop(columns=['vector']) if 'vector' in df.columns else df
            st.dataframe(display_df, use_container_width=True)
            
            # Show column info
            with st.expander("📊 Column Information"):
                st.write(f"**Total Columns:** {len(df.columns)}")
                st.write("**Columns:**")
                for col in df.columns:
                    if col == 'vector':
                        st.write(f"- `{col}` (excluded from display)")
                    else:
                        st.write(f"- `{col}` ({df[col].dtype})")
            
except Exception as e:
    st.error(f"Could not connect to database: {e}")
    st.exception(e)