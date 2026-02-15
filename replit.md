# Oracool — Astrological Mental Wellness Chatbot

## Overview
A mental wellness chatbot combining astrological insights with AI-powered guidance via MiniMax API. Users take a 3-question archetype quiz that maps them to one of three astrological profiles, then chat with the AI for personalized advice.

## Project Architecture
- `app.py` — Flask backend: routes, MiniMax API integration, quiz-to-profile mapping, sample charts
- `templates/index.html` — Single-page frontend with quiz flow, birth info entry, planet dashboard, and chat interface (all CSS/JS inline)
- `static/` — Static assets (crystal ball logo, favicon)
- `pyproject.toml` — Python dependencies (Flask, requests)

## Key Features
- Real birth chart computation using Kerykeion (Swiss Ephemeris / NASA JPL precision)
- Planetary placements, aspects, houses, nodes, ascendant, and midheaven calculated from actual birth data
- Visual planet summary dashboard with planet cards, retrograde badges, colored aspect indicators, ASC/MC highlights
- Collapsible planet summary bar in chat for quick reference
- 3-question archetype quiz for psychological context (fallback to sample charts if computation fails)
- MiniMax M2.1 API for AI chat responses
- Typing indicators, suggestion chips, message history in chat UI
- Null-safe: if chart computation fails, skips dashboard and goes straight to chat

## Running
- The app runs on port 5000 with `python app.py`
- Debug mode enabled for development
- Requires MINIMAX_API_KEY secret

## AI Response Format
- Structured readings with numbered sections (1️⃣ 2️⃣ 3️⃣), core themes, specific planetary placements with degrees, bullet-point insights, aspect interpretations, and timing activation windows
- max_tokens: 4096, API timeout: 120s for comprehensive responses
- Frontend renders markdown formatting (headers, bold, bullets, horizontal rules) via formatMarkdown()

## UI Design
- Indigo-to-purple-to-pink gradient background with floating blurred orbs and twinkling star particles
- Crystal ball logo (`/static/oracool-crystal-logo.png`) with glow drop-shadow and floating animation
- Fascinate font for "Oracool" title, Work Sans for body text
- Star constellation SVG loading animation ("Aligning the stars...") shown during profile creation
- Chat bubbles with purple/pink gradient star avatar for assistant messages
- Round gradient send button with arrow icon
- Pill-shaped suggestion chips
- Glass-morphism cards with `rgba(255,255,255,0.08)` backgrounds and backdrop blur

## Recent Changes
- 2026-02-14: Integrated Cosmic Blueprint visual design (crystal logo, Fascinate font, gradient bg, floating orbs, twinkling stars, constellation loading animation, polished chat UI with avatars)
- 2026-02-14: Added visual planet summary dashboard with planet cards, aspect indicators, ASC/MC highlights, collapsible summary bar in chat
- 2026-02-14: Backend compute_chart now returns chart_json with planet symbols, sign symbols, meanings for visual rendering
- 2026-02-14: Overhauled system prompt and chart profiles for deep structured astrological readings
- 2026-02-14: Added markdown rendering to frontend for formatted AI responses
- 2026-02-14: Replaced dropdown profile selector with engaging archetype quiz
- 2026-02-14: Added quiz-to-profile mapping backend logic with validation
- 2026-02-14: Initial project setup with Python 3.11 + Flask + MiniMax API
