from flask import Flask, send_file, send_from_directory, jsonify
import re
import json
from pathlib import Path
import os

app = Flask(__name__)

def parse_session_structure(content):
    structure = []
    current_section = None
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith(('1.', '2.', '3.')):  # Main section
            if current_section:
                structure.append(current_section)
            current_section = {
                'name': line.split(':', 1)[1].strip() if ':' in line else line[3:].strip(),
                'duration': line.split('(')[1].split(')')[0] if '(' in line else None,
                'items': []
            }
        elif line.startswith('-') and current_section:  # Sub-items
            current_section['items'].append(line[1:].strip())
            
    if current_section:
        structure.append(current_section)
        
    return structure

def parse_training_week(week_content):
    days = []
    
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
        lines = [line.rstrip() for line in content.split('\n')]
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if line.startswith('- '):  # Main session
                session = {'name': line[2:].strip(), 'details': [], 'structure': []}
                i += 1
                
                # Collect session details until next main session or end
                while i < len(lines):
                    line = lines[i]
                    
                    # Skip empty lines
                    if not line.strip():
                        i += 1
                        continue
                    
                    # Break if we hit next main session
                    if line.startswith('- ') and not line.startswith('       -'):
                        break
                    
                    # Parse session details
                    if line.startswith('  * '):
                        detail = line[4:].strip()
                        if 'Duration:' in detail:
                            duration_match = re.search(r'Duration: ~?(\d+)', detail)
                            if duration_match:
                                session['duration'] = duration_match.group(1)
                        elif 'Session structure:' in detail:
                            i += 1
                            # Parse structure sections
                            current_section = None
                            while i < len(lines):
                                line = lines[i]
                                
                                # Break if we hit next main session
                                if line.startswith('- ') and not line.startswith('       -'):
                                    break
                                
                                # Parse section header
                                if line.lstrip().startswith(('1.', '2.', '3.')):
                                    section_match = re.match(r'\s*\d+\.\s*(.*?)\s*\((\d+)\s*min\):', line)
                                    if section_match:
                                        name, duration = section_match.groups()
                                        current_section = {
                                            'name': name.strip(),
                                            'duration': duration,
                                            'items': []
                                        }
                                        session['structure'].append(current_section)
                                
                                # Parse section items
                                elif line.startswith('       -') and current_section:
                                    item = line[9:].strip()
                                    current_section['items'].append(item)
                                
                                i += 1
                                if i >= len(lines):
                                    break
                            
                            # Back up one to not skip next session
                            i -= 1
                        else:
                            session['details'].append(detail)
                    i += 1
                
                sessions.append(session)
                continue
            i += 1
        
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

def calculate_progress(weeks):
    from datetime import datetime
    current_time = datetime.strptime('2025-01-13T15:24:00+01:00', '%Y-%m-%dT%H:%M:%S%z')
    
    # Initialize counters for each session type
    session_stats = {}
    starting_weight = None
    current_weight = None
    
    for week in weeks:
        for day in week['days']:
            # Parse the date
            date_str = f"{day['date']} 2025"  # Add year since it's not in the original string
            day_date = datetime.strptime(date_str, '%b %d %Y')
            
            # Only process past days
            if day_date.date() <= current_time.date():
                # Track weight progress
                if starting_weight is None and day['weight']:
                    starting_weight = day['weight']
                if day['weight']:
                    current_weight = day['weight']
                
                # Process sessions
                for session in day['sessions']:
                    session_type = session['name'].split(':')[-1].strip() if ':' in session['name'] else session['name']
                    
                    # Initialize stats for new session type
                    if session_type not in session_stats:
                        session_stats[session_type] = {
                            'total': 0,
                            'completed': 0
                        }
                    
                    session_stats[session_type]['total'] += 1
                    # Consider a session completed if it has details or structure
                    if session['details'] or (session['structure'] and session['structure'][0]['items']):
                        session_stats[session_type]['completed'] += 1
    
    # Calculate completion percentages and format stats
    progress_stats = {
        'session_progress': [],
        'weight_progress': {
            'starting_weight': starting_weight,
            'current_weight': current_weight,
            'weight_loss': round(starting_weight - current_weight, 2) if starting_weight and current_weight else None
        }
    }
    
    for session_type, stats in session_stats.items():
        if stats['total'] > 0:
            completion_rate = (stats['completed'] / stats['total']) * 100
            progress_stats['session_progress'].append({
                'type': session_type,
                'completed': stats['completed'],
                'total': stats['total'],
                'percentage': round(completion_rate, 1)
            })
    
    return progress_stats

@app.route('/')
def home():
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@app.route('/api/training/<month>')
def get_training_data(month):
    try:
        file_path = os.path.join('planning', f'{month}_2025.md')
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Parse the content
        weeks = parse_training_file(file_path)
        
        # Debug: Print the JSON structure for the first day's sessions
        if weeks and weeks[0]['days']:
            print("\nDEBUG: First day's sessions:")
            print(json.dumps(weeks[0]['days'][0]['sessions'], indent=2))
            
        return jsonify(weeks)
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/progress/<month>')
def get_progress(month):
    try:
        file_path = os.path.join('planning', f'{month}_2025.md')
        with open(file_path, 'r') as f:
            content = f.read()
        
        weeks = parse_training_file(file_path)
        progress = calculate_progress(weeks)
        return jsonify(progress)
    except Exception as e:
        print(f"Error calculating progress: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8080, debug=True)
