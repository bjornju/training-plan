from flask import Flask, send_file, send_from_directory, jsonify
import re
import json
from pathlib import Path
import os
from datetime import datetime
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)

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

def get_actual_weights(month):
    try:
        progress_file = os.path.join('progress', f'{month}_2025_progress.md')
        print(f"\n=== Reading progress file: {progress_file} ===")  # Debug
        
        if not os.path.exists(progress_file):
            print(f"Progress file not found: {progress_file}")  # Debug
            return []
        
        actual_weights = []
        
        with open(progress_file, 'r') as f:
            content = f.read()
            print(f"\nProgress file content:\n{content}\n")  # Debug
            
        # Parse each day's entry - using simpler pattern that works
        day_pattern = r'### ([A-Za-z]+ [A-Za-z]+ \d+) \| Weight: ([\d.]+) kg'
        matches = list(re.finditer(day_pattern, content))
        print(f"\nFound {len(matches)} weight entries")  # Debug
        
        # Print all matches
        for i, match in enumerate(matches):
            print(f"Match {i+1}:")
            print(f"  Full match: '{match.group(0)}'")
            print(f"  Groups: {match.groups()}")
            print(f"  Start: {match.start()}, End: {match.end()}")
        
        for match in matches:
            date_str, weight = match.groups()
            date_str = date_str.strip()  # Clean up any extra whitespace
            weight = weight.strip()  # Clean up any extra whitespace
            print(f"Found match - Date: '{date_str}', Weight: '{weight}'")  # Debug
            try:
                # Parse date in format "Mon Jan 13"
                date = datetime.strptime(f"{date_str} 2025", '%a %b %d %Y')
                weight_float = float(weight)
                actual_weights.append({
                    'date': date,
                    'weight': weight_float
                })
                print(f"Successfully parsed weight: {weight_float} kg for date: {date}")  # Debug
            except ValueError as e:
                print(f"Error parsing date or weight: {e}")
                continue
        
        # Sort by date and return
        sorted_weights = sorted(actual_weights, key=lambda x: x['date'])
        print(f"\nFinal sorted weights: {sorted_weights}")  # Debug
        return sorted_weights
    except Exception as e:
        print(f"Error reading progress file: {str(e)}")
        traceback.print_exc()  # Print full stack trace
        return []

def calculate_progress(weeks, actual_weights):
    try:
        current_time = datetime.strptime('2025-01-13T22:48:17+01:00', '%Y-%m-%dT%H:%M:%S%z')
        print(f"\n=== Calculating Progress ===")  # Debug
        print(f"Current time: {current_time}")  # Debug
        
        # Initialize counters for each session type
        session_stats = {}
        
        # Get starting and current weight from actual weights
        starting_weight = None
        current_weight = None
        weight_loss = None
        
        if actual_weights:
            starting_weight = float(actual_weights[0]['weight'])
            current_weight = float(actual_weights[-1]['weight'])
            weight_loss = round(starting_weight - current_weight, 2) if starting_weight and current_weight else None
            print(f"Calculated weights - Starting: {starting_weight}, Current: {current_weight}, Loss: {weight_loss}")  # Debug
        else:
            print("No actual weights found")  # Debug
        
        # Track planned weights and dates
        planned_weights = []
        dates = []
        
        for week in weeks:
            for day in week['days']:
                try:
                    # Parse the date correctly based on month
                    date_str = day['date']  # e.g. "Feb 1"
                    month = date_str.split()[0]  # e.g. "Feb"
                    day_num = int(date_str.split()[1])  # e.g. 1
                    
                    # Convert month abbreviation to month number
                    month_num = datetime.strptime(month, '%b').month
                    
                    # Create full date in 2025
                    day_date = datetime(2025, month_num, day_num)
                    dates.append(day_date)
                    print(f"Parsed date {date_str} as {day_date}")  # Debug
                    
                    # Track planned weights
                    if day.get('weight'):  # Use get() to safely handle missing weight
                        try:
                            weight = float(day['weight'])
                            planned_weights.append({
                                'date': day_date,
                                'weight': weight
                            })
                            print(f"Added planned weight: {weight} for date: {day_date}")  # Debug
                        except (ValueError, TypeError) as e:
                            print(f"Error parsing planned weight for {date_str}: {e}")
                    
                    # Only process sessions that have passed
                    if day_date.date() <= current_time.date():
                        # Process sessions
                        for session in day.get('sessions', []):  # Use get() with default empty list
                            session_type = session['name'].split(':')[-1].strip() if ':' in session['name'] else session['name']
                            
                            # Initialize stats for new session type
                            if session_type not in session_stats:
                                session_stats[session_type] = {
                                    'total': 0,
                                    'completed': 0
                                }
                            
                            session_stats[session_type]['total'] += 1
                            # Consider a session completed if it has details or structure
                            if session.get('details') or (session.get('structure') and session['structure'][0].get('items')):
                                session_stats[session_type]['completed'] += 1
                except Exception as e:
                    print(f"Error processing day {date_str}: {e}")  # Debug
                    continue
        
        # Calculate completion percentages and format stats
        progress_stats = {
            'session_progress': [],
            'weight_progress': {
                'starting_weight': starting_weight,
                'current_weight': current_weight,
                'weight_loss': weight_loss,
                'planned_weights': [float(w['weight']) for w in sorted(planned_weights, key=lambda x: x['date'])],
                'actual_weights': [float(w['weight']) for w in sorted(actual_weights, key=lambda x: x['date'])],
                'dates': [d.strftime('%Y-%m-%d') for d in dates]
            }
        }
        
        print(f"\n=== Progress Stats ===")  # Debug
        print(f"Session Progress: {json.dumps(progress_stats['session_progress'], indent=2)}")  # Debug
        print(f"Weight Progress: {json.dumps(progress_stats['weight_progress'], indent=2)}")  # Debug
        
        # Only include session types that have at least one session
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
    except Exception as e:
        print(f"Error in calculate_progress: {str(e)}")
        traceback.print_exc()
        raise  # Re-raise the exception to be caught by the route handler

@app.route('/')
def home():
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@app.route('/api/training/<month>')
def get_training_data(month):
    try:
        print(f"\n=== Getting training data for month: {month} ===")  # Debug
        file_path = os.path.join('planning', f'{month}_2025.md')
        print(f"Looking for file: {file_path}")  # Debug
        
        if not os.path.exists(file_path):
            print(f"Training file not found: {file_path}")  # Debug
            return jsonify({"error": f"Training file not found: {file_path}"}), 404
            
        with open(file_path, 'r') as f:
            content = f.read()
            print(f"Found training file with {len(content)} bytes")  # Debug
            
        # Parse the content
        weeks = parse_training_file(file_path)
        print(f"Parsed {len(weeks)} weeks of training data")  # Debug
        return jsonify(weeks)
        
    except Exception as e:
        print(f"Error in get_training_data: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/progress/<month>')
def get_progress(month):
    try:
        print(f"\n=== Getting progress for month: {month} ===")  # Debug
        
        # First get the training data
        file_path = os.path.join('planning', f'{month}_2025.md')
        if not os.path.exists(file_path):
            print(f"Training file not found: {file_path}")  # Debug
            return jsonify({"error": f"Training file not found: {file_path}"}), 404
            
        with open(file_path, 'r') as f:
            content = f.read()
            print(f"Found training file with {len(content)} bytes")  # Debug
            
        weeks = parse_training_file(file_path)
        if not weeks:
            print("No training data found")  # Debug
            return jsonify({"error": "No training data found"}), 404
            
        # Get actual weights
        actual_weights = get_actual_weights(month)
        print(f"Found actual weights: {json.dumps(actual_weights, indent=2, default=str)}")  # Debug
            
        # Calculate progress
        progress = calculate_progress(weeks, actual_weights)
        print(f"Final progress data: {json.dumps(progress, indent=2, default=str)}")  # Debug
        
        # Ensure we have the required structure
        if not progress.get('weight_progress'):
            progress['weight_progress'] = {
                'starting_weight': None,
                'current_weight': None,
                'weight_loss': None,
                'planned_weights': [],
                'actual_weights': [],
                'dates': []
            }
        if not progress.get('session_progress'):
            progress['session_progress'] = []
            
        return jsonify(progress)
        
    except Exception as e:
        print(f"Error in get_progress: {str(e)}")
        traceback.print_exc()  # Print full stack trace
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8080, debug=True, use_reloader=True)
