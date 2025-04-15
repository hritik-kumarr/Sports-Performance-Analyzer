import os
import requests
import re
import time
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app with correct static folder configuration
app = Flask(__name__, static_folder='public', static_url_path='')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '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')
PORT = int(os.getenv('PORT', 3000))
USE_OFFLINE_MODE = False  # Set to False to use the API

def is_sports_performance_related(message):
    """Check if the message is related to sports performance analysis"""
    # If message is too short, likely not sports performance-related
    if len(message.strip()) < 3:
        return False
        
    sports_keywords = [
        'performance', 'analysis', 'metrics', 'stats', 'statistics', 'athlete', 'player', 'team',
        'training', 'workout', 'fitness', 'strength', 'conditioning', 'endurance', 'speed',
        'agility', 'power', 'recovery', 'injury', 'prevention', 'rehab', 'nutrition',
        'hydration', 'sleep', 'fatigue', 'energy', 'stamina', 'technique', 'form',
        'biomechanics', 'movement', 'motion', 'tracking', 'monitor', 'measure', 'improvement',
        'progress', 'goal', 'achievement', 'competition', 'match', 'game', 'season',
        'career', 'amateur', 'professional', 'elite', 'olympic', 'championship', 'league',
        'tournament', 'benchmark', 'baseline', 'test', 'assessment', 'evaluation', 'score',
        'rating', 'ranking', 'comparison', 'trend', 'pattern', 'insight', 'data',
        'analytics', 'visualization', 'report', 'dashboard', 'KPI', 'metric', 'statistic',
        'VO2 max', 'heart rate', 'HR', 'lactate', 'threshold', 'zone', 'intensity',
        'volume', 'load', 'RPE', 'perceived exertion', 'GPS', 'accelerometer', 'wearable',
        'sensor', 'camera', 'video', 'footage', 'replay', 'tactic', 'strategy',
        'play', 'formation', 'position', 'offense', 'defense', 'skill', 'ability',
        'talent', 'potential', 'development', 'coach', 'trainer', 'physio', 'therapist',
        'doctor', 'nutritionist', 'psychologist', 'mental', 'focus', 'concentration',
        'motivation', 'confidence', 'anxiety', 'stress', 'pressure', 'routine',
        'habit', 'discipline', 'consistency', 'periodization', 'macrocycle', 'mesocycle',
        'microcycle', 'preseason', 'inseason', 'offseason', 'peak', 'taper',
        'football', 'soccer', 'basketball', 'baseball', 'hockey', 'tennis', 'golf',
        'swimming', 'track', 'field', 'running', 'cycling', 'triathlon', 'marathon',
        'sprint', 'weight lifting', 'gymnastics', 'volleyball', 'rugby', 'cricket',
        'health', 'wellness', 'wellbeing', 'diet', 'exercise', 'lifestyle', 'healthy',
        'weight loss', 'weight gain', 'body fat', 'muscle', 'cardio', 'stretching',
        'flexibility', 'mobility', 'balance', 'posture', 'meditation', 'mindfulness',
        'relaxation', 'rest', 'metabolism', 'vitamins', 'minerals', 'proteins', 'carbs',
        'fats', 'supplements', 'immune', 'longevity', 'vitality', 'aging', 'prevention'
    ]

    message_lower = message.lower()
    
    # Detect measurement patterns (could indicate performance analysis)
    measurement_pattern = r'\b\d+[\s-]?(?:kg|lb|s|min|km|mi|mph|km/h|bpm|%|cm|m)\b'
    if re.search(measurement_pattern, message_lower):
        return True
        
    # Detect comparative references
    comparison_keywords = ['improve', 'better', 'faster', 'stronger', 'higher', 'lower', 'increase', 'decrease', 'optimize', 'maximize']
    for word in comparison_keywords:
        if word in message_lower.split():
            return True
    
    # Check for possessive references to sports
    possessive_pattern = r'\b(?:my|our|their|your|the)\s+(?:performance|training|workout|game|match|team|stats)\b'
    if re.search(possessive_pattern, message_lower):
        return True
    
    # Check for keywords
    for keyword in sports_keywords:
        if keyword.lower() in message_lower:
            return True

    # Additional heuristic: Check for phrases commonly used in sports performance
    sports_phrases = [
        'how to improve', 'best method for', 'analyze my', 'track my', 'measure my',
        'training plan', 'workout routine', 'performance metrics', 'player stats',
        'team analytics', 'injury prevention', 'recovery strategy', 'nutrition plan',
        'how to get faster', 'how to get stronger', 'improve technique'
    ]

    for phrase in sports_phrases:
        if phrase.lower() in message_lower:
            return True

    return False

def format_response(response_text):
    """Format the raw LLM response for better presentation"""
    if not response_text:
        return "I apologize, but I couldn't generate a response. Please try again."

    # Remove any unnecessary prefixes
    import re
    clean_response = re.sub(r'^(as an ai assistant|as a tournament planning assistant|i am a tournament planning assistant|as your tournament assistant)', '', response_text, flags=re.IGNORECASE).strip()

    # Ensure first letter is capitalized
    clean_response = clean_response[0].upper() + clean_response[1:] if clean_response else clean_response
    
    # Format response with HTML line breaks and proper styling
    clean_response = format_text_with_html(clean_response)
    
    return clean_response

def format_text_with_html(text):
    """Convert plain text formatting to HTML for better display"""
    if not text:
        return text
        
    # Replace repeated newlines with paragraph breaks
    text = re.sub(r'\n\s*\n', '</p><p>', text)
    
    # Replace single newlines with breaks
    text = text.replace('\n', '<br>')
    
    # Format numbered lists
    text = re.sub(r'(\d+)\.\s+([^\n<]+)', r'<b>\1.</b> \2', text)
    
    # Format bullet points
    text = re.sub(r'[-•*]\s+([^\n<]+)', r'• \1', text)
    
    # Wrap in paragraph if not already
    if not text.startswith('<p>'):
        text = '<p>' + text + '</p>'
        
    # Replace any multiple breaks
    text = re.sub(r'<br>\s*<br>', '</p><p>', text)
    
    # Clean up any empty paragraphs
    text = re.sub(r'<p>\s*</p>', '', text)
    
    return text

def handle_chat_request(message):
    """Process chat request and get response from LLM"""
    try:
        # Include a timestamp in offline responses to make them unique
        timestamp = int(time.time())
        
        # Check if the message is related to sports performance
        if not is_sports_performance_related(message):
            return "<p>This query is out of scope. I can only help with sports performance analysis.</p>"
            
        # Add a unique session ID to messages to avoid caching
        user_session_id = request.cookies.get('session_id', str(timestamp))
            
        # Using offline mode (no API calls)
        if USE_OFFLINE_MODE:
            return get_offline_response(message, timestamp)

        # Call the Hugging Face Inference API with a more reliable model
        try:
            input_context = f"""<s>[INST] You are SportsAnalytica, a specialized assistant for sports performance analysis and health & wellness guidance. Answer this question in comprehensive detail: {message}

Your response should:
1. Include specific examples and clear insights
2. Use HTML formatting (<p>, <ul>, <li>, <b>) for readability 
3. Be thorough and informative, at least 150-200 words
4. Include practical advice for users
5. Avoid saying "undefined" or giving very short responses
6. Be direct and focused on the topic at hand

If asked about:
- Performance metrics (explain relevant KPIs and measurement techniques)
- Training optimization (personalized workout guidance, periodization)
- Recovery strategies (injury prevention, nutrition, sleep optimization)
- Data analytics (interpreting statistics, performance trends)
- Technique improvement (biomechanics, form correction, skill development)
- Health & wellness (nutrition, lifestyle, general fitness, wellbeing)

Session ID: {user_session_id}-{timestamp} [/INST]</s>"""
            
            print(f"Calling API for: {message}")
            
            response = requests.post(
                'https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2',
                json={
                    'inputs': input_context,
                    'parameters': {
                        'max_new_tokens': 800,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'return_full_text': False
                    },
                    'options': {'use_cache': False, 'wait_for_model': True}
                },
                headers={
                    'Authorization': f'Bearer {HUGGINGFACE_API_KEY}',
                    'Content-Type': 'application/json'
                },
                timeout=20  # Increased timeout
            )
            
            print(f"API response status: {response.status_code}")
            
            # Extract and format the response
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"Raw API result type: {type(result)}")
                    
                    # Handle different response formats
                    if isinstance(result, list) and len(result) > 0:
                        if 'generated_text' in result[0]:
                            api_response = format_response(result[0]['generated_text'])
                        else:
                            api_response = format_response(str(result[0]))
                    elif isinstance(result, dict) and 'generated_text' in result:
                        api_response = format_response(result['generated_text'])
                    else:
                        api_response = format_response(str(result))
                    
                    # Final validation
                    if api_response and len(api_response) > 50 and 'undefined' not in api_response.lower():
                        return api_response
                    else:
                        print(f"API response too short or contains 'undefined': {api_response}")
                        return get_offline_response(message, timestamp)
                except Exception as e:
                    print(f"Error processing API response: {e}")
                    return get_offline_response(message, timestamp)
            else:
                print(f"API request failed with status {response.status_code}")
                return get_offline_response(message, timestamp)
                
        except requests.exceptions.RequestException as e:
            # If API call fails, use fallback response
            print(f"API request exception: {e}")
            return get_offline_response(message, timestamp)
            
    except Exception as e:
        print(f"Error in chat service: {e}")
        return get_offline_response(message, int(time.time()))

def get_offline_response(message, timestamp=None):
    """Generate an offline response based on message keywords"""
    message_lower = message.lower()
    
    # Add some randomness to responses
    if timestamp is None:
        timestamp = int(time.time())
    
    # Make the response subtly different based on timestamp
    response_variant = timestamp % 3  # Creates 3 variants
    
    # Check for strength training questions
    if any(word in message_lower for word in ['strength', 'lifting', 'weights', 'muscle']) and any(word in message_lower for word in ['training', 'workout', 'program', 'routine']):
        return """<p>Developing an effective strength training program involves several key components:</p>
        
        <p><b>Strength Training Fundamentals:</b></p>
        <ul>
            <li><b>Progressive overload:</b> Gradually increasing weight, frequency, or reps</li>
            <li><b>Exercise selection:</b> Compound movements (squats, deadlifts, bench press) for efficiency</li>
            <li><b>Training volume:</b> Balancing sets, reps, and intensity for optimal stimulus</li>
            <li><b>Rest periods:</b> Typically 2-5 minutes for strength, 30-90 seconds for hypertrophy</li>
            <li><b>Training frequency:</b> Each muscle group 2-3 times per week for most athletes</li>
        </ul>
        
        <p><b>Performance Metrics to Track:</b></p>
        <ul>
            <li><b>1RM (one-rep max):</b> Maximum weight lifted for a single repetition</li>
            <li><b>Volume load:</b> Total weight × sets × reps per session/week</li>
            <li><b>Rate of perceived exertion (RPE):</b> Subjective intensity measure on 1-10 scale</li>
            <li><b>Velocity:</b> Movement speed with submaximal loads (requires special equipment)</li>
            <li><b>Work capacity:</b> Total workload completed in a given time period</li>
        </ul>
        
        <p><b>Programming Considerations:</b></p>
        <ul>
            <li><b>Periodization:</b> Structured variation in training variables over time</li>
            <li><b>Recovery management:</b> Balancing training stress with adequate recovery</li>
            <li><b>Sport-specific needs:</b> Tailoring strength work to sport demands</li>
            <li><b>Individual response:</b> Adjusting based on progress and feedback</li>
            <li><b>Testing protocols:</b> Regular assessment of strength gains and adaptations</li>
        </ul>
        
        <p>Would you like more specific advice on any aspect of strength training or performance measurement?</p>"""
    
    # Check for performance metrics questions
    if any(word in message_lower for word in ['metric', 'measure', 'track', 'monitor', 'analyze']) and any(word in message_lower for word in ['performance', 'progress', 'improvement', 'stats', 'data']):
        return """<p>For comprehensive sports performance analysis, consider these key metrics and measurement approaches:</p>
        
        <p><b>1. Physical Performance Metrics</b></p>
        <ul>
            <li><b>Speed:</b> Sprint times (10m, 20m, 40m), maximum velocity, acceleration profiles</li>
            <li><b>Strength:</b> 1RM tests, force-velocity profiles, rate of force development</li>
            <li><b>Power:</b> Vertical jump height, broad jump distance, medicine ball throw</li>
            <li><b>Endurance:</b> VO2max, lactate threshold, critical power, heart rate recovery</li>
            <li><b>Agility:</b> T-test, 5-10-5 shuttle, reactive agility with decision-making</li>
        </ul>
        
        <p><b>2. Workload Monitoring</b></p>
        <ul>
            <li><b>External load:</b> GPS metrics (distance, speeds, accelerations), weights lifted</li>
            <li><b>Internal load:</b> RPE × duration, heart rate-based training impulse (TRIMP)</li>
            <li><b>Acute:Chronic Workload Ratio:</b> Comparing recent vs. established workload</li>
            <li><b>Training monotony:</b> Variation in daily training load (lower is better)</li>
            <li><b>Training strain:</b> Product of weekly load and monotony</li>
        </ul>
        
        <p><b>3. Recovery Assessment</b></p>
        <ul>
            <li><b>Subjective measures:</b> Wellness questionnaires, sleep quality, muscle soreness</li>
            <li><b>Physiological markers:</b> HRV (heart rate variability), resting HR, blood markers</li>
            <li><b>Neuromuscular function:</b> Countermovement jump, grip strength, reaction time</li>
            <li><b>Psychological readiness:</b> Mood state, perceived fatigue, readiness to train</li>
            <li><b>Sleep metrics:</b> Total sleep time, sleep efficiency, sleep stages</li>
        </ul>
        
        <p>For creating an effective monitoring system, I recommend selecting 2-3 metrics from each category that are most relevant to your sport and implementing a consistent testing schedule to track changes over time.</p>"""
    
    # Check for nutrition and recovery questions
    if any(word in message_lower for word in ['nutrition', 'diet', 'food', 'eat', 'meal']) and any(word in message_lower for word in ['performance', 'recovery', 'energy', 'training']):
        return """<p>Optimizing nutrition for athletic performance and recovery requires a strategic approach:</p>
        
        <p><b>Performance Nutrition Fundamentals:</b></p>
        <ul>
            <li><b>Energy availability:</b> Consuming adequate calories to support training demands</li>
            <li><b>Macronutrient distribution:</b> Personalized ratios of carbs, protein, and fats</li>
            <li><b>Nutrient timing:</b> Strategic intake around training sessions</li>
            <li><b>Hydration strategy:</b> Individualized fluid and electrolyte protocol</li>
            <li><b>Micronutrient sufficiency:</b> Ensuring adequate vitamins and minerals</li>
        </ul>
        
        <p><b>Training Day Nutrition:</b></p>
        <ul>
            <li><b>Pre-workout (1-3 hours before):</b> Moderate protein, easy-digest carbs, low fat</li>
            <li><b>During training:</b> Carbohydrate intake for sessions >60 minutes (30-60g/hour)</li>
            <li><b>Post-workout (within 30-60 min):</b> 20-40g protein, 0.5-0.7g carbs/kg bodyweight</li>
            <li><b>Recovery meals:</b> Complete proteins, complex carbs, healthy fats, vegetables</li>
            <li><b>Hydration restoration:</b> 150% of fluid lost (weigh before/after training)</li>
        </ul>
        
        <p><b>Performance-Based Nutrition Periodization:</b></p>
        <ul>
            <li><b>Training adaptations:</b> Matching nutrition to training block goals</li>
            <li><b>Carbohydrate periodization:</b> Strategic manipulation for metabolic adaptations</li>
            <li><b>Recovery-focused periods:</b> Increased anti-inflammatory foods, antioxidants</li>
            <li><b>Competition preparation:</b> Carbohydrate loading, sodium/fluid strategies</li>
            <li><b>Supplement integration:</b> Evidence-based ergogenic aids when appropriate</li>
        </ul>
        
        <p>Would you like more specific nutritional guidance for your particular sport or training phase?</p>"""
    
    # Check for team creation questions
    if any(word in message_lower for word in ['make', 'create', 'form']) and any(word in message_lower for word in ['team', 'squad', 'roster']):
        return """<p>Creating a successful tournament team involves several key steps:</p>
        
        <p><b>Team Formation Essentials:</b></p>
        <ul>
            <li><b>Roster size:</b> Determine optimal team size (core players + substitutes)</li>
            <li><b>Skill balance:</b> Mix experienced players with promising newcomers</li>
            <li><b>Role definition:</b> Clearly establish each player's responsibilities</li>
            <li><b>Team captain:</b> Select a leader for communication and decision-making</li>
            <li><b>Team name/identity:</b> Create a memorable brand for your team</li>
        </ul>
        
        <p><b>Administrative Requirements:</b></p>
        <ul>
            <li><b>Registration forms:</b> Complete all required tournament paperwork</li>
            <li><b>Contact information:</b> Maintain updated contact details for all members</li>
            <li><b>Equipment/uniforms:</b> Ensure consistent appearance if required</li>
            <li><b>Tournament rules:</b> Familiarize all members with competition rules</li>
            <li><b>Practice schedule:</b> Establish regular training sessions before the event</li>
        </ul>
        
        <p><b>Team Management Tips:</b></p>
        <ul>
            <li><b>Communication channel:</b> Create a group chat or email list</li>
            <li><b>Availability tracking:</b> Confirm player availability for all tournament dates</li>
            <li><b>Strategy development:</b> Prepare and practice competitive approaches</li>
            <li><b>Conflict resolution:</b> Establish a process for handling disagreements</li>
            <li><b>Feedback mechanism:</b> Create opportunities for constructive criticism</li>
        </ul>
        
        <p>Would you like more specific advice on any aspect of team creation?</p>"""
    
    # Check for 16-team fixture/schedule questions
    if any(word in message_lower for word in ['fixture', 'schedule', 'bracket', 'draw']) and ('16' in message_lower or 'sixteen' in message_lower):
        return """<p>For a 16-team tournament, here are the most common format options with their fixture structures:</p>
        
        <p><b>1. Single Elimination Bracket (15 matches total)</b></p>
        <ul>
            <li><b>Round 1 (Round of 16):</b> 8 matches - Teams 1v16, 8v9, 5v12, 4v13, 3v14, 6v11, 7v10, 2v15</li>
            <li><b>Quarterfinals:</b> 4 matches - Winners of Round 1 matches</li>
            <li><b>Semifinals:</b> 2 matches - Winners of Quarterfinals</li>
            <li><b>Final:</b> 1 match - Winners of Semifinals</li>
        </ul>
        
        <p><b>2. Double Elimination (30 matches maximum)</b></p>
        <ul>
            <li>Follows single elimination format but with a losers bracket</li>
            <li>Teams need to lose twice to be eliminated</li>
            <li>Requires approximately twice the number of matches</li>
        </ul>
        
        <p><b>3. Group Stage + Knockout (32 matches total)</b></p>
        <ul>
            <li><b>Group Stage:</b> 4 groups of 4 teams each (6 matches per group, 24 total)</li>
            <li><b>Each team plays 3 matches</b> (once against each team in their group)</li>
            <li><b>Quarterfinals:</b> Top 2 teams from each group advance (4 matches)</li>
            <li><b>Semifinals:</b> 2 matches</li>
            <li><b>Final & 3rd place match:</b> 2 matches</li>
        </ul>
        
        <p><b>4. Swiss System (5-7 rounds, 40-56 matches total)</b></p>
        <ul>
            <li>Each round pairs teams with similar records</li>
            <li>No eliminations until final standings</li>
            <li>Recommended for 5-7 rounds for 16 teams</li>
            <li>8 matches per round (40-56 matches total)</li>
        </ul>
        
        <p>For creating the actual fixture schedule, I recommend using tournament software like Challonge, Toornament, or dedicated spreadsheet templates that can generate the matchups automatically based on your chosen format.</p>"""
    
    # Check for chess tournament equipment questions
    if any(word in message_lower for word in ['chess', 'equipment', 'supplies', 'need']) and any(word in message_lower for word in ['tournament', 'competition', 'event']):
        return """<p>For organizing a chess tournament, you'll need the following equipment:</p>
        
        <p><b>Essential Chess Equipment:</b></p>
        <ul>
            <li><b>Chess sets:</b> Standard Staunton design, with 3.75" king height for tournament play</li>
            <li><b>Chess boards:</b> Standard 2.25" squares, vinyl rollup mats are cost-effective</li>
            <li><b>Chess clocks:</b> Digital preferred (DGT, Chronos) with delay/increment capability</li>
            <li><b>Score sheets:</b> Standard algebraic notation sheets for players to record moves</li>
            <li><b>Pens:</b> Provide for players to fill in score sheets</li>
        </ul>
        
        <p><b>Tournament Organization Materials:</b></p>
        <ul>
            <li><b>Pairing software:</b> Swiss-Manager, Vega, or lichess.org's free tournament manager</li>
            <li><b>Results slips:</b> For players to record and submit game outcomes</li>
            <li><b>Wall charts/projector:</b> To display standings and pairings</li>
            <li><b>Table numbers:</b> To help players find their boards</li>
            <li><b>Rule books:</b> FIDE/National Chess Federation rules as appropriate</li>
        </ul>
        
        <p><b>Venue Requirements:</b></p>
        <ul>
            <li><b>Tables:</b> At least 2.5' x 2.5' per board</li>
            <li><b>Chairs:</b> Comfortable enough for long games</li>
            <li><b>Good lighting:</b> Critical for players to see the board clearly</li>
            <li><b>Quiet environment:</b> Minimize external noise</li>
            <li><b>Tournament director's table:</b> Central location for administration</li>
        </ul>
        
        <p><b>Optional/Additional Items:</b></p>
        <ul>
            <li><b>Spare pieces and boards:</b> In case of damage or loss</li>
            <li><b>Demonstration board:</b> For game analysis or featured matches</li>
            <li><b>Certificates/trophies:</b> For winners and participants</li>
            <li><b>Name tags:</b> For officials and staff</li>
            <li><b>First aid kit:</b> For any minor emergencies</li>
        </ul>
        
        <p>For large tournaments, consider renting equipment from local chess clubs or federations to reduce costs.</p>"""
    
    # Round-robin tournament organization
    if ('round' in message_lower and 'robin' in message_lower) or 'round-robin' in message_lower:
        if any(word in message_lower for word in ['organize', 'create', 'start', 'setup', 'schedule', 'plan']):
            return """<p>Organizing a round-robin tournament requires careful planning. Here's a comprehensive guide:</p>

            <p><b>1. Planning Your Round-Robin Tournament</b></p>
            <ul>
                <li><b>Determine participant count:</b> Ideal for 6-12 teams (more teams require more rounds)</li>
                <li><b>Calculate total matches:</b> n(n-1)/2 where n = number of teams</li>
                <li><b>Assess time constraints:</b> Each team plays (n-1) matches</li>
                <li><b>Venue requirements:</b> Ensure adequate space and time allocation</li>
            </ul>

            <p><b>2. Creating the Schedule (Circle Method)</b></p>
            <ol>
                <li>Assign numbers to each team (1 through n)</li>
                <li>If you have an odd number of teams, add a "bye" (making it even)</li>
                <li>Place team #1 at the top and arrange remaining teams in a circle</li>
                <li>Record the matchups for round 1 (each team paired with the one opposite)</li>
                <li>Rotate all teams except #1 clockwise for the next round</li>
                <li>Repeat until all rounds are scheduled</li>
            </ol>

            <p><b>3. Schedule Example for 8 Teams</b></p>
            <p>Round 1: 1v8, 2v7, 3v6, 4v5<br>
            Round 2: 1v7, 8v6, 2v5, 3v4<br>
            Round 3: 1v6, 7v5, 8v4, 2v3<br>
            Round 4: 1v5, 6v4, 7v3, 8v2<br>
            Round 5: 1v4, 5v3, 6v2, 7v8<br>
            Round 6: 1v3, 4v2, 5v8, 6v7<br>
            Round 7: 1v2, 3v8, 4v7, 5v6</p>

            <p><b>4. Logistical Considerations</b></p>
            <ul>
                <li><b>Home/away balance:</b> Alternate if applicable</li>
                <li><b>Rest periods:</b> Avoid scheduling teams for consecutive matches</li>
                <li><b>Field/court rotation:</b> Distribute premium playing areas fairly</li>
                <li><b>Time slots:</b> Account for match duration, setup, and breakdown time</li>
            </ul>

            <p><b>5. Tournament Management</b></p>
            <ul>
                <li><b>Scoring system:</b> Define points for wins, draws, losses (e.g., 3-1-0)</li>
                <li><b>Tiebreakers:</b> Establish clear criteria (head-to-head, point differential, etc.)</li>
                <li><b>Results tracking:</b> Update standings after each match</li>
                <li><b>Software tools:</b> Consider using Tournament.io, Challonge, or Excel templates</li>
            </ul>

            <p><b>6. Communication</b></p>
            <ul>
                <li>Distribute complete schedule to all teams before the tournament</li>
                <li>Provide regular standings updates throughout the event</li>
                <li>Clearly communicate tiebreaker rules in advance</li>
            </ul>

            <p>Would you like me to elaborate on any specific aspect of round-robin tournament organization?</p>"""
    
    # Check for fixture related questions
    if any(word in message_lower for word in ['fixture', 'schedule', 'pairing', 'matchup']) or 'how' in message_lower and any(word in message_lower for word in ['create', 'make', 'generate', 'set up']):
        if '12' in message_lower or 'twelve' in message_lower:
            return """<p>For creating fixtures for a 12-team tournament, you have several options:</p>
            
            <p><b>1. Round Robin Format</b></p>
            <p>For a complete round robin where all teams play each other once:</p>
            <ul>
                <li>Each team will play 11 matches (playing every other team once)</li>
                <li>Total matches: 66 (12 × 11 ÷ 2)</li>
                <li>Typically requires 11 rounds to complete</li>
            </ul>
            
            <p><b>2. Groups + Knockout Format</b></p>
            <p>Split into 4 groups of 3 teams each:</p>
            <ul>
                <li>Group stage: Each team plays 2 matches (3 matches per group, 12 total)</li>
                <li>Top 2 from each group advance to quarterfinals (8 teams)</li>
                <li>Then 4 quarterfinals, 2 semifinals, and 1 final</li>
                <li>Total matches: 12 (group) + a (quarterfinals) + 2 (semifinals) + 1 (final) = 19 matches</li>
            </ul>
            
            <p><b>3. Swiss System (5 rounds)</b></p>
            <ul>
                <li>Round 1: Random or seeded pairings</li>
                <li>Rounds 2-5: Teams with similar records play each other</li>
                <li>Total matches: 30 (6 matches per round × 5 rounds)</li>
                <li>At the end, rank teams by their record or use tiebreakers</li>
            </ul>
            
            <p>To create the actual fixture table, use tournament software like:</p>
            <ul>
                <li><b>Challonge:</b> Free online bracket generator with round robin support</li>
                <li><b>Toornament:</b> Offers templates for various formats</li>
                <li><b>Microsoft Excel:</b> Use templates or create manually with formulas</li>
            </ul>
            
            <p>For your 12-team tournament, I recommend the Groups + Knockout format unless you have plenty of time for a full round robin.</p>"""
        else:
            return """<p>Creating fixtures (match schedules) depends on your tournament format and number of teams. Here are the main approaches:</p>
            
            <p><b>1. Round Robin Format</b></p>
            <ul>
                <li>Each team plays against all other teams once (or twice for double round robin)</li>
                <li>For n teams, each team plays (n-1) matches</li>
                <li>Total matches = n × (n-1) ÷ 2</li>
                <li>Use the "circle method" where one team stays fixed while others rotate</li>
            </ul>
            
            <p><b>2. Elimination Brackets</b></p>
            <ul>
                <li><b>Single elimination:</b> Losers are immediately eliminated</li>
                <li><b>Double elimination:</b> Losers move to a losers bracket</li>
                <li>For n teams, you'll have (n-1) matches in single elimination</li>
                <li>Seed teams appropriately to balance the bracket</li>
            </ul>
            
            <p><b>3. Groups + Knockout</b></p>
            <ul>
                <li>Divide teams into equal groups for round robin play</li>
                <li>Top teams from each group advance to elimination rounds</li>
                <li>Example: 4 groups of 4, top 2 from each advance to quarterfinals</li>
            </ul>
            
            <p><b>4. Swiss System</b></p>
            <ul>
                <li>Teams with similar records play each other in each round</li>
                <li>No eliminations until the final standings</li>
                <li>Good for large fields where full round robin isn't feasible</li>
            </ul>
            
            <p>To create actual fixtures, you can use software like:</p>
            <ul>
                <li><b>Challonge:</b> Free online bracket generator</li>
                <li><b>Toornament:</b> Robust tournament management platform</li>
                <li><b>Battlefy:</b> Popular for esports tournaments</li>
            </ul>
            
            <p>How many teams are in your tournament? I can provide more specific guidance based on your number of participants.</p>"""
    
    # Check for greetings
    greeting_pattern = r'\b(?:hi|hello|hey|greetings|howdy)\b'
    if re.search(greeting_pattern, message_lower) and len(message_lower) < 10:
        greetings = [
            "<p>Hello! I'm your sports performance analysis assistant. How can I help optimize your athletic performance today?</p>",
            "<p>Hi there! Ready to help with your sports performance needs. What would you like assistance with?</p>",
            "<p>Hey! I'm here to help with your athletic performance analysis. What aspect are you working on?</p>"
        ]
        return greetings[response_variant]
    
    # Check for specific date mentions
    date_match = re.search(r'\b(\d{1,2})\s?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', message_lower)
    if date_match:
        return f"<p>I see your tournament is planned for {date_match.group(0)}. Make sure to send out invitations at least 3-4 weeks in advance, confirm your venue, and prepare your schedule and bracket templates.</p>"
    
    # Check for questions about tournament size
    size_pattern = r'\b(?:how many|number of)\s+(?:teams|players|participants|people)\b'
    if re.search(size_pattern, message_lower):
        return """<p>The ideal number of participants depends on your format:</p>
        
        <p>• For single elimination: Powers of 2 (8, 16, 32, 64) work best</p>
        <p>• For double elimination: Same as single, but plan for about 1.5x more matches</p>
        <p>• For round robin: Usually best with 6-10 participants (otherwise too many matches)</p>
        <p>• For Swiss: Works with any number, but 8+ is better</p>
        
        <p>With more participants, consider using qualifying rounds or group stages.</p>"""
    
    # Questions about scheduling
    if any(word in message_lower for word in ['schedule', 'when', 'time', 'date', 'how long']):
        return """<p>For tournament scheduling, consider:</p>
        
        <p><b>1.</b> Match duration: Estimate realistic times including setup/teardown</p>
        <p><b>2.</b> Breaks: Allow 10-15 minutes between matches and longer breaks for meals</p>
        <p><b>3.</b> Concurrent matches: If possible, run multiple matches simultaneously</p>
        <p><b>4.</b> Buffer time: Add 15-20% extra time for delays</p>
        <p><b>5.</b> Player fatigue: Avoid scheduling too many consecutive matches for same team</p>
        
        <p>Create a detailed schedule and share it with all participants in advance.</p>"""
        
    # Questions about team/player management
    if any(word in message_lower for word in ['teams', 'players', 'participants', 'registration', 'sign up', 'join']):
        return """<p>For managing tournament participants:</p>
        
        <p><b>1.</b> Registration: Use a form with team name, captain contact, roster, and skill level</p>
        <p><b>2.</b> Seeding: Rank teams based on previous performance if available</p>
        <p><b>3.</b> Check-in: Require teams to check in 30-60 minutes before their first match</p>
        <p><b>4.</b> Rules briefing: Hold a captains' meeting to review rules</p>
        <p><b>5.</b> Communication: Create a centralized way to announce updates (app, website, etc.)</p>
        
        <p>Clear organization of participants is key to a smooth tournament.</p>"""
        
    # Questions about tournament rules
    if any(word in message_lower for word in ['rules', 'scoring', 'points', 'win', 'lose', 'regulations']):
        return """<p>When establishing tournament rules:</p>
        
        <p><b>1.</b> Game-specific rules: Clearly define any modifications to standard game rules</p>
        <p><b>2.</b> Match format: Specify number of games/sets/rounds per match</p>
        <p><b>3.</b> Scoring system: Define how winners are determined and points awarded</p>
        <p><b>4.</b> Tiebreakers: Establish criteria for resolving ties in standings</p>
        <p><b>5.</b> Conduct rules: Set expectations for sportsmanship and penalties for violations</p>
        
        <p>Document all rules and distribute to participants before the tournament begins.</p>"""
    
    # Questions about brackets and advancement
    if any(word in message_lower for word in ['bracket', 'elimination', 'knockout', 'advance', 'progress', 'move on']):
        return """<p>For tournament advancement and brackets:</p>
        
        <p><b>1.</b> Single elimination: Winners advance, losers are eliminated</p>
        <p><b>2.</b> Double elimination: Players move to losers bracket after first loss, eliminated after second</p>
        <p><b>3.</b> Group stage: Top 1-2 teams from each group advance to playoffs</p>
        <p><b>4.</b> Swiss system: Players with similar records are paired, final rankings determine winners</p>
        
        <p>Use tournament software or websites like Challonge or Toornament to create and manage your brackets.</p>"""
        
    # Questions about venues and equipment
    if any(word in message_lower for word in ['venue', 'location', 'place', 'equipment', 'setup', 'space']):
        return """<p>When selecting a tournament venue:</p>
        
        <p><b>1.</b> Size: Ensure adequate space for all matches, participants, and spectators</p>
        <p><b>2.</b> Equipment: Confirm all necessary game equipment, tables, chairs, etc.</p>
        <p><b>3.</b> Technical needs: Check power outlets, internet connectivity, A/V systems</p>
        <p><b>4.</b> Amenities: Consider restrooms, food/drink options, parking availability</p>
        <p><b>5.</b> Cost: Factor in rental fees, insurance, and security deposits</p>
        
        <p>Visit potential venues in person before booking to verify suitability.</p>"""
        
    # Questions about prizes and rewards
    if any(word in message_lower for word in ['prize', 'reward', 'winning', 'trophy', 'money']):
        return """<p>For tournament prizes and rewards:</p>
        
        <p><b>1.</b> Budget appropriately: Typically 50-70% of entry fees go to prize pool</p>
        <p><b>2.</b> Distribution: Common splits are 60/30/10 for 1st/2nd/3rd places</p>
        <p><b>3.</b> Trophy options: Physical trophies, medals, certificates, or digital badges</p>
        <p><b>4.</b> Sponsor prizes: Consider product donations from relevant sponsors</p>
        <p><b>5.</b> Recognition: Plan for awards ceremony and winner announcements</p>
        
        <p>Clearly communicate prize structure to participants before registration.</p>"""
        
    # Questions about promotion and marketing
    if any(word in message_lower for word in ['promote', 'marketing', 'advertise', 'announcement', 'invite']):
        return """<p>To promote your tournament effectively:</p>
        
        <p><b>1.</b> Create event pages on social media and gaming platforms</p>
        <p><b>2.</b> Design eye-catching graphics with key details (date, location, prizes)</p>
        <p><b>3.</b> Contact relevant communities, clubs, and organizations</p>
        <p><b>4.</b> Consider early-bird registration discounts to build momentum</p>
        <p><b>5.</b> Partner with sponsors for cross-promotion opportunities</p>
        
        <p>Start promotion at least 1-2 months before registration deadline.</p>"""
    
    # Check for general health improvement questions
    if any(word in message_lower for word in ['health', 'healthy', 'improve', 'better', 'wellness']):
        return """<p>Improving your overall health involves a comprehensive approach across multiple dimensions:</p>
        
        <p><b>Physical Health Fundamentals:</b></p>
        <ul>
            <li><b>Regular exercise:</b> Aim for 150+ minutes of moderate activity weekly, combining cardio, strength, and flexibility training</li>
            <li><b>Balanced nutrition:</b> Focus on whole foods, adequate protein, fruits, vegetables, healthy fats, and complex carbs</li>
            <li><b>Quality sleep:</b> Prioritize 7-9 hours of consistent, quality sleep for recovery and hormonal balance</li>
            <li><b>Hydration:</b> Consume adequate water (typically 2-3 liters daily) adjusted for activity level and climate</li>
            <li><b>Regular check-ups:</b> Schedule preventative health screenings and maintain dental/vision care</li>
        </ul>
        
        <p><b>Mental & Emotional Wellbeing:</b></p>
        <ul>
            <li><b>Stress management:</b> Incorporate meditation, deep breathing, or mindfulness practices</li>
            <li><b>Social connections:</b> Maintain meaningful relationships and community engagement</li>
            <li><b>Cognitive stimulation:</b> Challenge your mind with learning, puzzles, and new skills</li>
            <li><b>Emotional regulation:</b> Develop healthy coping strategies for difficult emotions</li>
            <li><b>Digital detox:</b> Set boundaries with technology and prioritize screen-free time</li>
        </ul>
        
        <p><b>Lifestyle Optimization:</b></p>
        <ul>
            <li><b>Consistency over intensity:</b> Build sustainable habits rather than pursuing extreme changes</li>
            <li><b>Environmental awareness:</b> Minimize exposure to toxins, pollutants, and harmful substances</li>
            <li><b>Work-life balance:</b> Set boundaries to prevent burnout and prioritize personal time</li>
            <li><b>Measurable goals:</b> Track progress with specific health markers relevant to your priorities</li>
            <li><b>Continuous learning:</b> Stay informed about health research while avoiding fads</li>
        </ul>
        
        <p>The most effective approach is starting with 1-2 small changes in each area and gradually building upon them as they become habitual, rather than attempting a complete lifestyle overhaul all at once.</p>"""
    
    # Default response for sports-related queries that don't match specific patterns
    return """<p>For optimal sports performance, focus on these key areas:</p>
    
    <p><b>1.</b> Performance assessment: Establish baselines and track progress with relevant metrics</p>
    <p><b>2.</b> Training optimization: Structure workouts based on evidence-based principles</p>
    <p><b>3.</b> Recovery strategies: Implement proper nutrition, sleep, and active recovery techniques</p>
    <p><b>4.</b> Technical development: Refine sport-specific skills and movement patterns</p>
    <p><b>5.</b> Mental performance: Enhance focus, confidence, and competitive mindset</p>
    <p><b>6.</b> Data analysis: Use performance data to guide training adjustments</p>
    
    <p>What specific aspect of sports performance can I help you with today?</p>"""

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('public', 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chat interactions"""
    try:
        data = request.json
        message = data.get('message', '')
        response = handle_chat_request(message)
        return jsonify({"response": response})
    except Exception as e:
        print(f"Error processing chat request: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

if __name__ == '__main__':
    print(f"SportsAnalytica Performance Analysis Bot running on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
