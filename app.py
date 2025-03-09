import streamlit as st
import os
import time
import cv2
import numpy as np
from deepface import DeepFace
import firebase_admin
from firebase_admin import credentials, firestore
import cohere
import base64
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from PIL import Image
import pyautogui
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pytz


os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"


# Initialize session state variables
if "page" not in st.session_state:
    st.session_state["page"] = "main"
if "candidates" not in st.session_state:
    st.session_state["candidates"] = []
if "recording_in_progress" not in st.session_state:
    st.session_state["recording_in_progress"] = False
if "emotion_data" not in st.session_state:
    st.session_state["emotion_data"] = []


# Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate(
        r"C:\Users\aadik\OneDrive\Documents\Desktop\finalhari.py\codewHari.py\assessai-44afc-firebase-adminsdk-fbsvc-4e13d0986d.json"
    )  # Replace with your Firebase credentials path
    firebase_admin.initialize_app(cred)
db = firestore.client()


# Initialize Cohere
COHERE_API_KEY = st.secrets["cohere"]["api_key"]
co = cohere.Client(COHERE_API_KEY)


# Google Sheets Integration
def setup_google_sheets_api():
    # Set up Google Sheets API connection using service account
    credentials = service_account.Credentials.from_service_account_file(
        r"C:\Users\aadik\OneDrive\Documents\Desktop\finalhari.py\codewHari.py\moonlit-haven-452014-i4-248bff09d735.json",  # Replace with your file path
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    service = build('sheets', 'v4', credentials=credentials)
    return service

def fetch_sheet_data(service, spreadsheet_id):
    """Fetch data from Google Sheets"""
    try:
        # Get the first sheet
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_name = sheet_metadata['sheets'][0]['properties']['title']
        
        # Get all values from the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_name
        ).execute()
        
        rows = result.get('values', [])
        
        if not rows:
            st.error("No data found in the spreadsheet.")
            return []
            
        # Assume first row is the header
        headers = rows[0]
        
        # Create a list of candidates
        candidates = []
        for row in rows[1:]:  # Skip header row
            # Extend row with empty strings if it's shorter than headers
            row_data = row + [''] * (len(headers) - len(row))
            
            # Find the exact indices for each column
            name_idx = headers.index("Name") if "Name" in headers else -1
            email_idx = headers.index("Email") if "Email" in headers else -1
            edu_idx = -1
            for i, h in enumerate(headers):
                if "Education" in h:
                    edu_idx = i
                    break
            role_idx = -1
            for i, h in enumerate(headers):
                if "Job role" in h:
                    role_idx = i
                    break
            skills_idx = -1
            for i, h in enumerate(headers):
                if "Skills" in h:
                    skills_idx = i
                    break
            exp_idx = -1
            for i, h in enumerate(headers):
                if "Years" in h and "experience" in h:
                    exp_idx = i
                    break
            
            # Create profile using found indices
            profile_data = {
                "name": row_data[name_idx] if name_idx >= 0 and name_idx < len(row_data) else "Unknown",
                "email": row_data[email_idx] if email_idx >= 0 and email_idx < len(row_data) else "Unknown",
                "education": row_data[edu_idx] if edu_idx >= 0 and edu_idx < len(row_data) else "Unknown",
                "role": row_data[role_idx] if role_idx >= 0 and role_idx < len(row_data) else "Unknown",
                "skills": row_data[skills_idx] if skills_idx >= 0 and skills_idx < len(row_data) else "Unknown",
                "experience": row_data[exp_idx] if exp_idx >= 0 and exp_idx < len(row_data) else "Unknown"
            }
            
            # Only add candidates with a name
            if profile_data["name"] and profile_data["name"] != "Unknown":
                # Store in Firebase
                db.collection("candidates").document(profile_data["name"]).set(profile_data)
                candidates.append(profile_data)
        
        return candidates
    except Exception as e:
        st.error(f"Error fetching spreadsheet data: {str(e)}")
        st.write(f"Debug - Exception details: {str(e)}")
        return []

def extract_spreadsheet_id(sheet_url):
    """Extract the spreadsheet ID from a Google Sheets URL"""
    import re
    
    pattern = r"/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, sheet_url)
    if match:
        return match.group(1)
    return None

# Function to create emotion timeline visualizations
def create_emotion_timeline(emotion_data):
    """Create timeline visualizations for stress levels and emotions"""
    try:
        # Convert to DataFrame
        df = pd.DataFrame(emotion_data)
        
        # Add stress value based on stress level
        df['stress_value'] = df['stress_level'].map({'Low': 1, 'Medium': 2, 'High': 3})
        
        # Create a timestamp that's readable
        df['readable_time'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S'))
        
        # Create stress level timeline
        stress_fig = go.Figure()
        stress_fig.add_trace(go.Scatter(
            x=df['readable_time'],
            y=df['stress_value'],
            mode='lines+markers',
            name='Stress Level',
            line=dict(color='red', width=2),
            marker=dict(size=8, color='darkred')
        ))
        
        stress_fig.update_layout(
            title='Candidate Stress Level Timeline',
            xaxis_title='Interview Time',
            yaxis_title='Stress Level',
            yaxis=dict(
                tickvals=[1, 2, 3],
                ticktext=['Low', 'Medium', 'High']
            ),
            height=400,  # Set the height for better spacing
            margin=dict(l=50, r=50, t=80, b=50)  # Add margins for better spacing
        )
        
        # Create emotion breakdown timeline if emotions data is available
        emotion_fig = None
        emotion_columns = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        
        if any(col in df.columns for col in emotion_columns):
            # Filter only existing emotion columns
            available_emotions = [col for col in emotion_columns if col in df.columns]
            
            if available_emotions:
                emotion_fig = go.Figure()
                for emotion in available_emotions:
                    if emotion in df.columns:
                        emotion_fig.add_trace(go.Scatter(
                            x=df['readable_time'],
                            y=df[emotion],
                            mode='lines',
                            name=emotion.capitalize()
                        ))
                
                emotion_fig.update_layout(
                    title='Emotion Intensity Timeline',
                    xaxis_title='Interview Time',
                    yaxis_title='Intensity',
                    yaxis=dict(range=[0, 1]),
                    height=400,  # Set the height for better spacing
                    margin=dict(l=50, r=50, t=80, b=50)  # Add margins for better spacing
                )
        
        return stress_fig, emotion_fig, df
    except Exception as e:
        st.error(f"Error creating timeline: {str(e)}")
        return go.Figure(), None, pd.DataFrame()

# Stress Level Detection functions
def detect_stress(image):
    try:
        img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        result = DeepFace.analyze(img_bgr, actions=['emotion'], enforce_detection=False)

        if isinstance(result, list) and len(result) > 0:
            emotion_data = result[0].get('emotion', {})
            dominant_emotion = result[0].get('dominant_emotion', 'neutral')
        else:
            emotion_data = {}
            dominant_emotion = 'neutral'

        # Emotions
        if dominant_emotion in ['fear', 'sad', 'angry']:
            stress_level = "High"
            stress_value = 3
        elif dominant_emotion in ['neutral', 'surprise']:
            stress_level = "Medium"
            stress_value = 2
        else:
            stress_level = "Low"
            stress_value = 1

        # Create analysis data object
        analysis = {
            "timestamp": int(time.time()),
            "emotion": dominant_emotion,
            "stress_level": stress_level,
            "stress_value": stress_value
        }
        
        # Add individual emotion scores if available
        if emotion_data:
            for emotion, score in emotion_data.items():
                analysis[emotion] = score / 100  # Normalize to 0-1 range
        
        return analysis, img_bgr
    except Exception as e:
        return {"timestamp": int(time.time()), "emotion": "unknown", "stress_level": "Unknown", "stress_value": 0, "error": str(e)}, None

def capture_and_analyze_stress():
    # Capture screenshot
    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)
    screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
    
    # Convert to grayscale for processing
    gray = cv2.cvtColor(screenshot_rgb, cv2.COLOR_RGB2GRAY)
    
    # Apply blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Edge detection with lower threshold to capture more potential frames
    edges = cv2.Canny(blurred, 30, 100)
    
    # Dilate edges to connect nearby edges
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    
    # Find contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Look for rectangular shapes that are likely to be the video frame
    video_frame = None
    max_area = 0
    min_area_threshold = 50000  # Minimum area to be considered a video frame
    target_aspect_ratio = 16/9  # Common aspect ratio for video
    
    for cnt in contours:
        # Approximate the contour to reduce the number of points
        epsilon = 0.02 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        
        # Check if it's a rectangle (4 points)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            area = w * h
            aspect_ratio = w / h if h > 0 else 0
            
            # Check if it's large enough and has a reasonable aspect ratio
            if (area > min_area_threshold and 
                area > max_area and 
                abs(aspect_ratio - target_aspect_ratio) < 0.5):  # Allow some deviation from perfect aspect ratio
                max_area = area
                video_frame = (x, y, w, h)
    
    # Crop the video frame if detected
    if video_frame:
        x, y, w, h = video_frame
        # Add a small margin (5%) to ensure we don't cut off any faces
        margin_x = int(w * 0.05)
        margin_y = int(h * 0.05)
        
        # Ensure margins don't go out of bounds
        x_start = max(0, x - margin_x)
        y_start = max(0, y - margin_y)
        x_end = min(screenshot_rgb.shape[1], x + w + margin_x)
        y_end = min(screenshot_rgb.shape[0], y + h + margin_y)
        
        # Crop the frame with margins
        cropped_frame = screenshot_rgb[y_start:y_end, x_start:x_end]
        
        # Analyze the cropped frame
        analysis, processed_image = detect_stress(cropped_frame)
    else:
        # If Digital Samba frame not detected, use a fallback method
        # Look for video frame area (dark background with lighter content in the center)
        st.warning("Video conference frame not detected using primary method, trying alternate approach...")
        
        # Try to crop the center portion of the screen where Digital Samba usually displays the video
        h, w = screenshot_rgb.shape[:2]
        center_x, center_y = w // 2, h // 2
        crop_w, crop_h = int(w * 0.6), int(h * 0.6)  # Take 60% of screen
        
        x1 = center_x - crop_w // 2
        y1 = center_y - crop_h // 2
        x2 = x1 + crop_w
        y2 = y1 + crop_h
        
        fallback_crop = screenshot_rgb[y1:y2, x1:x2]
        analysis, processed_image = detect_stress(fallback_crop)
    
    # Save the image with the analysis
    if processed_image is not None:
        # Encode the image to base64 for storage
        _, buffer = cv2.imencode('.jpg', processed_image)
        analysis["image"] = base64.b64encode(buffer).decode("utf-8")
    
    return analysis

def generate_interview_questions(profile):
    if not profile:
        return ["Please select a candidate profile first."]
    prompt = f"Generate five interview questions for a candidate applying as {profile.get('role', 'N/A')} with {profile.get('experience', 'N/A')} years of experience and skills in {profile.get('skills', 'N/A')}."
    response = co.generate(
        model="command",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )
    questions = response.generations[0].text.strip().split("\n")
    questions = [q.strip() for q in questions if q.strip()]
    return questions[:5]

# Navigation functions
def navigate_to_main():
    st.session_state["page"] = "main"

def navigate_to_analysis():
    st.session_state["page"] = "analysis"

# App Layout
st.sidebar.title("Navigation")
if st.sidebar.button("Interview Dashboard"):
    navigate_to_main()
if st.sidebar.button("Video Analysis"):
    navigate_to_analysis()

# Sidebar: Common elements for candidate selection
st.sidebar.header("Candidate Profiles from Google Sheets")

# Google Sheets URL input
sheet_url = st.sidebar.text_input(
    "Google Sheets URL", 
    value="https://docs.google.com/spreadsheets/d/1ePTP7QhzLZvf5YJI2qTX78wOeSupfmagBzOZ_MvpywQ/edit?usp=sharing",
    help="URL of the Google Sheet containing candidate information"
)

if st.sidebar.button("Sync Candidate Profiles"):
    if sheet_url:
        with st.spinner("Syncing profiles from Google Sheets..."):
            try:
                # Extract the spreadsheet ID from the URL
                spreadsheet_id = extract_spreadsheet_id(sheet_url)
                
                if not spreadsheet_id:
                    st.sidebar.error("Invalid Google Sheets URL. Please check and try again.")
                else:
                    service = setup_google_sheets_api()
                    candidates = fetch_sheet_data(service, spreadsheet_id)
                    
                    if candidates:
                        st.sidebar.success(f"Successfully synced {len(candidates)} candidate profiles!")
                        # Store the candidates in session state for display
                        st.session_state["candidates"] = candidates
                    else:
                        st.sidebar.warning("No candidate profiles found in the spreadsheet.")
            except Exception as e:
                st.sidebar.error(f"Error syncing profiles: {str(e)}")
    else:
        st.sidebar.warning("Please enter a Google Sheets URL")

# Display list of candidates
st.sidebar.subheader("Available Candidates")
if st.session_state["candidates"]:
    
    candidate_names = [candidate["name"] for candidate in st.session_state["candidates"] if candidate["name"] != "Unknown"]
    
    if candidate_names:
        selected_candidate = st.sidebar.selectbox(
            "Select a candidate",
            options=candidate_names,
            index=0
        )
        
        selected_profile = next((c for c in st.session_state["candidates"] if c["name"] == selected_candidate), None)
        
        if selected_profile:
            st.session_state["current_profile"] = selected_profile
        
            # Display the selected candidate profile
            st.sidebar.subheader("Selected Candidate Profile")
            st.sidebar.write(f"**Name:** {selected_profile.get('name', 'N/A')}")
            st.sidebar.write(f"**Email:** {selected_profile.get('email', 'N/A')}")
            st.sidebar.write(f"**Role:** {selected_profile.get('role', 'N/A')}")
            st.sidebar.write(f"**Education:** {selected_profile.get('education', 'N/A')}")
            st.sidebar.write(f"**Skills:** {selected_profile.get('skills', 'N/A')}")
            st.sidebar.write(f"**Experience:** {selected_profile.get('experience', 'N/A')} years")
    else:
        st.sidebar.info("No valid candidate names found in the data. Please check your Google Sheet format.")
else:
    st.sidebar.info("No candidates synced yet. Click 'Sync Candidate Profiles' to fetch data from Google Sheets.")

# Main Page Content
if st.session_state["page"] == "main":
    st.title("Recruiter Dashboard - AI Interview Assistant")
    
    # AI Interview Chatbot
    st.subheader("AI Interview Chatbot")
    
    if st.button("Generate Interview Questions"):
        if "current_profile" in st.session_state:
            st.session_state["questions"] = generate_interview_questions(st.session_state["current_profile"])
            st.success("Generated interview questions!")
        else:
            st.warning("No candidate selected. Please sync and select a candidate first.")
    
    if "questions" in st.session_state:
        st.write("### Interview Questions:")
        for i, question in enumerate(st.session_state["questions"], 1):
            st.write(f"{i}. {question}")
    
    # Digital Samba Video Conferencing Integration
    st.subheader("Video Interview Room")
    
    # Digital Samba meeting room link
    meeting_link = st.text_input("Enter Digital Samba Meeting Room Link:")
    
    # Embed the meeting
    if meeting_link:
        st.markdown(
            f"""
            <iframe
                src="{meeting_link}"
                width="100%"
                height="600px"
                allow="camera; microphone; fullscreen; display-capture"
                style="border: none;"
            ></iframe>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("Please enter a valid Digital Samba meeting room link to start the video interview.")
    
    # Stress Level Detection
    st.subheader("Automated Stress Level Detection")

    # Button to start analysis
    if st.button("Start Automated Stress Level Analysis"):
        if "current_profile" not in st.session_state:
            st.warning("Please select a candidate first.")
        else:
            # Setup
            st.write("Starting automated stress level analysis...")
            st.session_state["recording_in_progress"] = True
            st.session_state["emotion_data"] = []
            
            # Create a progress bar
            progress_bar = st.progress(0)
            
            # Create a container for the stop button
            stop_container = st.container()
            stop_button_pressed = stop_container.button("Stop Analysis")
            
            # Create a container for all analysis results
            analysis_container = st.container()
            
            # Number of samples to take
            num_samples = 5
            
            try:
                for i in range(num_samples):
                    # Check if stop button was pressed
                    if stop_button_pressed or not st.session_state.get("recording_in_progress", True):
                        st.warning("Analysis stopped by user")
                        break
                        
                    # Update progress
                    progress_bar.progress((i + 1) / num_samples)
                    
                    # Capture and analyze
                    analysis = capture_and_analyze_stress()
                    
                    # Store data
                    if analysis.get("emotion") != "Error":
                        st.session_state["emotion_data"].append(analysis)
                        
                        # Display current result in the container
                        with analysis_container:
                            # Create a new row for each analysis
                            cols = st.columns([2, 3])
                            
                            # Column 1: Display image
                            with cols[0]:
                                if "image" in analysis:
                                    try:
                                        image_data = base64.b64decode(analysis["image"])
                                        image_array = np.frombuffer(image_data, np.uint8)
                                        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                                        if image is not None:
                                            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                                            # FIXED LINE - replaced use_column_width with use_container_width
                                            st.image(image, caption=f"Analysis {i+1}", use_container_width=True)
                                        else:
                                            st.warning("Could not decode image")
                                    except Exception as e:
                                        st.error(f"Error displaying image: {str(e)}")
                                else:
                                    st.warning("No image captured")
                            
                            # Column 2: Display analysis data
                            with cols[1]:
                                st.write(f"### Analysis {i+1}")
                                st.write(f"**Emotion:** {analysis['emotion']}")
                                st.write(f"**Stress:** {analysis['stress_level']}")
                                
                                # Show appropriate message based on stress level
                                if analysis['stress_level'] == "High":
                                    st.error("High stress")
                                elif analysis['stress_level'] == "Medium":
                                    st.warning("Medium stress")
                                else:
                                    st.success("Relaxed")
                    
                        # Save to Firebase
                        try:
                            selected_name = st.session_state["current_profile"]["name"]
                            db.collection("stress_analysis").document(selected_name).collection("timeline").document(str(analysis["timestamp"])).set(analysis)
                        except Exception as e:
                            st.error(f"Failed to save to database: {str(e)}")
                    
                    else:
                        with analysis_container:
                            st.error(f"Capture {i+1} failed: {analysis.get('error', 'Unknown error')}")
                    
                    # Wait before next capture
                    time.sleep(3)  # Reduced from 10 seconds for better user experience
                
                if i == num_samples - 1:  # Successfully completed all samples
                    st.success("Analysis complete! Go to Video Analysis page to view detailed results.")
                    
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
            finally:
                # Reset recording flag
                st.session_state["recording_in_progress"] = False
                # Clear progress bar
                progress_bar.empty()

# Analysis Page Content
elif st.session_state["page"] == "analysis":
    st.title("Video Analysis Dashboard")
    
    if not "emotion_data" in st.session_state or len(st.session_state["emotion_data"]) == 0:
        st.info("No interview data available. Please run an interview analysis first.")
        if st.button("Return to Interview Dashboard"):
            navigate_to_main()
    else:
        # Create timeline visualizations
        stress_fig, emotion_fig, timeline_df = create_emotion_timeline(st.session_state["emotion_data"])
        
        # Display the timeline visualization with spacing
        st.subheader("Stress Level Timeline")
        st.plotly_chart(stress_fig, use_container_width=True)
        
        st.markdown("---")
        
        if emotion_fig:
            st.subheader("Emotion Intensity Timeline")
            st.plotly_chart(emotion_fig, use_container_width=True)
            
            st.markdown("---")
        
        # Create a slider to navigate through the timeline
        if 'timestamp' in timeline_df.columns and len(timeline_df) > 1:
            st.subheader("Interview Timeline Navigator")
            
            # Convert Unix timestamps to IST
            def unix_to_ist(unix_timestamp):
                utc_time = datetime.fromtimestamp(unix_timestamp)
                ist_timezone = pytz.timezone('Asia/Kolkata')
                ist_time = utc_time.astimezone(ist_timezone)
                return ist_time

            min_time = int(timeline_df['timestamp'].min())
            max_time = int(timeline_df['timestamp'].max())
            
            # Get IST times for display
            min_time_ist = unix_to_ist(min_time)
            max_time_ist = unix_to_ist(max_time)

            selected_time = st.slider(
                "Select a moment in the interview",
                min_value=min_time,
                max_value=max_time,
                value=min_time
            )
            
            # Find the closest data point
            closest_point = timeline_df.iloc[(timeline_df['timestamp'] - selected_time).abs().argsort()[0]]
            
            # Display the data for this point with IST time
            selected_time_ist = unix_to_ist(selected_time)
            st.subheader(f"Analysis at {selected_time_ist.strftime('%H:%M:%S IST')}")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(min_time_ist.strftime('%H:%M:%S IST'))
            with col2:
                st.write(max_time_ist.strftime('%H:%M:%S IST'))
            
            with col1:
                # Display the snapshot image if available with proper error handling
                if "image" in closest_point and closest_point["image"]:
                    try:
                        image_data = base64.b64decode(closest_point["image"])
                        image_array = np.frombuffer(image_data, np.uint8)
                        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                        if image is not None:
                            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                            # FIXED LINE - replaced use_column_width with use_container_width
                            st.image(image, caption="Candidate at this moment", use_container_width=True)
                        else:
                            st.warning("Could not decode image data")
                    except Exception as e:
                        st.error(f"Error displaying image: {str(e)}")
                else:
                    st.info("No image available for this moment")
            
            with col2:
                # Display emotion metrics with proper error handling
                if 'emotion' in closest_point:
                    st.write(f"### Dominant Emotion: {closest_point['emotion'].capitalize()}")
                else:
                    st.write("### Dominant Emotion: Unknown")
                    
                if 'stress_level' in closest_point:
                    st.write(f"### Stress Level: {closest_point['stress_level']}")
                else:
                    st.write("### Stress Level: Unknown")
                
                # Create a gauge chart for stress level
                if 'stress_value' in closest_point:
                    stress_gauge = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = closest_point['stress_value'],
                        title = {'text': "Stress Level"},
                        gauge = {
                            'axis': {'range': [0, 3], 'tickvals': [1, 2, 3], 'ticktext': ['Low', 'Medium', 'High']},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 1], 'color': "green"},
                                {'range': [1, 2], 'color': "yellow"},
                                {'range': [2, 3], 'color': "red"}
                            ]
                        }
                    ))
                    stress_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(stress_gauge, use_container_width=True)
                else:
                    st.warning("Stress value data not available")
            
            st.markdown("---")
            
            # Display emotions breakdown with proper error handling
            st.subheader("Emotion Breakdown")
            emotions_to_display = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
            
            # Check if emotion data exists
            has_emotion_data = any(emotion in closest_point for emotion in emotions_to_display)
            
            if has_emotion_data:
                emotion_values = {e: float(closest_point.get(e, 0)) for e in emotions_to_display if e in closest_point}
                
                if emotion_values:
                    emotion_pie = px.pie(
                        values=list(emotion_values.values()),
                        names=list(emotion_values.keys()),
                        title='Emotion Distribution',
                        color_discrete_sequence=px.colors.sequential.Plasma
                    )
                    emotion_pie.update_layout(height=400, margin=dict(l=20, r=20, t=80, b=20))
                    st.plotly_chart(emotion_pie, use_container_width=True)
                else:
                    st.info("No detailed emotion data available for this moment")
            else:
                st.info("No emotion breakdown data available")
            
            st.markdown("---")
            
            # Notes and analysis section with proper error handling
            st.subheader("Recruiter Notes")
            
            # Load any existing notes
            if "current_profile" in st.session_state:
                try:
                    selected_name = st.session_state["current_profile"]["name"]
                    doc_ref = db.collection("stress_analysis").document(selected_name).collection("notes").document(str(closest_point['timestamp']))
                    doc = doc_ref.get()
                    existing_notes = doc.to_dict().get('text', '') if doc.exists else ''
                    
                    # Allow recruiters to add notes at this timestamp
                    notes = st.text_area("Add notes about this moment:", value=existing_notes, height=150)
                    
                    if st.button("Save Notes"):
                                # Convert numpy.int64 to standard Python int
                                timestamp_py_int = int(closest_point['timestamp'])
                                doc_ref.set({'text': notes, 'timestamp': timestamp_py_int})
                                st.success("Notes saved successfully!")
                except Exception as e:
                                st.error(f"Error loading/saving notes: {str(e)}")
            else:
                                st.warning("No candidate selected. Please select a candidate to add notes.")

            st.markdown("---")
            
            # Export interview analysis report
            st.subheader("Export Interview Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Generate Summary Report"):
                    try:
                        # Create a summary of the interview
                        # Convert NumPy types to Python native types
                        summary = {
                            "candidate_name": st.session_state["current_profile"]["name"],
                            "interview_date": datetime.fromtimestamp(timeline_df['timestamp'].min()).strftime('%Y-%m-%d'),
                            "interview_duration": f"{float((timeline_df['timestamp'].max() - timeline_df['timestamp'].min()) / 60):.1f} minutes",
                            "avg_stress_level": float(timeline_df['stress_value'].mean()),
                            "max_stress_level": int(timeline_df['stress_value'].max()),
                            "dominant_emotion": str(timeline_df['emotion'].mode()[0]) if 'emotion' in timeline_df.columns and not timeline_df['emotion'].empty else 'Unknown',
                            "stress_peaks": int(len(timeline_df[timeline_df['stress_value'] == 3])),
                            "relaxed_moments": int(len(timeline_df[timeline_df['stress_value'] == 1]))
                        }
                        
                        # Store summary in Firebase
                        db.collection("stress_analysis").document(st.session_state["current_profile"]["name"]).collection("reports").document("summary").set(summary)
                        
                        # Create PDF using ReportLab
                        from reportlab.lib import colors
                        from reportlab.lib.pagesizes import letter
                        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                        from reportlab.lib.styles import getSampleStyleSheet
                        import tempfile
                        import base64
                        
                        # Create a temporary file for the PDF
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            pdf_path = tmp_file.name
                        
                        # Create the PDF
                        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
                        styles = getSampleStyleSheet()
                        
                        # Build the content
                        content = []
                        
                        # Add title
                        title_style = styles['Heading1']
                        content.append(Paragraph(f"Interview Summary Report", title_style))
                        content.append(Spacer(1, 12))
                        
                        # Add candidate info section
                        content.append(Paragraph("Candidate Information", styles['Heading2']))
                        content.append(Spacer(1, 6))
                        
                        # Create a table for candidate information
                        candidate_data = [
                            ["Candidate Name:", summary["candidate_name"]],
                            ["Interview Date:", summary["interview_date"]],
                            ["Interview Duration:", summary["interview_duration"]]
                        ]
                        
                        candidate_table = Table(candidate_data, colWidths=[150, 300])
                        candidate_table.setStyle(TableStyle([
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 10),
                            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ]))
                        content.append(candidate_table)
                        content.append(Spacer(1, 12))
                        
                        # Add stress analysis section
                        content.append(Paragraph("Stress Analysis", styles['Heading2']))
                        content.append(Spacer(1, 6))
                        
                        # Create a table for stress analysis
                        stress_data = [
                            ["Average Stress Level:", f"{summary['avg_stress_level']:.2f}"],
                            ["Maximum Stress Level:", str(summary['max_stress_level'])],
                            ["Dominant Emotion:", summary["dominant_emotion"]],
                            ["High Stress Moments:", str(summary["stress_peaks"])],
                            ["Relaxed Moments:", str(summary["relaxed_moments"])]
                        ]
                        
                        stress_table = Table(stress_data, colWidths=[150, 300])
                        stress_table.setStyle(TableStyle([
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 10),
                            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ]))
                        content.append(stress_table)
                        
                        # Add analysis note
                        content.append(Spacer(1, 24))
                        note_style = styles['Normal']
                        
                        # Create a personalized analysis based on the data
                        if summary['avg_stress_level'] > 2.5:
                            analysis_note = f"{summary['candidate_name']} exhibited high stress levels throughout the interview. Consider providing more preparation or a more comfortable interview environment in the future."
                        elif summary['avg_stress_level'] > 1.5:
                            analysis_note = f"{summary['candidate_name']} showed moderate stress levels with some peaks during the interview. Overall handling was adequate."
                        else:
                            analysis_note = f"{summary['candidate_name']} maintained low stress levels throughout the interview, indicating good preparation and comfort with the process."
                            
                        content.append(Paragraph("Analysis Note:", styles['Heading3']))
                        content.append(Paragraph(analysis_note, note_style))
                        
                        # Add timestamp for the report
                        content.append(Spacer(1, 30))
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        content.append(Paragraph(f"Report generated on: {timestamp}", styles['Italic']))
                        
                        # Build the PDF
                        doc.build(content)
                        
                        # Create a download link for the PDF
                        with open(pdf_path, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                            
                        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                        
                        # Generate download link
                        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{summary["candidate_name"]}_interview_summary.pdf">Download PDF Report</a>'
                        
                        # Display a success message and download link
                        st.success("Summary report generated and saved!")
                        st.markdown(href, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Error generating summary report: {str(e)}")
                        import traceback
                        st.error(traceback.format_exc())
                