# Orienteering Training Plan

## Overview
This training plan is designed to improve orienteering skills while maintaining a daily run streak and supporting weight management goals.

## Training Plan Structure
The plan is divided into monthly segments:
- [January 2025](planning/january_2025.md) - Weeks 1-3
- [February 2025](planning/february_2025.md) - Weeks 4-7
- [March 2025](planning/march_2025.md) - Weeks 8-11
- [April 2025](planning/april_2025.md) - Weeks 12-15

## Key Components

### Daily Run Streak
- Minimum distance: 1.5 km
- Can be integrated into warm-ups on training days
- Very easy intensity on rest days
- Morning timing preferred

### Weight Management
Starting weight: 74.00 kg
Target weight: 67.85 kg
Weekly weight loss target: 0.41 kg

### Training Intensity Levels
- High intensity days: 2,200-2,300 kcal
- Medium intensity days: 2,000-2,100 kcal
- Rest/Light days: 1,800-1,900 kcal

### Recovery Strategy
- Active recovery on rest days
- Mobility work
- Technical study
- Proper nutrition timing

### Equipment Checklist
Standard training equipment:
- Compass
- Map holder
- Watch with HR monitor
- Water bottles
- Exercise mat
- Resistance bands
- Light weights
- Timer
- Foam roller

Additional equipment for long sessions:
- Energy gels
- Emergency snack
- Light backpack
- Phone (emergency only)
- Weather appropriate clothing
- First aid basics

## Training Locations
Primary training areas:
- Djurgården
- Lidingö
- Hellasgården

## Progress Tracking
- Daily weight measurements
- Caloric intake monitoring
- Session analysis and feedback
- Weekly reviews and adjustments

## Training Plan Viewer

An interactive web-based viewer for training plans with visual enhancements and exercise guides.

## Features

- Visual representation of training plans
- Weekly metrics and statistics
- Exercise descriptions and guides
- Equipment tracking
- Mobile-friendly design

## Local Development

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install flask
   ```
3. Run the development server:
   ```bash
   python server.py
   ```
4. Open http://localhost:8080 in your browser

## Deployment

This site is deployed using GitHub Pages. To deploy your own version:

1. Fork this repository
2. Go to repository Settings > Pages
3. Set the source to "main" branch and "/" (root) folder
4. Your site will be available at https://[username].github.io/training-plan/

## File Structure

- `index.html` - Main viewer application
- `planning/*_2025.md` - Training plan data files
- `server.py` - Local development server
