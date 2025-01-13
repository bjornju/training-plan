import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import frontmatter
import re
from datetime import datetime, timedelta
import random

# Set page config
st.set_page_config(
    page_title="Training Plan Viewer",
    page_icon="🏃",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stApp {
        background-color: #f5f5f5;
    }
    .training-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #1f77b4;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    .quote-card {
        background-color: #2ecc71;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        font-style: italic;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Motivational quotes
QUOTES = [
    "The only bad workout is the one that didn't happen.",
    "Your body can stand almost anything. It's your mind you have to convince.",
    "The difference between try and triumph is just a little umph!",
    "Success is walking from failure to failure with no loss of enthusiasm.",
    "The hard days are the best because that's when champions are made.",
    "Don't count the days, make the days count.",
    "The only person you are destined to become is the person you decide to be.",
    "Believe you can and you're halfway there.",
]

def parse_training_file(file_path):
    """Parse markdown training file and extract weekly data."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract weeks using regex, but preserve the week header
    week_pattern = r'## Week (\d+)'
    weeks = re.split(week_pattern, content)[1:]  # Skip the header
    parsed_weeks = []
    
    for i in range(0, len(weeks), 2):  # Step by 2 since we have number and content
        week_num = weeks[i]
        week_content = weeks[i + 1] if i + 1 < len(weeks) else ""
        days = re.split(r'\*\*[A-Za-z]+, [A-Za-z]+ \d+\*\*', week_content)[1:]
        week_data = []
        
        for day in days:
            # Extract key information
            caloric_match = re.search(r"TODAY'S CALORIC TARGET: (\d+)", day)
            weight_match = re.search(r"Current weight: ([\d.]+)", day)
            sessions = re.findall(r'- (.+?)(?=\n\n|$)', day, re.DOTALL)
            
            day_data = {
                'caloric_target': int(caloric_match.group(1)) if caloric_match else None,
                'weight': float(weight_match.group(1)) if weight_match else None,
                'sessions': [s.split('\n')[0].strip() for s in sessions if s.strip()]
            }
            week_data.append(day_data)
        
        parsed_weeks.append((week_num, week_data))
    
    return parsed_weeks

def create_weekly_metrics(week_data):
    """Create metrics visualization for the week."""
    calories = [day['caloric_target'] for day in week_data if day['caloric_target']]
    weights = [day['weight'] for day in week_data if day['weight']]
    
    metrics = {
        'avg_calories': sum(calories) / len(calories) if calories else 0,
        'avg_weight': sum(weights) / len(weights) if weights else 0,
        'total_sessions': sum(len(day['sessions']) for day in week_data)
    }
    
    return metrics

def display_week(week_data, week_number):
    """Display a single week's training data."""
    st.markdown(f"### {week_number}")  # Remove the extra "Week" here
    
    metrics = create_weekly_metrics(week_data)
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Average Daily Calories</h4>
                <h2>{int(metrics['avg_calories'])}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Average Weight</h4>
                <h2>{metrics['avg_weight']:.2f} kg</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Total Sessions</h4>
                <h2>{metrics['total_sessions']}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Display daily training cards
    for i, day in enumerate(week_data):
        with st.expander(f"Day {i+1} - {day['caloric_target']} kcal"):
            st.markdown(
                f"""
                <div class="training-card">
                    <h4>Weight: {day['weight']} kg</h4>
                    <h4>Training Sessions:</h4>
                    <ul>
                        {''.join(f'<li>{session}</li>' for session in day['sessions'])}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )

def main():
    st.title("🏃 Training Plan Viewer")
    
    # Display random motivational quote
    st.markdown(
        f"""
        <div class="quote-card">
            "{random.choice(QUOTES)}"
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # File selection
    training_files = list(Path('.').glob('*.md'))
    selected_file = st.selectbox(
        "Select Training Plan",
        training_files,
        format_func=lambda x: x.stem.capitalize()
    )
    
    if selected_file:
        weeks = parse_training_file(selected_file)
        
        # Week selection
        total_weeks = len(weeks)
        week_range = st.slider(
            "Select Weeks",
            1, total_weeks,
            (1, min(2, total_weeks)),
            1
        )
        
        # Display selected weeks
        for week_num in range(week_range[0]-1, week_range[1]):
            display_week(weeks[week_num][1], weeks[week_num][0])
            st.markdown("---")

if __name__ == "__main__":
    main()
