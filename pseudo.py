# SunRun Pseudo-code

# Architecture

profile = {
    "id":"",
    "personality": "",
    "vocation":"",
    "vessel":"",
    "adventure":""
}

user_inputs = {}

### ACTION 1: SAVE PROFILE

# Field/Personality Retrieval & Storage Script

def profile_setup():
    for field, value in profile:
        if value: 
            user_inputs[field] = value
        else: 
            user_inputs[field] = model.generate_content(contents = f"come up with a hypothetical {field} for a plant").text

# Save Profile Data

def profile_save():
    profile_data = profile_setup()
    database.store("plant_profile", profile_data)


# User Interaction - Save Profile

if st.button("Save Plant"):
    profile_setup(profile)
    profile_save(user_inputs)
    print("Your Pal is Saved!")

### ACTION 2: RETRIEVE TODAY'S LOG

# Fetch Sunrunner Data

def sunrun_fetch():
    return collect_sensor_data()

# Fetch Profile
def profile_fetch():
    return database.fetch("plant_profile")

# Process Sunrunner Data

def process_sunrun(sunrunner_data):
    total_sun = sum(entry["sun_exposure"] for entry in sunrunner_data)
    total_sun = total_sun/(len(sunrunner_data)*100)
    total_steps = len(sunrunner_data)

    return total_sun, total_steps

# Package Data for Gemini

def gemini_data(total_sun, total_steps, plant_profile):
    processed_data = {
        "total_sun": total_sun,
        "total_steps": total_steps,
        "name": plant_profile["name"],
        "personality": plant_profile["personality"],
        "vocation": plant_profile['vocation'],
        "vessel": plant_profile['vessel'],
        "adventure": plant_profile['adventure']
    }

# Query Gemini

def query_gemini():
    processed_data = processed_data
    prompt = f"{processed_data['name']} is a plant that is a {processed_data['vocation']}. They are {processed_data['personality']} and they live in their {processed_data['vessel']}. 
    Their ideal adventure is {['adventure']}. Their sun exposure today was {processed_data['total_sun']} and they took {processed_data['total_steps']}.
    Write a log coming from the plant as if it were a person reporting on their day."
    log = model.generate_content(contets=prompt).text

# Visualization

def visualization(sunrunner_data): # Got a little help here :).
    x, y = 0, 0
    x_positions = [x]
    y_positions = [y]

    for entry in sunrunner_data:
        direction = np.radians(entry["direction"]) 
        step_size = 1  

        x += step_size * np.cos(direction)
        y += step_size * np.sin(direction)

        x_positions.append(x)
        y_positions.append(y)

    plt.figure(figsize=(6,6))
    plt.plot(x_positions, y_positions, marker="o", linestyle="-", color="blue", markersize=4)
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.title("SunRunner Movement Path")
    plt.grid(True)
    plt.show()

if st.button("Today's Log"):
    sunrunner_data = sunrun_fetch()
    plant_profile = profile_fetch()
    process_sunrun(sunrunner_data)
    gemini_data(total_sun, total_steps, plant_profile)
    print("Today's Log")
    print(log)
    visualization(sunrunner_data)
