from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import re
from datetime import datetime
import uuid
from kerykeion import AstrologicalSubject, NatalAspects

app = Flask(__name__)
app.secret_key = 'oracool-hackathon-secret-key-2024'
CORS(app)

users = {}
conversations = {}

SIGN_FULL_NAMES = {
    'Ari': 'Aries', 'Tau': 'Taurus', 'Gem': 'Gemini', 'Can': 'Cancer',
    'Leo': 'Leo', 'Vir': 'Virgo', 'Lib': 'Libra', 'Sco': 'Scorpio',
    'Sag': 'Sagittarius', 'Cap': 'Capricorn', 'Aqu': 'Aquarius', 'Pis': 'Pisces'
}

HOUSE_NUMBERS = {
    'First_House': '1st', 'Second_House': '2nd', 'Third_House': '3rd',
    'Fourth_House': '4th', 'Fifth_House': '5th', 'Sixth_House': '6th',
    'Seventh_House': '7th', 'Eighth_House': '8th', 'Ninth_House': '9th',
    'Tenth_House': '10th', 'Eleventh_House': '11th', 'Twelfth_House': '12th'
}


def format_position(degrees):
    d = int(degrees)
    m = int((degrees - d) * 60)
    return f"{d}°{m:02d}'"


SIGN_SYMBOLS = {
    'Aries': '\u2648', 'Taurus': '\u2649', 'Gemini': '\u264a', 'Cancer': '\u264b',
    'Leo': '\u264c', 'Virgo': '\u264d', 'Libra': '\u264e', 'Scorpio': '\u264f',
    'Sagittarius': '\u2650', 'Capricorn': '\u2651', 'Aquarius': '\u2652', 'Pisces': '\u2653'
}

PLANET_SYMBOLS = {
    'Sun': '\u2609', 'Moon': '\u263d', 'Mercury': '\u263f', 'Venus': '\u2640',
    'Mars': '\u2642', 'Jupiter': '\u2643', 'Saturn': '\u2644', 'Uranus': '\u2645',
    'Neptune': '\u2646', 'Pluto': '\u2647'
}

PLANET_MEANINGS = {
    'Sun': 'Core identity & ego',
    'Moon': 'Emotions & inner self',
    'Mercury': 'Communication & thinking',
    'Venus': 'Love & values',
    'Mars': 'Drive & action',
    'Jupiter': 'Growth & expansion',
    'Saturn': 'Discipline & lessons',
    'Uranus': 'Change & innovation',
    'Neptune': 'Dreams & intuition',
    'Pluto': 'Transformation & power'
}


def compute_chart(name, year, month, day, hour, minute, city, nation=''):
    try:
        if nation:
            subject = AstrologicalSubject(name, year, month, day, hour, minute, city=city, nation=nation)
        else:
            subject = AstrologicalSubject(name, year, month, day, hour, minute, city=city)

        planet_names = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
        planets = []
        for pname in planet_names:
            p = getattr(subject, pname)
            sign = SIGN_FULL_NAMES.get(p.sign, p.sign)
            house = HOUSE_NUMBERS.get(p.house, p.house)
            pos = format_position(p.position)
            planets.append({
                'name': p.name, 'sign': sign, 'position': pos,
                'house': house, 'retrograde': p.retrograde,
                'abs_pos': p.abs_pos,
                'symbol': PLANET_SYMBOLS.get(p.name, ''),
                'sign_symbol': SIGN_SYMBOLS.get(sign, ''),
                'meaning': PLANET_MEANINGS.get(p.name, '')
            })

        nn = subject.true_north_lunar_node
        nn_sign = SIGN_FULL_NAMES.get(nn.sign, nn.sign)
        nn_house = HOUSE_NUMBERS.get(nn.house, nn.house)
        nn_pos = format_position(nn.position)

        asc = subject.first_house
        mc = subject.tenth_house
        asc_sign = SIGN_FULL_NAMES.get(asc.sign, asc.sign)
        mc_sign = SIGN_FULL_NAMES.get(mc.sign, mc.sign)

        aspects_obj = NatalAspects(subject)
        aspect_list_text = []
        aspect_list_json = []
        for a in aspects_obj.relevant_aspects:
            if a.p1_name in ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto'] and \
               a.p2_name in ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto']:
                p1_data = next((p for p in planets if p['name'] == a.p1_name), None)
                p2_data = next((p for p in planets if p['name'] == a.p2_name), None)
                aspect_name = a.aspect.replace('_', ' ')
                orbit_str = f"{a.orbit:.1f}"
                detail = ""
                if p1_data and p2_data:
                    detail = f" ({p1_data['house']} House / {p2_data['house']} House)"
                aspect_list_text.append(f"- {a.p1_name} {aspect_name} {a.p2_name}{detail}, orb {orbit_str}°")
                aspect_list_json.append({
                    'planet1': a.p1_name,
                    'planet2': a.p2_name,
                    'aspect': aspect_name,
                    'orb': round(a.orbit, 1)
                })

        lines = []
        lines.append(f"BIRTH CHART FOR: {name}")
        lines.append(f"Born: {month}/{day}/{year} at {hour:02d}:{minute:02d}")
        lines.append(f"Location: {city}")
        lines.append("")
        lines.append("PLANETARY PLACEMENTS:")
        lines.append("")
        for p in planets:
            retro_str = ' Retrograde' if p['retrograde'] else ''
            lines.append(f"{p['name']} in {p['sign']} ({p['position']}) in {p['house']} House{retro_str}")
        lines.append(f"North Node in {nn_sign} ({nn_pos}) in {nn_house} House")
        lines.append("")
        lines.append(f"Rising Sign / Ascendant: {asc_sign} ({format_position(asc.position)})")
        lines.append(f"Midheaven (MC): {mc_sign} ({format_position(mc.position)}) — 10th House")
        lines.append("")
        lines.append("KEY ASPECTS:")
        for asp in aspect_list_text[:15]:
            lines.append(asp)

        house_groups = {}
        for p in planets:
            h = p['house']
            if h not in house_groups:
                house_groups[h] = []
            house_groups[h].append(p['name'])
        stelliums = {h: ps for h, ps in house_groups.items() if len(ps) >= 3}
        if stelliums:
            lines.append("")
            lines.append("HOUSE EMPHASIS:")
            for h, ps in stelliums.items():
                lines.append(f"- Stellium in {h} House ({', '.join(ps)}): Multiple planets concentrate energy here")
            for h, ps in house_groups.items():
                if len(ps) == 2:
                    lines.append(f"- {h} House ({', '.join(ps)}): Significant focus area")

        chart_text = "\n".join(lines)

        chart_json = {
            'planets': [{k: v for k, v in p.items() if k != 'abs_pos'} for p in planets],
            'northNode': {'sign': nn_sign, 'position': nn_pos, 'house': nn_house},
            'ascendant': {'sign': asc_sign, 'position': format_position(asc.position), 'symbol': SIGN_SYMBOLS.get(asc_sign, '')},
            'midheaven': {'sign': mc_sign, 'position': format_position(mc.position), 'symbol': SIGN_SYMBOLS.get(mc_sign, '')},
            'aspects': aspect_list_json[:15],
        }

        print(f"Chart computed successfully for {name}: {len(chart_text)} chars, {len(aspect_list_text)} aspects")
        return chart_text, chart_json

    except Exception as e:
        print(f"Error computing chart: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


SAMPLE_CHARTS = {
    "sarah": """PROFILE: Sarah (Burned Out Tech Worker)
Birth: March 15, 1995, 2:30 PM, San Francisco, CA

PLANETARY PLACEMENTS:

Sun in Pisces (24°52') in 8th House
Moon in Virgo (10°28') in 2nd House
Mercury in Pisces (1°29') in 8th House
Venus in Aquarius (15°21') in 7th House
Mars in Leo (13°38' Retrograde) in 1st House
Jupiter in Sagittarius (14°05') in 5th House
Saturn in Pisces (8°12') in 8th House
Uranus in Capricorn (27°33') in 6th House
Neptune in Capricorn (24°55') in 6th House
Pluto in Scorpio (29°50') in 4th House
North Node in Scorpio (5°18') in 4th House

Rising Sign: Leo (10°02')
Midheaven: Taurus (4°30') — 10th House

KEY ASPECTS:
- Sun conjunct Saturn (8th House): Heavy sense of duty, feels burdened by expectations, chronic overwork pattern
- Sun conjunct Mercury (8th House): Intuitive processing, deep psychological insight
- Venus opposite Mars: Tension between need for independence and asserting boundaries
- Moon opposite Mercury: Conflict between logical analysis and emotional needs
- Moon trine Pluto: Deep emotional resilience, transformative inner life
- Mars square Pluto: Intense drive that can become self-destructive under stress
- Jupiter trine Mars: Natural leadership and creative confidence when aligned
- Saturn square Uranus: Tension between tradition/stability and need for freedom/change
- Neptune conjunct Uranus (6th House): Idealistic about work, may blur boundaries around health and daily routine

HOUSE EMPHASIS:
- Strong 8th House (Sun, Mercury, Saturn): Deep transformation themes, psychology, shared resources, crisis management
- 6th House (Uranus, Neptune): Health and work routines need conscious attention, burnout risk
- 1st House Mars Retrograde: Struggles to assert personal needs, projects strength while feeling depleted

CURRENT TRANSITS (2025-2026):
- Saturn transiting 7th House: Relationship structures being tested, boundaries with partners
- Pluto entering Aquarius: Transforming social identity and long-term goals
- Jupiter in Gemini transiting 11th House: Expanding social networks, new community connections""",

    "alex": """PROFILE: Alex (Creative Anxious)
Birth: July 22, 1998, 8:15 AM, New York, NY

PLANETARY PLACEMENTS:

Sun in Cancer (29°29') in 12th House
Moon in Cancer (16°16') in 12th House
Mercury in Leo (25°21') in 1st House
Venus in Cancer (3°27') in 12th House
Mars in Cancer (10°49') in 12th House
Jupiter in Pisces (21°08') in 8th House
Saturn in Taurus (2°45' Retrograde) in 10th House
Uranus in Aquarius (10°33') in 7th House
Neptune in Aquarius (0°42') in 6th House
Pluto in Sagittarius (5°52') in 4th House
North Node in Virgo (12°30') in 2nd House

Rising Sign: Leo (28°14')
Midheaven: Taurus (22°10') — 10th House

KEY ASPECTS:
- Sun conjunct Moon (12th House): Deeply unified emotional identity, but hidden from the world
- Sun opposite Neptune: Dissolving boundaries, spiritual sensitivity, confusion about identity
- Moon conjunct Mars (12th House): Emotional intensity channeled inward, quick to react but suppresses it
- Moon conjunct Venus (12th House): Deep compassion, nurturing love style, self-sacrifice tendency
- Saturn square Neptune: Tension between structure/career ambition and dreams/ideals
- Jupiter trine Sun: Natural optimism and spiritual gifts, protection through intuition
- Pluto square Mars: Power struggles with anger expression, creative intensity
- Uranus opposite Mercury: Brilliant but scattered thinking, needs unconventional communication outlets
- North Node in Virgo (2nd House): Life path toward practical skills, self-worth, and grounded routines

HOUSE EMPHASIS:
- Stellium in 12th House (Sun, Moon, Venus, Mars): Rich inner world, strong intuition, needs solitude, spiritual gifts but risk of isolation
- 10th House Saturn Retrograde: Career path feels delayed or uncertain, fear of public visibility
- 4th House Pluto: Family dynamics deeply transformative, home is both sanctuary and trigger

CURRENT TRANSITS (2025-2026):
- Saturn transiting Pisces through 8th House: Deep psychological restructuring, facing fears
- Neptune transiting Pisces through 8th House: Spiritual awakening through crisis or loss
- Jupiter in Gemini transiting 11th House: New creative communities and friendships emerging""",

    "jordan": """PROFILE: Jordan (Career Confused)
Birth: November 3, 2000, 11:45 PM, Austin, TX

PLANETARY PLACEMENTS:

Sun in Scorpio (12°06') in 4th House
Moon in Aquarius (11°20') in 7th House
Mercury in Scorpio (1°22' Retrograde) in 4th House
Venus in Sagittarius (19°20') in 5th House
Mars in Libra (0°05') in 3rd House
Jupiter in Gemini (8°44' Retrograde) in 11th House
Saturn in Taurus (18°15') in 10th House
Uranus in Aquarius (16°55') in 7th House
Neptune in Aquarius (3°48') in 7th House
Pluto in Sagittarius (11°22') in 5th House
North Node in Cancer (15°40') in 12th House

Rising Sign: Leo (10°30')
Midheaven: Taurus (0°15') — 10th House

KEY ASPECTS:
- Sun square Moon: Internal conflict between emotional depth (Scorpio) and intellectual detachment (Aquarius)
- Sun trine Jupiter: Natural luck and expansion, philosophical mind, big-picture thinking
- Moon conjunct Uranus (7th House): Sudden emotional changes, need for independence, unconventional relationship needs
- Moon conjunct Neptune (7th House): Idealizes partners, sensitive to others' energy, empathic
- Mercury Retrograde conjunct Sun: Deep thinker who constantly re-evaluates, revisits past decisions
- Venus conjunct Pluto (5th House): Intense creative passion, all-or-nothing in romance and art
- Saturn in Taurus (10th House): Career path feels slow, pressure to build something lasting and practical
- Mars square Saturn: Frustration between desire to act and feeling blocked, career impatience
- Jupiter Retrograde in 11th House: Re-evaluating social groups, delayed but eventual success in community

HOUSE EMPHASIS:
- Strong 4th House (Sun, Mercury): Identity rooted in family, home, and inner foundations
- 7th House (Moon, Uranus, Neptune): Relationships are a major life theme, unconventional partnerships
- 5th House (Venus, Pluto): Creative expression and romance are transformative
- 10th House Saturn: Career requires patience, discipline, and long-term commitment

CURRENT TRANSITS (2025-2026):
- Saturn transiting Pisces through 8th House: Financial and emotional restructuring
- Pluto entering Aquarius transiting 7th House: Transformative relationship dynamics
- Jupiter in Gemini activating 11th House: Social expansion, new networks, career opportunities through community"""
}

DEFAULT_CHART = SAMPLE_CHARTS["sarah"]


def get_minimax_response(user_message, chart_data, conversation_history):
    system_prompt = f"""You are Oracool, an expert astrologer and mental wellness guide. You deliver deep, structured astrological analyses combined with psychological insight.

USER'S BIRTH CHART DATA:
{chart_data}

YOUR RESPONSE FORMAT:
You must produce detailed, structured readings using numbered sections. Follow this format precisely:

1️⃣ Section Title
Core themes
Theme1 · Theme2 · Theme3 · Theme4

Planet in Sign in House
Interpretation of what this means for the person.

● Bullet point insight
● Bullet point insight
● Bullet point insight

Planet aspect Planet
What this aspect activates.

● Bullet point insight
● Bullet point insight

So in short:
A concise summary sentence.

2️⃣ Next Section Title
Continue with the same structured format.

RULES FOR ANALYSIS:

1. ALWAYS reference SPECIFIC placements from their chart with exact degrees and houses
   - "Venus in Aquarius (15°21') in the 7th House" — not vague references
   - Pull directly from their chart data above

2. Organize into 3-5 NUMBERED SECTIONS relevant to the user's question
   - For relationships: Relationship Style, Partner Profile, Timing Activation
   - For career: Career Identity, Work Style, Growth Path, Timing
   - For anxiety: Emotional Patterns, Stress Triggers, Coping Architecture, Healing Path
   - For life purpose: Core Identity, Life Direction, Soul Mission, Current Activation

3. Each section must include:
   - A "Core themes" line with key words separated by · 
   - Specific planetary placements with interpretations
   - Bullet points (●) with direct, clear insights
   - Aspect interpretations showing how planets interact

4. Include a TIMING section using their current transits
   - Break into time windows (e.g., "Nov 2025 – Feb 2026")
   - Describe what each window activates
   - Give concrete examples of what may unfold

5. Use direct, confident language:
   - "You are not wired for lukewarm situations."
   - "This is transformative love. Not light romance."
   - "You cannot ignore relationship questions anymore."
   - Short declarative sentences. Not wishy-washy.

6. End sections with "So in short:" summaries when appropriate

TONE:
- Direct and confident, like a master astrologer giving a private reading
- Use "you" language throughout
- No hedging or excessive disclaimers
- Psychologically insightful — connect placements to real behavioral patterns
- Empowering but honest — tell them what they need to hear

WHAT TO AVOID:
- Generic horoscope content that could apply to anyone
- Medical diagnoses
- Vague, uncommitted language ("maybe", "perhaps", "it could be")
- Overly long paragraphs — use bullets and short statements
- Ignoring their actual chart data

RESPONSE LENGTH:
- Produce comprehensive readings: 400-800 words minimum
- Use all relevant placements from their chart
- Do not cut corners — the user wants DEPTH"""

    messages = [{"role": "system", "content": system_prompt}]

    for msg in conversation_history:
        messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    try:
        print(f"Calling MiniMax API for question: {user_message[:50]}...")

        response = requests.post(
            "https://api.minimax.io/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ.get('MINIMAX_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "MiniMax-M2.1",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95
            },
            timeout=120
        )

        data = response.json()
        if response.status_code == 200 and 'choices' in data:
            ai_response = data['choices'][0]['message']['content']
            ai_response = re.sub(r'<think>.*?</think>\s*', '', ai_response, flags=re.DOTALL)
            print(f"MiniMax response received: {len(ai_response)} characters")
            return ai_response
        else:
            print(f"MiniMax API error: {response.status_code}")
            print(f"Response: {response.text}")
            return get_fallback_response(chart_data)

    except requests.exceptions.Timeout:
        print("MiniMax API timeout")
        return get_fallback_response(chart_data)
    except Exception as e:
        print(f"Error calling MiniMax: {str(e)}")
        return get_fallback_response(chart_data)


def get_fallback_response(chart_data):
    return """I'm having a moment of connection difficulty, but I'm still here for you!

Based on your birth chart, I can see you have deep emotional sensitivity and natural intuition. Your chart shows a beautiful capacity for understanding yourself and others.

Here are some practices that align with your astrological profile:

**Grounding Practice:** Take 5 minutes right now to sit quietly and observe your breath. Notice how you're feeling without trying to change it.

**Journaling Prompt:** Write about what you're experiencing emotionally today. Your chart suggests you process feelings deeply through reflection.

**Gentle Movement:** Try some stretching, yoga, or a mindful walk. Moving your body helps process emotional energy.

Let's try your question again - I'd love to give you more personalized guidance! Ask me anything about anxiety, career, relationships, or life purpose."""


@app.route('/')
def index():
    return render_template('index.html')


QUIZ_PROFILE_MAP = {
    "career_pressure": "sarah",
    "overwork": "sarah",
    "rest": "sarah",
    "emotional_overwhelm": "alex",
    "withdraw": "alex",
    "expression": "alex",
    "direction_confusion": "jordan",
    "overthink": "jordan",
    "clarity": "jordan",
}


def map_quiz_to_profile(quiz_answers):
    scores = {"sarah": 0, "alex": 0, "jordan": 0}
    for answer in quiz_answers.values():
        profile = QUIZ_PROFILE_MAP.get(answer)
        if profile:
            scores[profile] += 1
    return max(scores, key=scores.get)


@app.route('/api/create-user', methods=['POST'])
def create_user():
    data = request.json

    user_id = str(uuid.uuid4())

    birth_date = data.get('birthDate', '')
    birth_time = data.get('birthTime', '12:00')
    birth_city = data.get('birthCity', '')

    print(f"Creating user: {user_id}")
    print(f"   Birth: {birth_date} at {birth_time}")
    print(f"   Location: {birth_city}")

    quiz_answers = data.get('quizAnswers', {})
    if not quiz_answers:
        print(f"   No quiz answers provided, using default profile")
    profile_key = map_quiz_to_profile(quiz_answers)

    chart_data = None
    chart_visual = None
    if birth_date and birth_city:
        try:
            parts = birth_date.split('-')
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            time_parts = birth_time.split(':')
            hour, minute = int(time_parts[0]), int(time_parts[1])

            user_name = f"User_{user_id[:8]}"
            chart_data, chart_visual = compute_chart(user_name, year, month, day, hour, minute, birth_city)
        except Exception as e:
            print(f"   Chart computation failed: {str(e)}")

    if not chart_data:
        print(f"   Falling back to sample chart for profile: {profile_key}")
        chart_data = SAMPLE_CHARTS.get(profile_key, DEFAULT_CHART)

    print(f"   Quiz answers: {quiz_answers}")
    print(f"   Matched profile: {profile_key}")

    users[user_id] = {
        'birthDate': birth_date,
        'birthTime': birth_time,
        'birthCity': birth_city,
        'profile': profile_key,
        'chartData': chart_data,
        'chartVisual': chart_visual,
        'createdAt': datetime.now().isoformat()
    }

    conversations[user_id] = []

    print(f"User created successfully: {user_id}")

    return jsonify({
        'userId': user_id,
        'chartData': chart_data,
        'chartVisual': chart_visual
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('userId')
    message = data.get('message')

    if not user_id or user_id not in users:
        print(f"Invalid user ID: {user_id}")
        return jsonify({'error': 'Invalid user ID'}), 400

    if not message or not message.strip():
        print(f"Empty message from user: {user_id}")
        return jsonify({'error': 'Message is required'}), 400

    print(f"User {user_id[:8]}... asked: {message[:50]}...")

    user = users[user_id]
    chart_data = user['chartData']

    conversation_history = conversations[user_id]

    ai_response = get_minimax_response(message, chart_data, conversation_history)

    conversations[user_id].append({"role": "user", "content": message})
    conversations[user_id].append({"role": "assistant", "content": ai_response})

    print(f"Response sent to user: {len(ai_response)} characters")

    return jsonify({
        'response': ai_response
    })


@app.route('/api/messages/<user_id>', methods=['GET'])
def get_messages(user_id):
    if user_id not in conversations:
        return jsonify({'messages': []})

    return jsonify({
        'messages': conversations[user_id]
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'totalUsers': len(users),
        'activeConversations': len(conversations)
    })


@app.route('/api/debug/<user_id>', methods=['GET'])
def debug_user(user_id):
    if user_id not in users:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user': users[user_id],
        'messageCount': len(conversations.get(user_id, []))
    })


if __name__ == '__main__':
    print("=" * 50)
    print("ORACOOL BACKEND STARTING...")
    print("=" * 50)
    print(f"Flask app initialized")
    print(f"MiniMax API key: {'SET' if os.environ.get('MINIMAX_API_KEY') else 'MISSING!'}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('REPL_SLUG') is not None)
