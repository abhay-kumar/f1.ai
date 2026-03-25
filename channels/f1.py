"""
F1 Burnouts channel configuration.

All F1-specific constants extracted from the pipeline modules.
"""

CHANNEL = {
    # =========================================================================
    # IDENTITY
    # =========================================================================
    "id": "f1",
    "name": "F1 Burnouts",
    "name_upper": "F1 BURNOUTS",
    "handle": "@f1burnouts",
    "category_id": "17",  # YouTube: Sports
    "default_subreddit": "formula1",
    "search_context": "F1 2024",  # appended to footage search queries
    "created_with": "Created with iti.ai",

    # =========================================================================
    # BRANDING COLORS
    # =========================================================================
    "brand_color": "#E8002D",  # Ferrari red
    "accent_color": "#FF8000",  # Papaya orange
    "default_text_color": "#FFFFFF",
    "cover_bg_color": "0x1a1a2e",  # Dark navy (podcast cover)
    "cover_accent_color": "0xff8000",  # Orange (podcast cover)

    # =========================================================================
    # FONTS (relative to channel asset dir)
    # =========================================================================
    "font_bold": "fonts/Formula1-Bold.ttf",
    "font_regular": "fonts/TitilliumWeb-Black.ttf",

    # =========================================================================
    # ASSETS (relative to channel asset dir)
    # =========================================================================
    "logo": "assets/logo/logo.png",
    "logo_jpg": "assets/logo/logo.jpg",
    "logo_video": "assets/logo/logo.mp4",
    "logo_video_2": "assets/logo/logo2.mp4",
    "intro_voiceover": "audio/intro_voiceover.mp3",
    "outro_audio": "audio/outro_longform.mp3",
    "f1sound": "audio/f1sound.mp3",
    "background_music": "music/background.mp3",
    "background_music_longform": "music/f1_cinematic_rock.mp3",
    "background_music_invincible": "music/f1_invincible.mp3",
    "daily_news": {
        "intro": "assets/daily-news/intro.mp4",
        "outro": "assets/daily-news/outro.mp4",
        "outro_cta": "assets/daily-news/outro_cta.mp4",
        "logo": "assets/daily-news/logo.jpg",
        "logo_voice": "assets/daily-news/logo_voice.mp3",
        "logo_zoom": "assets/daily-news/logo_zoom.mp4",
        "logo_zoom_16x9": "assets/daily-news/logo_zoom_16x9.mp4",
        "f1sound_2x": "assets/daily-news/f1sound_2x.mp3",
        "logo_with_f1sound": "assets/daily-news/logo_with_f1sound.mp3",
    },

    # =========================================================================
    # ENTITY COLORS (team/driver name → hex color)
    # =========================================================================
    "entity_colors": {
        # Current teams (2026 grid)
        "red bull": "#3671C6",
        "redbull": "#3671C6",
        "mclaren": "#FF8000",
        "ferrari": "#E8002D",
        "mercedes": "#27F4D2",
        "aston martin": "#229971",
        "alpine": "#FF87BC",
        "williams": "#64C4FF",
        "haas": "#B6BABD",
        "cadillac": "#C4A747",
        "audi": "#BB0A1E",
        "racing bulls": "#6692FF",
        # Drivers (mapped to their 2026 teams)
        "vettel": "#3671C6",
        "webber": "#3671C6",
        "norris": "#FF8000",
        "piastri": "#FF8000",
        "verstappen": "#3671C6",
        "hadjar": "#3671C6",
        "hamilton": "#E8002D",
        "leclerc": "#E8002D",
        "alonso": "#229971",
        "russell": "#27F4D2",
        "antonelli": "#27F4D2",
        "perez": "#C4A747",
        "bottas": "#C4A747",
        "ocon": "#B6BABD",
        "bortoleto": "#BB0A1E",
        "hulkenberg": "#BB0A1E",
        "colapinto": "#FF87BC",
        "lawson": "#6692FF",
        "palou": "#FF8000",
    },

    # =========================================================================
    # OFFICIAL YOUTUBE CHANNELS (prioritized in footage search)
    # =========================================================================
    "official_channels": [
        "FORMULA 1",
        "Formula 1",
        "F1",
        "Sky Sports F1",
        "Red Bull Racing",
        "Mercedes-AMG PETRONAS F1 Team",
        "Scuderia Ferrari",
        "McLaren",
        "Aston Martin Aramco F1 Team",
        "BWT Alpine F1 Team",
        "Williams Racing",
    ],

    # =========================================================================
    # UPLOAD METADATA
    # =========================================================================
    "base_tags": [
        "F1", "Formula1", "Formula 1", "Racing", "Motorsport", "Grand Prix",
    ],
    "base_hashtags": [
        "#F1", "#Formula1", "#Reels", "#FormulaOne", "#Racing",
    ],
    "description_hashtags": "#F1 #Formula1 #Racing #Motorsport",
    "shorts_hashtags": "#F1 #Formula1 #Shorts",

    # Disclaimers
    "disclaimer_shorts": (
        "\n───────────────────────────────────────────────────────────\n"
        "DISCLAIMER: This video is unofficial fan content and is not\n"
        "associated with, endorsed by, or affiliated with Formula 1,\n"
        "FIA, or Formula One Management (FOM). All F1-related trademarks\n"
        "and imagery are property of their respective owners. Created\n"
        "for commentary and entertainment under fair use principles.\n"
        "\n"
        "For official F1 content: https://www.formula1.com\n"
        "───────────────────────────────────────────────────────────\n"
    ),
    "disclaimer_longform": (
        "\n───────────────────────────────────────────────────────────────────\n"
        "\u26a0\ufe0f DISCLAIMER\n"
        "\n"
        "This video is unofficial fan content created for commentary,\n"
        "education, and entertainment purposes. It is not associated with,\n"
        "endorsed by, or affiliated with:\n"
        "\u2022 Formula 1 / Formula One Management (FOM)\n"
        "\u2022 F\u00e9d\u00e9ration Internationale de l\u2019Automobile (FIA)\n"
        "\u2022 Any Formula 1 team or driver\n"
        "\n"
        "All F1-related trademarks, footage, and imagery are property of\n"
        "their respective owners and are used here under fair use for\n"
        "transformative commentary.\n"
        "\n"
        "For official F1 content: https://www.formula1.com\n"
        "For official F1 TV: https://f1tv.formula1.com\n"
        "───────────────────────────────────────────────────────────────────\n"
    ),
    "disclaimer_instagram": (
        "This is unofficial fan content \u2014 not affiliated with Formula 1, FIA, or FOM. "
        "Created for commentary and entertainment."
    ),
    "about_video": "An in-depth look at Formula 1 history, statistics, and stories.",

    # =========================================================================
    # TAG DETECTION (keyword → tag list, for auto-tagging uploads)
    # =========================================================================
    "driver_tags": {
        "verstappen": ["Verstappen", "Max Verstappen", "Red Bull"],
        "hamilton": ["Hamilton", "Lewis Hamilton"],
        "leclerc": ["Leclerc", "Charles Leclerc", "Ferrari"],
        "norris": ["Norris", "Lando Norris", "McLaren"],
        "sainz": ["Sainz", "Carlos Sainz"],
        "alonso": ["Alonso", "Fernando Alonso", "Aston Martin"],
        "piastri": ["Piastri", "Oscar Piastri"],
        "russell": ["Russell", "George Russell"],
        "vettel": ["Vettel", "Sebastian Vettel"],
        "schumacher": ["Schumacher", "Michael Schumacher"],
        "senna": ["Senna", "Ayrton Senna"],
        "prost": ["Prost", "Alain Prost"],
        "webber": ["Webber", "Mark Webber"],
        "ricciardo": ["Ricciardo", "Daniel Ricciardo"],
        "raikkonen": ["Raikkonen", "Kimi Raikkonen"],
        "bottas": ["Bottas", "Valtteri Bottas"],
        "perez": ["Perez", "Sergio Perez"],
        "ocon": ["Ocon", "Esteban Ocon"],
        "hulkenberg": ["Hulkenberg", "Nico Hulkenberg"],
        "antonelli": ["Antonelli", "Kimi Antonelli"],
        "hadjar": ["Hadjar", "Isack Hadjar"],
        "newey": ["Adrian Newey", "Newey"],
        "horner": ["Christian Horner", "Horner"],
        "toto": ["Toto Wolff", "Wolff"],
        "vasseur": ["Fred Vasseur", "Vasseur"],
        "lauda": ["Lauda", "Niki Lauda"],
        "brabham": ["Brabham", "Jack Brabham"],
        "andretti": ["Andretti", "Mario Andretti"],
        "maylander": ["Maylander", "Bernd Maylander", "Safety Car"],
    },
    "team_tags": {
        "red bull": ["Red Bull", "Red Bull Racing", "Red Bull F1"],
        "mclaren": ["McLaren", "McLaren F1 Team"],
        "ferrari": ["Ferrari", "Scuderia Ferrari"],
        "mercedes": ["Mercedes", "Mercedes AMG"],
        "aston martin": ["Aston Martin", "Aston Martin F1"],
        "williams": ["Williams", "Williams Racing"],
        "alpine": ["Alpine", "Alpine F1"],
        "haas": ["Haas", "Haas F1"],
        "cadillac": ["Cadillac", "Cadillac F1"],
        "audi": ["Audi", "Audi F1"],
        "racing bulls": ["Racing Bulls"],
    },
    "topic_tags": {
        "champion": ["World Championship", "F1 Champion"],
        "race win": ["Race Winner", "Victory"],
        "pole position": ["Pole Position", "Qualifying"],
        "rivalry": ["F1 Rivalry", "Racing Rivalry"],
        "history": ["F1 History", "Racing History"],
        "legend": ["F1 Legend", "Racing Legend"],
        "debut": ["F1 Debut", "Rookie"],
        "retirement": ["F1 Retirement"],
        "safety": ["F1 Safety", "Safety Car"],
        "testing": ["F1 Testing", "Pre-Season"],
        "regulation": ["F1 Regulations", "F1 Rules"],
        "crash": ["F1 Crash", "Incident"],
        "overtake": ["Overtake", "Overtaking"],
        "pit stop": ["Pit Stop", "Strategy"],
        "2026": ["F1 2026", "2026 Season"],
    },
    "driver_hashtags": {
        "vettel": "#Vettel",
        "webber": "#Webber",
        "norris": "#LandoNorris",
        "piastri": "#Piastri",
        "verstappen": "#Verstappen",
        "hamilton": "#LewisHamilton",
        "leclerc": "#Leclerc",
        "alonso": "#Alonso",
    },
    "team_hashtags": {
        "red bull": "#RedBull",
        "mclaren": "#McLaren",
        "ferrari": "#Ferrari",
        "mercedes": "#Mercedes",
        "aston martin": "#AstonMartin",
        "alpine": "#Alpine",
        "williams": "#Williams",
        "haas": "#Haas",
    },

    # =========================================================================
    # KNOWN ENTITIES (for content detection + visual routing)
    # =========================================================================
    "known_people": {
        "verstappen": "Max Verstappen",
        "hamilton": "Lewis Hamilton",
        "leclerc": "Charles Leclerc",
        "norris": "Lando Norris",
        "sainz": "Carlos Sainz",
        "russell": "George Russell",
        "perez": "Sergio Perez",
        "alonso": "Fernando Alonso",
        "stroll": "Lance Stroll",
        "ocon": "Esteban Ocon",
        "gasly": "Pierre Gasly",
        "tsunoda": "Yuki Tsunoda",
        "ricciardo": "Daniel Ricciardo",
        "bottas": "Valtteri Bottas",
        "piastri": "Oscar Piastri",
        "lawson": "Liam Lawson",
        "antonelli": "Kimi Antonelli",
        "bearman": "Oliver Bearman",
        "schumacher": "Michael Schumacher",
        "senna": "Ayrton Senna",
        "vettel": "Sebastian Vettel",
        "raikkonen": "Kimi Raikkonen",
        "wolff": "Toto Wolff",
        "horner": "Christian Horner",
        "binotto": "Mattia Binotto",
        "brown": "Zak Brown",
        "newey": "Adrian Newey",
        "brawn": "Ross Brawn",
    },
    "known_teams": {
        "red bull": "Red Bull Racing",
        "mercedes": "Mercedes F1",
        "ferrari": "Scuderia Ferrari",
        "mclaren": "McLaren F1 Team",
        "alpine": "Alpine F1 Team",
        "williams": "Williams Racing",
        "haas": "Haas F1 Team",
        "rb": "RB F1 Team",
    },
    "known_partners": {
        "aramco": "Saudi Aramco",
        "shell": "Shell",
        "petronas": "Petronas",
        "bp": "BP",
        "total": "TotalEnergies",
        "gulf": "Gulf Oil",
    },

    # =========================================================================
    # KNOWLEDGE BASE (for fact checking)
    # =========================================================================
    "knowledge_base": {
        "champions": {
            "verstappen": ["2021", "2022", "2023", "2024"],
            "hamilton": ["2008", "2014", "2015", "2017", "2018", "2019", "2020"],
            "vettel": ["2010", "2011", "2012", "2013"],
            "alonso": ["2005", "2006"],
            "raikkonen": ["2007"],
            "button": ["2009"],
            "rosberg": ["2016"],
            "schumacher": ["1994", "1995", "2000", "2001", "2002", "2003", "2004"],
        },
        "teams_2024": {
            "red bull": ["verstappen", "perez"],
            "ferrari": ["leclerc", "sainz"],
            "mercedes": ["hamilton", "russell"],
            "mclaren": ["norris", "piastri"],
            "aston martin": ["alonso", "stroll"],
            "alpine": ["gasly", "ocon"],
            "williams": ["albon", "sargeant"],
            "haas": ["magnussen", "hulkenberg"],
            "kick sauber": ["bottas", "zhou"],
            "rb": ["tsunoda", "ricciardo"],
        },
        "records": {
            "most_wins": ("hamilton", 104),
            "most_poles": ("hamilton", 104),
            "most_championships": ("schumacher|hamilton", 7),
            "most_podiums": ("hamilton", 197),
            "youngest_champion": ("vettel", "23 years"),
            "oldest_champion": ("fangio", "46 years"),
        },
        "famous_moments": {
            "multi 21": {"year": "2013", "drivers": ["vettel", "webber"], "race": "malaysia"},
            "spa 2021": {"description": "shortest race, 2 laps behind safety car"},
            "monaco 1996": {"description": "only 3 cars finished"},
            "brazil 2008": {"description": "hamilton won championship on last corner"},
        },
    },

    # =========================================================================
    # VEO3 AI VIDEO PROMPTS
    # =========================================================================
    "veo3_prompts": {
        "fuel_production": "Industrial fuel production facility with advanced chemistry equipment, glowing reactors, sustainable energy, futuristic laboratory",
        "carbon_capture": "Carbon capture technology visualization, CO2 molecules being absorbed, green industrial facility, environmental technology",
        "engine_tech": "Formula 1 power unit internal visualization, turbo spinning, energy flow through MGU-K, high-tech engineering",
        "wind_tunnel": "F1 car in wind tunnel, smoke particles flowing over aerodynamic bodywork, technical testing facility",
        "chemistry": "Chemical synthesis process visualization, molecular bonds forming, laboratory equipment, scientific innovation",
        "factory": "High-tech F1 factory floor, carbon fiber components being manufactured, robotic precision, clean room environment",
        "data_analysis": "F1 data analysis visualization, telemetry streams, holographic displays, race strategy simulation",
        "sustainable": "Sustainable energy technology, green fuel production, environmental innovation, clean energy future",
    },
    "concept_keywords": [
        "how", "why", "explain", "understand", "break down", "analysis",
        "difference", "comparison", "evolve", "evolution", "history",
        "technical", "technology", "regulation", "rule", "change", "ban",
        "new", "era", "drs", "hybrid",
    ],
    "action_keywords": [
        "race", "racing", "overtake", "crash", "collision", "spin",
        "incident", "battle", "fight", "showdown", "chase", "pursuit",
    ],

    # =========================================================================
    # THUMBNAIL COLOR SCHEMES
    # =========================================================================
    "thumbnail_schemes": {
        "ferrari": {"bg": "#E8002D", "text": "#FFFFFF", "accent": "#FFD700"},
        "redbull": {"bg": "#1E41FF", "text": "#FFFFFF", "accent": "#FF0000"},
        "mercedes": {"bg": "#00D2BE", "text": "#000000", "accent": "#FFFFFF"},
        "mclaren": {"bg": "#FF8700", "text": "#000000", "accent": "#FFFFFF"},
        "default": {"bg": "#E8002D", "text": "#FFFFFF", "accent": "#FFD700"},
    },

    # =========================================================================
    # CAROUSEL THEMES
    # =========================================================================
    "carousel_themes": {
        # F1 Teams
        "ferrari": {
            "primary": "#E8002D", "secondary": "#A80020",
            "bg": "#1a0005", "text": "#FFFFFF", "accent": "#FFD700",
        },
        "redbull": {
            "primary": "#3671C6", "secondary": "#1B3A6B",
            "bg": "#0a1628", "text": "#FFFFFF", "accent": "#FF0000",
        },
        "mercedes": {
            "primary": "#27F4D2", "secondary": "#00A88F",
            "bg": "#0a1a17", "text": "#FFFFFF", "accent": "#FFFFFF",
        },
        "mclaren": {
            "primary": "#FF8000", "secondary": "#CC6600",
            "bg": "#1a1000", "text": "#FFFFFF", "accent": "#FFFFFF",
        },
        "aston_martin": {
            "primary": "#229971", "secondary": "#186B50",
            "bg": "#0a1a14", "text": "#FFFFFF", "accent": "#CEF032",
        },
        "alpine": {
            "primary": "#FF87BC", "secondary": "#CC6B96",
            "bg": "#1a0a12", "text": "#FFFFFF", "accent": "#0093CC",
        },
        "williams": {
            "primary": "#64C4FF", "secondary": "#3A96CC",
            "bg": "#0a1520", "text": "#FFFFFF", "accent": "#FFFFFF",
        },
        "haas": {
            "primary": "#B6BABD", "secondary": "#8A8D8F",
            "bg": "#141414", "text": "#FFFFFF", "accent": "#E8002D",
        },
        "cadillac": {
            "primary": "#C4A747", "secondary": "#8B7530",
            "bg": "#141008", "text": "#FFFFFF", "accent": "#FFFFFF",
        },
        "audi": {
            "primary": "#BB0A1E", "secondary": "#8A0716",
            "bg": "#1a0508", "text": "#FFFFFF", "accent": "#FFFFFF",
        },
        # Generic themes (shared with other channels)
        "dramatic": {
            "primary": "#E8002D", "secondary": "#8B0000",
            "bg": "#0a0a0a", "text": "#FFFFFF", "accent": "#FFD700",
        },
        "gold": {
            "primary": "#FFD700", "secondary": "#DAA520",
            "bg": "#1a1400", "text": "#FFFFFF", "accent": "#FFFFFF",
        },
        "breaking": {
            "primary": "#FF0000", "secondary": "#CC0000",
            "bg": "#1a0000", "text": "#FFFFFF", "accent": "#FFD700",
        },
        "stats": {
            "primary": "#00CED1", "secondary": "#008B8B",
            "bg": "#0a1a1a", "text": "#FFFFFF", "accent": "#FFD700",
        },
    },
    "carousel_team_themes": {
        "ferrari", "redbull", "mercedes", "mclaren", "aston_martin",
        "alpine", "williams", "haas", "cadillac", "audi",
    },

    # =========================================================================
    # PODCAST
    # =========================================================================
    "podcast": {
        "show_name": "F1 Burnouts",
        "default_voice": "Charon",
        "rss_dashboard_url": "https://dashboard.rss.com/podcasts/f1-burnouts/",
        "rss_new_episode_url": "https://dashboard.rss.com/podcasts/f1-burnouts/new-episode/",
        "tagline": "F1 Burnouts - Your weekly dose of Formula 1 passion, engineering deep-dives, and honest takes.",
        "hashtags": "#F1 #Formula1 #Podcast #Motorsport #Racing",
        "keywords": ["F1", "Formula 1", "Podcast", "Motorsport", "Racing", "F1 Burnouts"],
        "voice_profile": """
## Audio Profile
You are the host of "F1 Burnouts", a passionate and knowledgeable Formula 1 podcast host.

Character traits:
- Expert in F1 engineering, regulations, and history
- Conversational and engaging, like talking to a friend
- Witty with well-timed humor and occasional sarcasm
- Genuinely passionate about the sport
- Speaks with natural flow and breathing

Voice characteristics:
- Warm, confident, and authoritative
- SLOW, DELIBERATE PACING - speak at approximately 140-150 words per minute
- Take your time with each sentence, let words breathe
- Varied intonation to keep listeners engaged
- Clear articulation but not overly formal
- Natural pauses between sentences (0.5-1 second)

## Director's Notes - PACING IS CRITICAL
- SPEAK SLOWLY AND DELIBERATELY - this is a podcast, not an audiobook on 2x speed
- Maintain consistent voice throughout the entire podcast
- Use LONG natural pauses between topics (1-2 seconds, like taking a breath)
- Build energy during exciting moments, soften during reflective ones
- Keep the same fundamental voice character from start to finish
- Speak as one continuous monologue, not separate disconnected pieces
- Do NOT rush through the content - listeners need time to absorb information
- When you see [speaking slowly], reduce pace even further

## Performance Style
- Conversational podcast host speaking directly to the audience
- Natural transitions between topics
- Occasional emphasis on key words for impact
- Breathing pauses between paragraphs
""",
    },

    # =========================================================================
    # CREDENTIALS (filenames relative to shared/creds/<channel_id>/)
    # =========================================================================
    "creds": {
        "youtube_client_secrets": "youtube_client_secrets.json",
        "youtube_token": "youtube_token.pickle",
        "youtube_analytics_token": "youtube_analytics_token.pickle",
        "instagram": "instagram",
        "instagram_session": "instagram_session.json",
        "rss_com": "rss_com",
    },
}
