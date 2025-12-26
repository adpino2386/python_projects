"""
Script to help replace use_container_width with width parameter
This is a helper file documenting the replacement needed
"""

# Replacements needed:
# use_container_width=True  -> width='stretch'
# use_container_width=False -> width='content'

# For st.dataframe: use width='stretch' or width='content'
# For st.plotly_chart: use width='stretch' or width='content'  
# For st.button: width parameter not applicable, remove use_container_width

