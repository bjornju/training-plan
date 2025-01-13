import re
from datetime import datetime
import json

def test_weight_parsing():
    # Read the January progress file
    with open('progress/january_2025_progress.md', 'r') as f:
        content = f.read()
    
    print("\nFile content:")
    print(content)
    print("\n" + "="*50 + "\n")
    
    # Try different regex patterns
    patterns = [
        (r'### ([A-Za-z]+ [A-Za-z]+ \d+) \| Weight: ([\d.]+) kg \| Calories:', "Pattern 1 - Exact with Calories"),
        (r'### ([A-Za-z]+ [A-Za-z]+ \d+) \| Weight: ([\d.]+) kg', "Pattern 2 - Just weight"),
        (r'### ([A-Za-z]+ [A-Za-z]+ \d+)\s*\|\s*Weight:\s*([\d.]+)\s*kg', "Pattern 3 - Flexible whitespace")
    ]
    
    for pattern, desc in patterns:
        print(f"\nTesting {desc}")
        print(f"Pattern: {pattern}")
        
        matches = list(re.finditer(pattern, content))
        print(f"Found {len(matches)} matches")
        
        weights = []
        for match in matches:
            date_str, weight = match.groups()
            print(f"\nMatch found:")
            print(f"  Full match: '{match.group(0)}'")
            print(f"  Date: '{date_str}'")
            print(f"  Weight: '{weight}'")
            
            try:
                date = datetime.strptime(f"{date_str} 2025", '%a %b %d %Y')
                weight_float = float(weight)
                weights.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'weight': weight_float
                })
            except ValueError as e:
                print(f"Error parsing: {e}")
        
        print("\nParsed weights:")
        print(json.dumps(weights, indent=2))
        print("\n" + "="*50)

if __name__ == '__main__':
    test_weight_parsing()
