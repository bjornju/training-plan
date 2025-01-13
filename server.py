from flask import Flask, send_file, send_from_directory, jsonify
import re
from pathlib import Path
import os

app = Flask(__name__)

def parse_training_week(week_content):
    days = []
    current_day = None
    
    # Split into days
    day_pattern = r'\*\*(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), ([A-Za-z]+ \d+)\*\*\n(.*?)(?=\*\*|$)'
    day_matches = re.finditer(day_pattern, week_content, re.DOTALL)
    
    for match in day_matches:
        day_name, date, content = match.groups()
        
        # Extract caloric target and weight
        caloric_match = re.search(r"TODAY'S CALORIC TARGET: ([\d,]+)", content)
        weight_match = re.search(r"Current weight: ([\d.]+)", content)
        
        # Extract sessions
        sessions = []
        session_pattern = r'- ([^*\n]+?)(?=\n\s*[*-]|\n\n|$)'
        session_matches = re.finditer(session_pattern, content)
        
        for s_match in session_matches:
            session_name = s_match.group(1).strip()
            if session_name and not session_name.startswith("Run streak"):  # Skip run streak entries
                session_details = {}
                session_details['name'] = session_name
                
                # Try to extract duration and location if available
                duration_match = re.search(r'Duration: (\d+)', content[s_match.start():])
                location_match = re.search(r'Location: ([^\n]+)', content[s_match.start():])
                
                if duration_match:
                    session_details['duration'] = duration_match.group(1)
                if location_match:
                    session_details['location'] = location_match.group(1).strip()
                
                sessions.append(session_details)
        
        day_data = {
            'day': day_name,
            'date': date,
            'calories': int(caloric_match.group(1).replace(',', '')) if caloric_match else None,
            'weight': float(weight_match.group(1)) if weight_match else None,
            'sessions': sessions
        }
        days.append(day_data)
    
    return days

def parse_training_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    weeks = []
    # Extract week number and title separately
    week_pattern = r'## (?:Week )?(\d+)[^\n]*\n(.*?)(?=## (?:Week )?|\Z)'
    week_matches = re.finditer(week_pattern, content, re.DOTALL)
    
    for match in week_matches:
        week_num = match.group(1)
        week_content = match.group(2)
        
        # Extract the full title from the original content
        title_pattern = fr'## (?:Week )?{week_num}([^\n]*)'
        title_match = re.search(title_pattern, match.group(0))
        full_title = f"{week_num}{title_match.group(1) if title_match else ''}"
        
        week_data = {
            'week_number': int(week_num),
            'title': full_title,  # Use the full title instead of just the number
            'days': parse_training_week(week_content)
        }
        
        # Calculate week metrics
        weights = [day['weight'] for day in week_data['days'] if day['weight']]
        total_sessions = sum(len(day['sessions']) for day in week_data['days'])
        
        # Get the most recent daily caloric target
        latest_calories = next((day['calories'] for day in reversed(week_data['days']) if day['calories']), 0)
        
        week_data['metrics'] = {
            'daily_calories': latest_calories,
            'avg_weight': sum(weights) / len(weights) if weights else 0,
            'total_sessions': total_sessions
        }
        
        weeks.append(week_data)
    
    return weeks

@app.route('/')
def home():
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@app.route('/api/training/<month>')
def get_training_data(month):
    try:
        file_path = Path(f'{month}_2025.md')
        if not file_path.exists():
            return jsonify({'error': f'File not found: {file_path}'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content, 200, {'Content-Type': 'text/markdown'}
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8080, debug=True)
