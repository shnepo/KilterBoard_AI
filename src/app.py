import streamlit as st
import matplotlib.pyplot as plt
import random

# Import your core logic
import parsing
from route_representation import generate_kilter_board_layout, Route
from route_generator import GeneticRouteGenerator

# --- SETUP & CONFIG ---
st.set_page_config(layout="wide", page_title="KilterGen: Evolutionary Route Solver")

# Initialize Session State
if 'board' not in st.session_state:
    st.session_state['board'] = generate_kilter_board_layout()
    st.session_state['generator'] = GeneticRouteGenerator(st.session_state['board'])
    st.session_state['population'] = []
    st.session_state['generation_count'] = 0

# --- HELPER: DRAWING ---
def draw_route_thumbnail(route: Route, board_data: dict) -> plt.Figure:
    """
    Draws a simplified view of the route using Kilter board color standards.
    """
    fig, ax = plt.subplots(figsize=(2.5, 3.5)) 
    
    # 1. Draw Background (Ghost Holds)
    all_x = [h.x for h in board_data.values()]
    all_y = [h.y for h in board_data.values()]
    ax.scatter(all_x, all_y, c='grey', s=5, alpha=0.3, zorder=1)
    
    # 2. Draw Connections (The Flow)
    r_coords = route.get_coordinates()
    
    # Draw path line (simple dashed line)
    ax.plot(r_coords['x'], r_coords['y'], c='#00AAAA', lw=3, alpha=0.6, linestyle='--', zorder=2)
    
    # 3. Draw Route Holds (The Kilter Colors)
    starts = route.start_holds
    top = route.top_hold
    
    for hid in route.holds:
        h = board_data[hid]
        color = '#00FFFF'  # Cyan for mid-holds
        size = 150 * h.size
        
        if hid in starts:
            color = '#00FF00' # Green for Start
            size = 180 * h.size
        elif hid == top:
            color = '#FF00FF' # Magenta for Finish
            size = 180 * h.size
        
        ax.scatter(h.x, h.y, c=color, s=size, edgecolors='black', linewidths=1.5, zorder=4)

    # Final plot cleanup
    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.1, 1.1)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    plt.tight_layout()
    return fig

# --- SIDEBAR: INPUTS ---
st.sidebar.title("KilterGen AI 🍌")
st.sidebar.subheader("Route Parameters")

diff_input = st.sidebar.selectbox(
    "Target Difficulty", 
    ["V3-V5 (Beginner)", "V6-V8 (Intermediate)", "V9+ (Advanced)", "V12 (Expert)"]
)

st.sidebar.markdown("##### Route Style")

# --- NEW STYLE BUTTONS ---
style_options = ["Dynamic", "Crimpy/Technical", "Traverse/Endurance", "Sloper/Pinch"]
active_styles = []

for option in style_options:
    if st.sidebar.checkbox(f"**{option}**", key=f"style_{option}"):
        active_styles.append(option)
# --------------------------

# Calculate parameters
difficulty_val = parsing.parse_difficulty(diff_input.split(" ")[0])
style_params = parsing.parse_style(active_styles) # Pass list of active styles

st.sidebar.write("---")

# Main action buttons
if st.session_state['generation_count'] == 0 and len(st.session_state['population']) == 0:
    if st.sidebar.button("🚀 Generate First Population", use_container_width=True, type="primary"):
        gen = st.session_state['generator']
        st.session_state['population'] = gen.init_population(difficulty_val, style_params)
        st.session_state['generation_count'] = 1
        st.rerun()
else:
    if st.sidebar.button("Reset / New Project", use_container_width=True):
        st.session_state['population'] = []
        st.session_state['generation_count'] = 0


# --- MAIN LOGIC ---

# Display the active styles to the user
display_styles = ", ".join(active_styles) if active_styles else "Generic/Balanced"

st.title(f"Interactive Route Evolution")
st.markdown(f"**Generation:** **{st.session_state['generation_count']}** | **Target Difficulty:** `{diff_input}` | **Style:** `{display_styles}`")

if st.session_state['generation_count'] == 0:
    st.info("Set your parameters in the sidebar and press 'Generate First Population' to begin!")
else:
    st.markdown("### Select your favorite routes to breed the next generation.")
    
    with st.form("evolution_form"):
        pop = st.session_state['population']
        
        # Display Grid of Routes (4 columns)
        cols = st.columns(4)
        selected_indices = []
        
        display_limit = 12 
        
        for i in range(min(len(pop), display_limit)):
            route = pop[i]
            
            with cols[i % 4]:
                fig = draw_route_thumbnail(route, st.session_state['board'])
                st.pyplot(fig)
                
                # Display the current length of the route for visibility
                st.caption(f"Holds: {len(route.holds)}") 
                
                # Checkbox for user selection (Human Boost)
                if st.checkbox(f"Keep Route {i+1}", key=f"c_{st.session_state['generation_count']}_{i}"):
                    selected_indices.append(i)
        
        st.write("---")
        evolve_btn = st.form_submit_button("🧬 Evolve Next Generation (Breed Selected Routes)", type="primary", use_container_width=True)
        
        if evolve_btn:
            if not selected_indices:
                st.warning("Please select at least one route to guide the AI's evolution!")
            else:
                st.info(f"Breeding {len(selected_indices)} favorites...")
                gen = st.session_state['generator']
                new_pop = gen.evolve(
                    st.session_state['population'], 
                    selected_indices, 
                    difficulty_val, 
                    style_params
                )
                st.session_state['population'] = new_pop
                st.session_state['generation_count'] += 1
                
                st.rerun()

    # Optional: Display the best routes found so far
    if st.session_state['population']:
        st.markdown("---")
        st.subheader("Current Elite Route")
        best_route = st.session_state['population'][0] 
        best_fig = draw_route_thumbnail(best_route, st.session_state['board'])
        st.pyplot(best_fig)
        st.markdown(f"**Length:** **{len(best_route.holds)}** moves.")