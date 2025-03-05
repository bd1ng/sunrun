# import packages
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
import os
import streamlit as st
import sqlite3
import shutil
import base64
import html
import streamlit.components.v1 as components
import streamlit_javascript as st_javascript
import pandas as pd
from plant_movement_viz import display_movement_visualization, display_crew_logs
import time
from datetime import datetime

# Initialize session states
if 'selected_plant' not in st.session_state:
    st.session_state.selected_plant = None

if 'clicked_plant_name' not in st.session_state:
    st.session_state.clicked_plant_name = None

if 'selected_option' not in st.session_state:
    st.session_state.selected_option = "Create New Plant"

def main():
    # Ensure image directory exists
    os.makedirs("plants_images", exist_ok=True)

    # set up key
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path=dotenv_path)
    key = os.getenv("KEY")
    genai.configure(api_key=key)

    # initialize session
    model = genai.GenerativeModel('gemini-1.5-flash')
    chat = model.start_chat(history=[])

    ##### DATABASE #####
    # Database setup
    conn = sqlite3.connect("plant_db.db", check_same_thread=False)
    c = conn.cursor()

    # Add title column if it doesn't exist
    try:
        c.execute("ALTER TABLE plants ADD COLUMN title TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    c.execute("""
        CREATE TABLE IF NOT EXISTS plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            personality TEXT,
            vocation TEXT,
            adventure TEXT,
            vessel TEXT,
            image_path TEXT,
            title TEXT
        )
    """)
    conn.commit()

    # Ensure stock.jpg exists in plants_images directory
    stock_image_path = "plants_images/stock.jpg"
    if not os.path.exists(stock_image_path):
        shutil.copy("stock.jpg", stock_image_path)

    # Function to encode image to Base64
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Custom CSS for sidebar styling
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                background-color: #6B705C !important;
                color: #FFFFFF;        
            }
            .title-container {
                margin-bottom: 15px;
                text-align: center;
            }
            .plant-container-wrapper {
                display: flex;
                overflow-x: auto;
                justify-content: flex-start;
                white-space: nowrap;
                padding-bottom: 10px;
                padding-left: 0;
                margin-left: -1rem;
                width: calc(100% + 2rem);
                /* Hide scrollbars while keeping scroll functionality */
                scrollbar-width: none; /* Firefox */
                -ms-overflow-style: none; /* IE and Edge */
            }
            /* Hide scrollbar for Chrome, Safari and Opera */
            .plant-container-wrapper::-webkit-scrollbar {
                display: none;
            }
            /* Hide scrollbar for the component's iframe */
            iframe {
                scrollbar-width: none !important;
                -ms-overflow-style: none !important;
            }
            iframe::-webkit-scrollbar {
                display: none !important;
            }
            .plant-container {
                display: inline-block;
                min-width: 100px; /* Changed to min-width to ensure consistent sizing */
                flex-shrink: 0; /* Prevent shrinking */
                text-align: center;
                margin: 0 10px;
            }
            .plant-image-container {
                position: relative;
                display: inline-block;
            }
            .plant-image {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 4px solid #A5A58D;
                object-fit: cover;
            }
            .plant-name {
                margin-top: 5px;
                font-weight: bold;
                text-align: center;
            }
            .add-icon {
                width: 24px;
                height: 24px;
                background-color: white;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 18px;
                font-weight: bold;
                color: green;
                position: absolute;
                bottom: 0;
                right: 0;
                transform: translate(5%, 5%);
                border: none;
            }
            /* Style the save button */
            [data-testid="stSidebar"] .stButton button {
                color: #6B705C !important;
                background-color: white !important;
                border-color: white !important;
            }
            
            [data-testid="stSidebar"] .stButton button:hover {
                color: #6B705C !important;
                background-color: #f0f0f0 !important;
                border-color: #f0f0f0 !important;
            }

                /* Style field titles */
                [data-testid="stSidebar"] label {
                    color: white !important;
                    font-size: 1.1em !important;
                    font-weight: bold !important;
                    margin-bottom: 8px !important;
                }

                /* Make text inputs black */
                [data-testid="stSidebar"] textarea {
                    color: black !important;
                    background-color: white !important;
                }
                [data-testid="stSidebar"] input[type="text"] {
                    color: black !important;
                    background-color: white !important;
                }

                /* Style placeholder text */
                [data-testid="stSidebar"] textarea::placeholder,
                [data-testid="stSidebar"] input[type="text"]::placeholder {
                    color: #666666 !important;
                    opacity: 0.8;
                }

                /* Center buttons container */
                .buttons-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 10px;
                    margin: 20px auto;
                    width: 100%;
                    flex-wrap: wrap;
                }

                /* Style buttons to be equal width */
                [data-testid="stSidebar"] .element-container {
                    width: 100%;
                }

                [data-testid="stSidebar"] .row-widget.stButton {
                    text-align: center;
                    display: inline-block;
                }
                
                [data-testid="stSidebar"] .stButton button {
                    color: #6B705C !important;
                    background-color: white !important;
                    border-color: white !important;
                    min-width: 110px !important;
                    padding: 0.5rem 1rem !important;
                    margin: 0 5px !important;
                    height: 40px !important;
                    line-height: 1.2 !important;
                    white-space: nowrap !important;
                    display: inline-block !important;
                }
                
                [data-testid="stSidebar"] .stButton button:hover {
                    color: #6B705C !important;
                    background-color: #f0f0f0 !important;
                    border-color: #f0f0f0 !important;
                }

                /* Container for buttons */
                .button-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 20px;
                    margin: 20px auto;
                    width: 100%;
                }

                /* Remove any existing button margins and adjust container */
                [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
                    gap: 20px;
                    justify-content: center;
                    margin: 0 auto;
                }

                [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="column"] {
                    flex: 0 1 auto;
                    min-width: auto;
                }

                /* Style buttons */
                [data-testid="stSidebar"] .stButton {
                    margin: 0;
                }
                
                [data-testid="stSidebar"] .stButton button {
                    color: #6B705C !important;
                    background-color: white !important;
                    border-color: white !important;
                    min-width: 110px !important;
                    padding: 0.5rem 1rem !important;
                    height: 40px !important;
                    line-height: 1.2 !important;
                    white-space: nowrap !important;
                    margin: 0 !important;
                }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='title-container'><h2>🌱  Your Plant Crew</h2></div>", unsafe_allow_html=True)

    plants = c.execute("SELECT name, image_path, title FROM plants ORDER BY name ASC").fetchall()

    if not plants:
        st.error("❌ ERROR: No plants found in the database!")
    else:
        st.markdown(
            f"""
            <div style="text-align: center; color: #666666; font-style: italic; margin-bottom: 20px;">
                Your Crew Has {len(plants)} Pals
            </div>
            """,
            unsafe_allow_html=True
        )

    html_content = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
            
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen-Sans, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
            }
            
            .outer-container {
                width: 100%;
                padding-right: 20px;
            }
            
            .scroll-container {
                width: 100%;
                height: 100%;
                overflow: hidden;
            }
            
            .scroll-area {
                width: 100%;
                height: 100%;
                overflow-x: auto;
                padding-bottom: 20px;
                margin-bottom: -20px;
            }
            
            .plant-container-wrapper {
                display: flex;
                align-items: flex-start;
                gap: 20px;
                padding-right: 20px;
                min-width: min-content;
            }
            
            .plant-container {
                flex: 0 0 auto;
                width: 100px;
                text-align: center;
                cursor: pointer;
                transition: opacity 0.2s;
            }

            .plant-container.clicked {
                opacity: 0.7;
            }

            .plant-image-container {
                position: relative;
                width: 80px;
                height: 80px;
                margin: 0 auto;
            }

            .plant-image {
                width: 100%;
                height: 100%;
                border-radius: 50%;
                border: 4px solid #A5A58D;
                object-fit: cover;
            }

            .plant-name {
                    margin-top: 10px;
                    margin-bottom: 2px;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 16px;
                font-weight: 600;
                text-align: center;
                color: #6B705C;
                width: 100%;
                display: inline-block;
            }
            
                .plant-title {
                    font-family: 'Times New Roman', serif;
                    font-size: 12px;
                    font-style: italic;
                    text-align: center;
                    color: #A5A58D;
                    width: 100%;
                    display: inline-block;
                    margin-top: 0;
                    letter-spacing: 1px;
            }
        </style>

        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <div class="outer-container">
            <div class="scroll-container">
                <div class="scroll-area">
                    <div class="plant-container-wrapper">
    """

    # Loop through plants and add them to the HTML content
    for plant_name, image_path, title in plants:
        encoded_image = encode_image(image_path)
        title_display = title if title else "Wandering Plant"

        html_content += f"""
            <div class="plant-container" data-plant-name="{html.escape(plant_name)}">
                <div class="plant-image-container">
                    <img src="data:image/png;base64,{encoded_image}" class="plant-image">
                </div>
                <p class="plant-name">{plant_name}</p>
                <p class="plant-title">{title_display}</p>
            </div>
        """

    html_content += """
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=200, scrolling=True)

    # Add stylized date section
    def int_to_roman(num):
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        roman_num = ''
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman_num += syb[i]
                num -= val[i]
            i += 1
        return roman_num

    today = datetime.now()
    day_roman = int_to_roman(today.day)
    year_roman = int_to_roman(today.year)
    month_names = ["IANUARIUS", "FEBRUARIUS", "MARTIUS", "APRILIS", "MAIUS", "IUNIUS", 
                    "IULIUS", "AUGUSTUS", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]

    st.markdown(
        f"""
        <div style="text-align: center; margin: 20px 0; font-family: 'Times New Roman', serif;">
            <div style="font-size: 12px; color: #6B705C; letter-spacing: 3px;">ANNO DOMINI</div>
            <div style="font-size: 24px; color: #6B705C; font-weight: bold; letter-spacing: 5px; margin: 5px 0;">
                {day_roman} • {month_names[today.month - 1]} • {year_roman}
            </div>
            <div style="font-size: 10px; color: #A5A58D; letter-spacing: 2px; font-style: italic;">
                IN THE YEAR OF THE WANDERING PLANTS
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display plant details if one is selected
    if st.session_state.selected_plant and st.session_state.selected_plant != "New":
        # Fetch plant details from database
        plant_details = c.execute("""
            SELECT name, personality, vocation, adventure, vessel 
            FROM plants 
            WHERE name = ?
        """, (st.session_state.selected_plant,)).fetchone()
        
        if plant_details:
            st.markdown("---")
            st.markdown(f"### 🌿 {plant_details[0]}'s Profile")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Personality**")
                st.write(plant_details[1] if plant_details[1] else "No personality set yet!")
                
                st.markdown("**Vocation**")
                st.write(plant_details[2] if plant_details[2] else "No vocation set yet!")
            
            with col2:
                st.markdown("**Vessel**")
                st.write(plant_details[4] if plant_details[4] else "No vessel set yet!")
                
                st.markdown("**Adventure**")
                st.write(plant_details[3] if plant_details[3] else "No adventure set yet!")

    # Add Movement Visualization Section
    st.markdown("---")

    # Movement Tracking Section
    st.markdown("<h1 style='text-align: center;'>🌿 Your Crew's Log 🌿</h1>", unsafe_allow_html=True)

    if 'show_tracking' not in st.session_state:
        st.session_state.show_tracking = False

    if not st.session_state.show_tracking:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Initialize Crew Tracking", use_container_width=True):
                with st.spinner("🛰️ Establishing connection to tracking systems..."):
                    st.empty()
                    time.sleep(1)
                with st.spinner("📍 Calibrating position sensors..."):
                    st.empty()
                    time.sleep(1)
                with st.spinner("🌟 Activating crew monitoring..."):
                    st.empty()
                    time.sleep(1)
                st.session_state.show_tracking = True
                st.rerun()

    if st.session_state.show_tracking:
        # Create tabs
        tab1, tab2, tab3 = st.tabs([
            "🧭 Wayfinder",
            "📊 Crew Stats",
            "📝 Crew Logs"
        ])
        
        with tab1:
            st.markdown("<h2 style='text-align: center;'>🧭 Wayfinder</h2>", unsafe_allow_html=True)
            if 'movements.csv' in os.listdir():
                try:
                    movement_data = pd.read_csv('movements.csv')
                    plants = movement_data['Name'].unique().tolist()
                    display_movement_visualization(movement_data, plants, "plants_images")
                except Exception as e:
                    st.error(f"Error displaying movement visualization: {str(e)}")
        
        with tab2:
            st.markdown("<h2 style='text-align: center;'>📊 Crew Stats</h2>", unsafe_allow_html=True)
            if 'movements.csv' in os.listdir():
                try:
                    movements_df = pd.read_csv('movements.csv')
                    # Calculate statistics for each crew member
                    stats = movements_df.groupby('Name').agg({
                        'Distance Traveled (in)': ['mean', 'max'],
                        'Rotation (°)': ['mean', 'max'],
                        'UV Levels (%)': ['mean', 'max']
                    }).round(2)
                    
                    # Flatten column names
                    stats.columns = [f"{col[0]} ({col[1]})" for col in stats.columns]
                    
                    # Display statistics
                    st.dataframe(stats, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading crew statistics: {str(e)}")
        
        with tab3:
            if 'movements.csv' in os.listdir():
                try:
                    movement_data = pd.read_csv('movements.csv')
                    crew_members = movement_data['Name'].unique().tolist()
                    display_crew_logs(movement_data, crew_members)
                except Exception as e:
                    st.error(f"Error generating crew logs: {str(e)}")
            else:
                st.info("No movement data available yet. Start tracking your crew's journey to generate logs!")

    # Sidebar UI
    with st.sidebar:
        st.markdown("<div class='title-container'><h1>🌿 Roster Manager 🌿</h1></div>", unsafe_allow_html=True)
        
        # Get all plants
        existing_plants = c.execute("SELECT name FROM plants ORDER BY name ASC").fetchall()
        plant_names = [plant[0] for plant in existing_plants]
        
        # Function to handle selectbox change
        def on_select_change():
            st.session_state.selected_option = st.session_state.select_plant
            # Clear edit/create form states and temporary content when switching plants
            for key in ['edit_name', 'edit_title', 'edit_personality', 'edit_vocation', 'edit_vessel', 'edit_adventure', 'edit_photo',
                        'new_name', 'new_title', 'new_personality', 'new_vocation', 'new_vessel', 'new_adventure', 'new_photo',
                        'temp_generated_content']:
                if key in st.session_state:
                    del st.session_state[key]
        
        # Add "Create New Plant" option at the top
        options = ["Create New Plant"] + plant_names
        
        # Find the correct index, defaulting to 0 if not found
        try:
            current_index = options.index(st.session_state.selected_option)
        except ValueError:
            current_index = 0
            st.session_state.selected_option = "Create New Plant"
        
        selected_option = st.selectbox("Select a plant to edit or create new", 
                                        options, 
                                        key="select_plant",
                                        on_change=on_select_change,
                                        index=current_index)
        
        st.markdown("---")
        
        if selected_option == "Create New Plant":
            st.markdown("### 🌱 Create New Plant")
            
            # Display all form fields first
            plant_name_input = st.text_input("Your Pal's Name", 
                                            value=st.session_state.temp_generated_content.get('name', "") if 'temp_generated_content' in st.session_state else st.session_state.get('new_name', ""),
                                            placeholder="e.g. Elvis Parsley", 
                                            key="new_name")
            
            title_input = st.text_input("Their Title",
                                        value=st.session_state.temp_generated_content.get('title', "") if 'temp_generated_content' in st.session_state else st.session_state.get('new_title', ""),
                                        placeholder="e.g. Cosmic Navigator",
                                        key="new_title")
            
            image_upload = st.file_uploader("Your Pal's Photo", type=["jpg", "png", "jpeg"], key="new_photo")
            
            personality_input = st.text_area("Their Personality", 
                                            value=st.session_state.temp_generated_content.get('personality', "") if 'temp_generated_content' in st.session_state else st.session_state.get('new_personality', ""),
                                            placeholder="Are they adventurous? Or sassy?", 
                                            key="new_personality")
            
            vocation_input = st.text_area("Their Hustle", 
                                        value=st.session_state.temp_generated_content.get('vocation', "") if 'temp_generated_content' in st.session_state else st.session_state.get('new_vocation', ""),
                                        placeholder="What are they up? Are they a sailor, explorer, librarian?", 
                                        key="new_vocation")
            
            vessel_input = st.text_area("Their Ride", 
                                        value=st.session_state.temp_generated_content.get('vessel', "") if 'temp_generated_content' in st.session_state else st.session_state.get('new_vessel', ""),
                                        placeholder="What's your plant's sweet ride — a ship, a balloon?", 
                                        key="new_vessel")
            
            adventure_input = st.text_area("Their Ideal Adventure", 
                                            value=st.session_state.temp_generated_content.get('adventure', "") if 'temp_generated_content' in st.session_state else st.session_state.get('new_adventure', ""),
                                            placeholder="Describe an adventure that would make your pal smile.", 
                                            key="new_adventure")
            
            # Buttons row
            st.markdown('<div class="button-wrapper">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Plant", key="save_btn", use_container_width=True):
                    if plant_name_input and personality_input and vocation_input and adventure_input and vessel_input:
                        image_path = f"plants_images/{plant_name_input}.jpg" if image_upload else "plants_images/stock.jpg"
                        
                        if image_upload:
                            with open(image_path, "wb") as f:
                                f.write(image_upload.read())
                        
                        c.execute("INSERT INTO plants (name, personality, vocation, adventure, vessel, image_path, title) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (plant_name_input, personality_input, vocation_input, adventure_input, vessel_input, image_path, title_input))
                        conn.commit()
                        
                        # Clear session states
                        for key in ['new_name', 'new_title', 'new_personality', 'new_vocation', 'new_vessel', 'new_adventure', 'new_photo', 'temp_generated_content']:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.rerun()
                    else:
                        st.error("Hold on! We need more info about your pal!")
            
            with col2:
                if st.button("Help Me ✨", key="help_btn", use_container_width=True):
                    st.info("🔍 Starting content generation...")
                    
                    # Store current values and preserve them in generated content
                    current_values = {
                        'name': plant_name_input,
                        'title': title_input,
                        'personality': personality_input,
                        'vocation': vocation_input,
                        'vessel': vessel_input,
                        'adventure': adventure_input
                    }

                    # Initialize temporary content with current non-empty values
                    generated_content = {k: v for k, v in current_values.items() if v}
                    
                    # Create prompt based on existing context
                    context_prompt = "Create a character with the following details. Focus on creating a believable persona that could be from any genre of fictional work - sci-fi, fantasy, detective, romance, or literary fiction. Always provide definitive statements, never questions. The character should maintain consistent identity and personality traits throughout all descriptions. "
                    if generated_content:
                        context_prompt += "Maintain consistency with these existing traits:\n"
                        for key, value in generated_content.items():
                            context_prompt += f"- {key}: {value}\n"
                    
                    # Only generate content for empty fields
                    if not plant_name_input:
                        name_response = chat.send_message(
                            f"{context_prompt}Generate a character name that would fit in a fictional book of any genre - sci-fi, fantasy, detective, romance, or literary fiction. The name should reflect their background and personality. Respond with just the name, no explanation."
                        )
                        generated_content['name'] = name_response.text.strip()
                    
                    if not title_input:
                        st.info("✨ Generating new title...")
                        title_response = chat.send_message(
                            f"{context_prompt}Generate a title or epithet (2-4 words) that reflects their role or nature (e.g. 'Cosmic Navigator', 'Keeper of Ancient Whispers'). The title should be poetic and mysterious while staying true to the character's established identity. Respond with just the title, no explanation."
                        )
                        generated_content['title'] = title_response.text.strip()
                        context_prompt += f"\n- title: {generated_content['title']}"
                    
                    if not personality_input:
                        st.info("✨ Generating personality...")
                        personality_response = chat.send_message(
                            f"{context_prompt}Write a compelling description of {plant_name_input}'s personality in 2-3 clear sentences. Focus on their unique traits, quirks, and what makes them memorable, while maintaining consistency with their name and title."
                        )
                        generated_content['personality'] = personality_response.text.strip()
                        context_prompt += f"\n- personality: {generated_content['personality']}"
                    
                    if not vocation_input:
                        st.info("✨ Generating vocation...")
                        vocation_response = chat.send_message(
                            f"{context_prompt}Describe {plant_name_input}'s profession or calling in 2-3 clear sentences. Focus on what they do and why they're passionate about it, ensuring it aligns with their established personality and title."
                        )
                        generated_content['vocation'] = vocation_response.text.strip()
                        context_prompt += f"\n- vocation: {generated_content['vocation']}"
                    
                    if not vessel_input:
                        st.info("✨ Generating vessel...")
                        vessel_response = chat.send_message(
                            f"{context_prompt}Describe {plant_name_input}'s signature mode of transport in 2-3 clear sentences. It can be unconventional. Make it unique and fitting to their established personality, title, and vocation."
                        )
                        generated_content['vessel'] = vessel_response.text.strip()
                        context_prompt += f"\n- vessel: {generated_content['vessel']}"
                    
                    if not adventure_input:
                        st.info("✨ Generating adventure...")
                        adventure_response = chat.send_message(
                            f"{context_prompt}Tell a defining adventure or moment in {plant_name_input}'s life in 2-3 clear sentences. Make it exciting and revealing while incorporating their established traits, title, and vocation."
                        )
                        generated_content['adventure'] = adventure_response.text.strip()
                        
                    # Store generated content and rerun once at the end
                    st.session_state.temp_generated_content = generated_content
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:  # Edit existing plant
            # Fetch current plant details
            plant_details = c.execute("""
                SELECT name, personality, vocation, adventure, vessel, image_path, title 
                FROM plants 
                WHERE name = ?
            """, (selected_option,)).fetchone()
            
            if plant_details:
                st.markdown("### ✏️ Edit Plant")
                plant_name_input = st.text_input("Name", 
                                                value=plant_details[0], 
                                                key="edit_name")
                title_input = st.text_input("Title",
                                                value=st.session_state.temp_generated_content.get('title', plant_details[6]) if 'temp_generated_content' in st.session_state else plant_details[6],
                                                key="edit_title")
                
                # Show current image centered
                current_image = plant_details[5]
                if current_image and os.path.exists(current_image):
                    col1, col2, col3 = st.columns([1,2,1])
                    with col2:
                        st.image(current_image, width=100, caption="Current Photo")
                else:
                    st.info("No current photo")
                
                image_upload = st.file_uploader("Update Photo (clear to use default)", type=["jpg", "png", "jpeg"], key="edit_photo")
                personality_input = st.text_area("Personality", 
                                                value=st.session_state.temp_generated_content.get('personality', plant_details[1]) if 'temp_generated_content' in st.session_state else plant_details[1], 
                                                key="edit_personality")
                vocation_input = st.text_area("Hustle", 
                                            value=st.session_state.temp_generated_content.get('vocation', plant_details[2]) if 'temp_generated_content' in st.session_state else plant_details[2],
                                            key="edit_vocation")
                vessel_input = st.text_area("Ride", 
                                            value=st.session_state.temp_generated_content.get('vessel', plant_details[4]) if 'temp_generated_content' in st.session_state else plant_details[4],
                                            key="edit_vessel")
                adventure_input = st.text_area("Adventure", 
                                                value=st.session_state.temp_generated_content.get('adventure', plant_details[3]) if 'temp_generated_content' in st.session_state else plant_details[3],
                                                key="edit_adventure")
                
                # Buttons container
                st.markdown('<div class="button-wrapper">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Update Plant", key="update_btn", use_container_width=True):
                        if plant_name_input and personality_input and vocation_input and adventure_input and vessel_input:
                            # Handle image update
                            if image_upload:
                                image_path = f"plants_images/{plant_name_input}.jpg"
                                with open(image_path, "wb") as f:
                                    f.write(image_upload.read())
                            else:
                                image_path = plant_details[5]  # Keep existing image if no new upload
                            
                            try:
                                # Update the plant in database
                                c.execute("""
                                    UPDATE plants 
                                    SET name=?, personality=?, vocation=?, adventure=?, vessel=?, image_path=?, title=?
                                    WHERE name=?
                                """, (plant_name_input, personality_input, vocation_input, adventure_input, 
                                        vessel_input, image_path, title_input, selected_option))
                                conn.commit()
                                
                                # Update the selected option to the new name
                                st.session_state.selected_option = plant_name_input
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error(f"A plant named '{plant_name_input}' already exists!")

                with col2:
                    if st.button("Help Me ✨", key="edit_help_btn", use_container_width=True):
                        try:
                            # Build context from all existing non-empty fields
                            existing_traits = {
                                'name': plant_name_input,
                                'title': title_input,
                                'personality': personality_input,
                                'vocation': vocation_input,
                                'vessel': vessel_input,
                                'adventure': adventure_input
                            }
                            
                            # Filter out empty values and build context
                            context = "Create content for a character with these existing traits:\n"
                            for trait, value in existing_traits.items():
                                if value and value.strip():
                                    context += f"- {trait}: {value}\n"
                            
                            context += "\nMaintain absolute consistency with these established traits when generating new content. The character should feel like a cohesive individual whose traits all connect logically."
                            
                            # Initialize temporary storage for generated content
                            temp_generated_content = {}
                            
                            # Generate content for empty fields
                            if not personality_input or personality_input.strip() == "":
                                personality_response = chat.send_message(
                                    f"{context}\nWrite a compelling description of their personality in 2-3 clear sentences. Focus on their unique traits, quirks, and what makes them memorable, but consistent with their other established characteristics."
                                )
                                temp_generated_content['personality'] = personality_response.text.strip()
                                context += f"\n- personality: {temp_generated_content['personality']}"
                            
                            if not vocation_input or vocation_input.strip() == "":
                                vocation_response = chat.send_message(
                                    f"{context}\nDescribe their profession or calling in 2-3 clear sentences. This should align with their established traits and explain how it fits their character."
                                )
                                temp_generated_content['vocation'] = vocation_response.text.strip()
                                context += f"\n- vocation: {temp_generated_content['vocation']}"
                            
                            if not vessel_input or vessel_input.strip() == "":
                                vessel_response = chat.send_message(
                                    f"{context}\nDescribe their signature mode of transport in 2-3 clear sentences, it can be an unconventional mode of transport. Make it a natural extension of their established character and activities."
                                )
                                temp_generated_content['vessel'] = vessel_response.text.strip()
                                context += f"\n- vessel: {temp_generated_content['vessel']}"
                            
                            if not adventure_input or adventure_input.strip() == "":
                                adventure_response = chat.send_message(
                                    f"{context}\nTell a defining adventure or moment in their life in 2-3 clear sentences. Make it exciting and this should showcase how their established traits come together in action."
                                )
                                temp_generated_content['adventure'] = adventure_response.text.strip()
                                context += f"\n- adventure: {temp_generated_content['adventure']}"
                            
                            if not title_input or title_input.strip() == "":
                                title_response = chat.send_message(
                                    f"{context}\nGenerate a title or epithet (2-4 words) that reflects their role or nature (e.g. 'Cosmic Navigator', 'Keeper of Ancient Whispers'). The title should be poetic and mysterious while staying true to the character's established identity. Respond with just the title, no explanation."
                                )
                                temp_generated_content['title'] = title_response.text.strip()
                            
                            # Store generated content in session state for next rerun
                            st.session_state.temp_generated_content = temp_generated_content
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error in content generation process: {str(e)}")

                with col3:
                    if st.button("Delete Plant", type="secondary", key="delete_btn", use_container_width=True):
                        try:
                            # Delete the plant from database
                            c.execute("DELETE FROM plants WHERE name=?", (selected_option,))
                            conn.commit()
                            
                            # Reset to Create New Plant after deletion
                            st.session_state.selected_option = "Create New Plant"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting plant: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
