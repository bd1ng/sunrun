import os
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image, ImageDraw
import base64
from io import BytesIO
import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import sqlite3

# Define color palette for plants
COLORS = [
    '#FF6B6B',  # Coral Red
    '#4ECDC4',  # Turquoise
    '#45B7D1',  # Sky Blue
    '#96CEB4',  # Sage Green
    '#FFEEAD',  # Cream Yellow
    '#D4A5A5',  # Dusty Rose
    '#9A8C98',  # Mauve
    '#C9ADA7',  # Taupe
    '#A5A58D',  # Olive
    '#FFB4A2',  # Peach
]

def create_circular_image(image_path, size=(100, 100)):
    """
    Create a circular image from a rectangular one and return as base64 URL.
    """
    # Open and resize image
    img = Image.open(image_path)
    img = img.convert('RGBA')
    img = img.resize(size, Image.Resampling.LANCZOS)
    
    # Create circular mask
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    
    # Apply mask
    output = Image.new('RGBA', size, (0, 0, 0, 0))
    output.paste(img, (0, 0))
    output.putalpha(mask)
    
    # Convert to base64
    buffer = BytesIO()
    output.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f'data:image/png;base64,{img_str}'

def calculate_positions(df):
    """
    Calculate cumulative X and Y positions from rotation angles and distances.
    """
    # Convert rotation to radians
    df['Rotation (rad)'] = np.radians(df['Rotation (°)'])
    
    # Calculate X and Y components for each movement
    df['X_step'] = df['Distance Traveled (in)'] * np.cos(df['Rotation (rad)'])
    df['Y_step'] = df['Distance Traveled (in)'] * np.sin(df['Rotation (rad)'])
    
    # Calculate cumulative positions for each plant
    positions = []
    for plant in df['Name'].unique():
        plant_data = df[df['Name'] == plant].copy()
        plant_data['X'] = plant_data['X_step'].cumsum()
        plant_data['Y'] = plant_data['Y_step'].cumsum()
        positions.append(plant_data)
    
    return pd.concat(positions)

def generate_crew_logs(positions_df, crew_members):
    """
    Generate narrative logs for each crew member using Gemini.
    """
    # Connect to the database to get plant personalities
    conn = sqlite3.connect("plant_db.db", check_same_thread=False)
    c = conn.cursor()
    
    # Prepare crew data summaries
    crew_data = {}
    for member in crew_members:
        member_data = positions_df[positions_df['Name'] == member]
        
        # Simplified movement statistics
        total_distance = member_data['Distance Traveled (in)'].sum()
        avg_uv = member_data['UV Levels (%)'].mean()
        
        # Get plant personality from database
        plant_details = c.execute("""
            SELECT personality, vocation, adventure, vessel, title 
            FROM plants 
            WHERE name = ?
        """, (member,)).fetchone()
        
        if plant_details:
            personality, vocation, adventure, vessel, title = plant_details
        else:
            personality = "mysterious"
            vocation = "wanderer"
            adventure = "exploring new horizons"
            vessel = "unknown vessel"
            title = "Wandering Plant"
        
        crew_data[member] = {
            'stats': {
                'total_distance': f"{total_distance:.1f}",
                'avg_uv': f"{avg_uv:.1f}"
            },
            'personality': personality,
            'vocation': vocation,
            'adventure': adventure,
            'vessel': vessel,
            'title': title
        }
    
    # Initialize Gemini
    key = os.getenv("KEY")
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Generate overall journey summary
    weather_condition = "sunny" if sum(float(data['stats']['avg_uv']) for data in crew_data.values())/len(crew_data) > 50 else "overcast"
    summary_prompt = f"""
    Write an intriguing, single-paragraph synopsis (like one you'd find on the back of a book) about today's botanical crew adventure.
    
    The crew consists of: {', '.join(f"{name} ({data['vocation']})" for name, data in crew_data.items())}.
    Setting: A {weather_condition} day aboard their vessels.
    
    Focus on:
    - One central mysterious or exciting event that happened today
    - A hint at the crew's shared purpose or mission
    - An enticing hook that makes readers want to know more
    
    Keep it concise (max 3-4 sentences) and make it feel like part of an ongoing magical expedition series.
    Don't resolve the central mystery - leave that for the individual logs to explore!
    """
    
    summary_response = model.generate_content(summary_prompt)
    journey_summary = summary_response.text
    
    # Generate individual logs
    crew_logs = {}
    for member, data in crew_data.items():
        # Create a rich context for each plant's perspective
        log_prompt = f"""
        Write a personal log entry from {member}'s perspective. They are a sentient plant with these traits:
        - Personality: {data['personality']}
        - Vocation: {data['vocation']}
        - Their vessel: {data['vessel']}
        - Dream adventure: {data['adventure']}
        
        Other crew members: {', '.join(f"{name} ({cdata['vocation']})" for name, cdata in crew_data.items() if name != member)}
        
        Write a single engaging paragraph that:
        1. Reveals their unique perspective on today's central mystery/event
        2. Shows their personality through their reaction
        3. Hints at their relationship with at least one other crew member
        
        Make it feel like a personal diary entry that adds a piece to the larger puzzle.
        """
        
        log_response = model.generate_content(log_prompt)
        crew_logs[member] = log_response.text
    
    conn.close()
    return {
        'summary': journey_summary,
        'logs': crew_logs
    }

def create_movement_visualization(positions_df, plants, plant_images_dir):
    """
    Create an animated visualization of plant movements.
    
    Args:
        positions_df: DataFrame with columns ['Name', 'Timestamp', 'Rotation (°)', 'Distance Traveled (in)', 'UV Levels (%)']
        plants: List of plant names
        plant_images_dir: Directory containing plant images named as plant_name.jpg
    
    Returns:
        plotly.graph_objects.Figure
    """
    # Calculate X and Y positions
    positions_df = calculate_positions(positions_df)
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Set axes to be fixed with some padding
    all_x = positions_df['X']
    all_y = positions_df['Y']
    x_range = [all_x.min() - 1, all_x.max() + 1]
    y_range = [all_y.min() - 1, all_y.max() + 1]
    
    # Get first timestamp data for initial state
    first_timestamp = positions_df['Timestamp'].min()
    initial_points = positions_df[positions_df['Timestamp'] == first_timestamp]
    
    # Add traces for each plant
    for idx, plant in enumerate(plants):
        plant_color = COLORS[idx % len(COLORS)]
        plant_initial = initial_points[initial_points['Name'] == plant]
        
        # Add plant markers first (so they appear in legend)
        fig.add_trace(
            go.Scatter(
                x=plant_initial['X'],
                y=plant_initial['Y'],
                mode='markers+text',
                name=plant,
                text=plant,
                textposition="top center",
                marker=dict(
                    size=20,
                    symbol='circle',
                    color=plant_color,
                    line=dict(
                        color=plant_color,
                        width=2
                    )
                ),
                showlegend=True,
                customdata=np.stack((
                    plant_initial['UV Levels (%)'],
                    plant_initial['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                    plant_initial['Rotation (°)'],
                    plant_initial['Distance Traveled (in)']
                ), axis=-1),
                hovertemplate=(
                    "<b>%{customdata[1]}</b><br>" +
                    "Plant: " + plant + "<br>" +
                    "Position: (%{x:.2f}, %{y:.2f})<br>" +
                    "Rotation: %{customdata[2]}°<br>" +
                    "Distance: %{customdata[3]} inches<br>" +
                    "UV Level: %{customdata[0]:.1f}%<br>" +
                    "<extra></extra>"
                )
            )
        )
        
        # Add connecting lines (empty at first)
        fig.add_trace(
            go.Scatter(
                x=plant_initial['X'],
                y=plant_initial['Y'],
                mode='lines',
                name=plant,
                line=dict(
                    color=plant_color,
                    width=2,
                    dash='solid'
                ),
                opacity=0.4,
                showlegend=False,  # Hide lines from legend
                hoverinfo='skip'
            )
        )

    # Create frames for animation
    frames = []
    timestamps = positions_df['Timestamp'].unique()
    for timestamp in timestamps:
        frame_data = positions_df[positions_df['Timestamp'] <= timestamp]  # Show cumulative paths
        current_points = positions_df[positions_df['Timestamp'] == timestamp]
        
        frame = go.Frame(
            data=[
                # Add markers first (for legend consistency)
                *[go.Scatter(
                    x=current_points[current_points['Name'] == plant]['X'],
                    y=current_points[current_points['Name'] == plant]['Y'],
                    mode='markers+text',
                    name=plant,
                    text=plant,
                    textposition="top center",
                    marker=dict(
                        size=20,
                        symbol='circle',
                        color=COLORS[idx % len(COLORS)],
                        line=dict(
                            color=COLORS[idx % len(COLORS)],
                            width=2
                        )
                    ),
                    showlegend=True,
                    customdata=np.stack((
                        current_points[current_points['Name'] == plant]['UV Levels (%)'],
                        current_points[current_points['Name'] == plant]['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                        current_points[current_points['Name'] == plant]['Rotation (°)'],
                        current_points[current_points['Name'] == plant]['Distance Traveled (in)']
                    ), axis=-1) if not current_points[current_points['Name'] == plant].empty else None,
                    hovertemplate=(
                        "<b>%{customdata[1]}</b><br>" +
                        "Plant: " + plant + "<br>" +
                        "Position: (%{x:.2f}, %{y:.2f})<br>" +
                        "Rotation: %{customdata[2]}°<br>" +
                        "Distance: %{customdata[3]} inches<br>" +
                        "UV Level: %{customdata[0]:.1f}%<br>" +
                        "<extra></extra>"
                    )
                ) for idx, plant in enumerate(plants)],
                # Add lines for paths
                *[go.Scatter(
                    x=frame_data[frame_data['Name'] == plant]['X'],
                    y=frame_data[frame_data['Name'] == plant]['Y'],
                    mode='lines',
                    name=plant,
                    line=dict(
                        color=COLORS[idx % len(COLORS)],
                        width=2,
                        dash='solid'
                    ),
                    opacity=0.4,
                    showlegend=False,
                    hoverinfo='skip'
                ) for idx, plant in enumerate(plants)]
            ],
            name=timestamp.strftime('%Y-%m-%d %H:%M:%S')
        )
        frames.append(frame)
    
    # Update figure layout
    fig.update_layout(
        xaxis=dict(
            range=x_range,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(128,128,128,0.4)',
            title="X Position (inches)",
            automargin=True
        ),
        yaxis=dict(
            range=y_range,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(128,128,128,0.4)',
            scaleanchor='x',
            scaleratio=1,
            title="Y Position (inches)",
            automargin=True
        ),
        showlegend=True,
        hovermode='closest',
        title="Today's Paths",
        margin=dict(l=80, r=80, t=100, b=80),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        updatemenus=[dict(
            type='buttons',
            showactive=False,
            buttons=[dict(
                label='Play',
                method='animate',
                args=[None, dict(
                    frame=dict(duration=1000, redraw=True),
                    fromcurrent=True,
                    mode='immediate'
                )]
            )]
        )],
        sliders=[{
            'currentvalue': {'prefix': 'Time: '},
            'pad': {'t': 50},
            'len': 0.9,
            'x': 0.1,
            'xanchor': 'left',
            'y': 0,
            'yanchor': 'top',
            'steps': [{
                'args': [[frame.name], dict(
                    frame=dict(duration=0, redraw=True),
                    mode='immediate',
                    transition=dict(duration=0)
                )],
                'label': frame.name,
                'method': 'animate'
            } for frame in frames]
        }]
    )
    
    # Add frames to the figure
    fig.frames = frames
    
    return fig

def display_crew_logs(positions_df, crew_members):
    """
    Display the crew logs in Streamlit with engaging teasers during generation.
    """
    st.markdown("<h2 style='text-align: center;'>🌿 Crew Entries 🌿</h2>", unsafe_allow_html=True)
    
    # Teaser messages that cycle during generation
    teasers = [
        "📡 Intercepting whispers from the botanical network...",
        "🌱 Decoding chlorophyll-encoded messages...",
        "🎭 Gathering tales from the wandering flora...",
        "🌟 Translating photosynthetic poetry...",
        "🎨 Illuminating stories of sunlit adventures...",
        "🌿 Unraveling leafy chronicles...",
        "🚀 Collecting dispatches from green voyagers...",
        "📖 Composing the day's botanical ballad...",
        "🎪 Assembling the garden's grand narrative...",
        "🎭 Channeling voices of the verdant crew..."
    ]
    
    if st.button("📡 Retrieve Crew Entries", use_container_width=True):
        # Create placeholder for teaser messages
        teaser_placeholder = st.empty()
        
        # Start generating logs in a separate thread
        import threading
        logs = [None]  # Use list to store result from thread
        
        def generate():
            logs[0] = generate_crew_logs(positions_df, crew_members)
        
        thread = threading.Thread(target=generate)
        thread.start()
        
        # Display cycling teasers until logs are ready
        while thread.is_alive():
            for teaser in teasers:
                if not thread.is_alive():
                    break
                with teaser_placeholder:
                    st.info(teaser)
                    time.sleep(0.5)
        
        # Clear the teaser and show success
        teaser_placeholder.empty()
        st.success("✨ Crew logs successfully retrieved!")
        
        st.markdown("### 📜 Journey Summary")
        st.write(logs[0]['summary'])
        
        st.markdown("### 👥 Individual Crew Perspectives")
        # Connect to the database to get titles
        conn = sqlite3.connect("plant_db.db", check_same_thread=False)
        c = conn.cursor()
        
        for member, log_data in logs[0]['logs'].items():
            # Get the title from the database
            title_result = c.execute("SELECT title FROM plants WHERE name = ?", (member,)).fetchone()
            title = title_result[0] if title_result and title_result[0] else "Wandering Plant"
            
            with st.expander(f"📝 Log of {member}, {title}"):
                st.write(log_data)
        
        conn.close()

def display_movement_visualization(positions_df, plants, plant_images_dir):
    """
    Display the plant movement visualization in Streamlit.
    
    Args:
        positions_df: DataFrame with columns ['Name', 'Timestamp', 'Rotation (°)', 'Distance Traveled (in)', 'UV Levels (%)']
        plants: List of plant names
        plant_images_dir: Directory containing plant images named as plant_name.jpg
    """
    # Convert Timestamp column to datetime if it's not already
    positions_df['Timestamp'] = pd.to_datetime(positions_df['Timestamp'])
    
    # Create the visualization figure
    fig = create_movement_visualization(positions_df, plants, plant_images_dir)
    
    # Display the figure in Streamlit
    st.plotly_chart(fig, use_container_width=True) 