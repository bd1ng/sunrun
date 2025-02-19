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
c.execute("""
    CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        personality TEXT,
        vocation TEXT,
        adventure TEXT,
        vessel TEXT,
        image_path TEXT
    )
""")
conn.commit()

# Ensure "New" plant always exists in database
c.execute("INSERT OR IGNORE INTO plants (name, image_path) VALUES (?, ?)", ("New", "plants_images/stock.jpg"))
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
            background-color: #6B705C !important; /* Grayish olive green */
            padding-left: 20px; /* Added padding to the left */
        }
        .title-container {
            margin-bottom: 15px; /* Ensures space between title and plants */
            text-align: center;
        }
        .plant-container-wrapper {
            display: flex;
            overflow-x: auto; /* ✅ Enables horizontal scrolling */
            justify-content: center; /* ✅ Centers the row inside the sidebar */
            white-space: nowrap; /* ✅ Keeps plants in one row */
            padding-bottom: 10px; /* Adds space for scrollbar */
            scrollbar-width: thin; /* For Firefox */
        }
        .plant-container {
            display: inline-block; /* ✅ Ensures elements stay in a row */
            width: 100px; /* ✅ Each plant card has a fixed width */
            text-align: center;
            margin: 0 10px; /* ✅ Adds even spacing between plants */
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
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar UI
with st.sidebar:
    
    st.markdown("<div class='title-container'><h1>🌱 Your Plant Crew</h1></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="plant-container-wrapper">
    """, unsafe_allow_html=True)
    
    # Fetch one plant for testing
    plants = c.execute("SELECT name, image_path FROM plants ORDER BY CASE WHEN name = 'New' THEN 1 ELSE 0 END, name ASC").fetchall()


    html_content = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
            .plant-container-wrapper {
                display: flex;
                overflow-x: auto;
                white-space: nowrap;
                padding-bottom: 10px;
                scrollbar-width: none; /* ✅ For Firefox */
                justify-content: center; /* ✅ Center the plants */

                -ms-overflow-style: none;  /* ✅ Hides scrollbar in Internet Explorer & Edge */
                scrollbar-width: none;      /* ✅ Hides scrollbar in Firefox */
            }
            .plant-container {
                display: inline-block;
                width: 100px;
                text-align: center;
                margin: 0 10px; /* ✅ Adds spacing between plants */
                font-family: 'Inter', sans-serif; /* ✅ Matches Streamlit’s font */
            }
            .plant-image-container {
                position: relative;
                display: inline-block;
                width: 80px;
                height: 80px;
            }
            .plant-image {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 4px solid #A5A58D;
                object-fit: cover;
            }
            .plant-name {
            font-weight: 600; /* ✅ Bold font */
            font-size: 14px; /* ✅ Adjust size for better readability */
            color: #262730; /* ✅ Matches Streamlit’s default text color */
            text-align: center;
            margin-top: 5px;
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
                transform: translate(25%, 25%);
            }
        </style>
        <div class="plant-container-wrapper">
    """

    # ✅ Loop through plants and add them to the HTML content
    for plant_name, image_path in plants:
        encoded_image = encode_image(image_path)
        add_icon = '<div class="add-icon">+</div>' if plant_name.strip() == 'New' else ''

        html_content += f"""
            <div class="plant-container">
                <div class="plant-image-container">
                    <img src="data:image/png;base64,{encoded_image}" class="plant-image">
                    {add_icon}
                </div>
                <p class="plant-name">{plant_name}</p>
            </div>
        """

    html_content += "</div>"  # ✅ Close the wrapper div

    # ✅ Use `components.html()` instead of `st.markdown()`
    components.html(html_content, height=150, scrolling=True)

    # Plant Profile Form
    st.markdown("---")
    st.markdown("<div class='title-container'><h2>🌿 Create a New Plant Profile</h2></div>", unsafe_allow_html=True)
    
    plant_name_input = st.text_input("Your Pal's Name", placeholder="e.g. Elvis Parsley")
    image_upload = st.file_uploader("Your Pal's Photo", type=["jpg", "png", "jpeg"])
    personality_input = st.text_area("Their Personality", placeholder="Are they adventurous? Or sassy?")
    vocation_input = st.text_area("Their Hustle", placeholder="What are they up? Are they a sailor, explorer, librarian?")
    vessel_input = st.text_area("Their Ride",placeholder="What's your plant's sweet ride — a ship, a balloon?")
    adventure_input = st.text_area("Their Ideal Adventure", placeholder="Describe an adventure that would make your pal smile.")
    
    if st.button("Save Plant"):
        if plant_name_input and personality_input and vocation_input and adventure_input and vessel_input:
            image_path = f"plants_images/{plant_name_input}.jpg" if image_upload else "plants_images/stock.jpg"
            
            if image_upload:
                with open(image_path, "wb") as f:
                    f.write(image_upload.read())
            
            c.execute("INSERT INTO plants (name, personality, vocation, adventure, vessel, image_path) VALUES (?, ?, ?, ?, ?, ?)",
                      (plant_name_input, personality_input, vocation_input, adventure_input, vessel_input, image_path))
            conn.commit()
            st.success(f"{plant_name_input} is ready to rock and roll! 🌱")
        else:
            st.error("Hold on! We need more info about your pal!")
