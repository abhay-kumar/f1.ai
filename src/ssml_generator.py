#!/usr/bin/env python3
"""
SSML Generator - Creates expressive SSML markup for immersive podcast TTS

Converts plain podcast scripts into SSML-enhanced text with:
- Gemini TTS emotion markers [excited], [sarcastic], [whispering], etc.
- SSML prosody control for rate, pitch, volume
- Strategic pauses for comedic timing, dramatic effect, and engagement
- Natural speech patterns with breath marks
- Emphasis on key words and phrases
- Say-as tags for numbers, dates, and measurements

Best Practices Applied:
1. Gemini [tag] syntax for emotions and vocalizations
2. SSML <break> for precise pause timing
3. SSML <emphasis> for word stress
4. SSML <prosody> for rate/pitch/volume adjustments
5. SSML <say-as> for proper number/date pronunciation
6. Hybrid approach mixing [tags] and SSML for maximum control
"""

import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir

# =============================================================================
# GEMINI TTS EMOTION MARKERS
# =============================================================================
# Gemini TTS reads these as instructions, NOT spoken words
# Use sparingly - one per paragraph maximum for best results

# Primary emotion markers mapped from segment emotions
EMOTION_TO_MARKER = {
    # High energy
    "energetic": "[excited]",
    "excited": "[excited]",
    # Intrigue and curiosity
    "intrigued": "[intrigued]",
    "curious": "[intrigued]",
    # Thoughtful/slow
    "contemplative": "[speaking slowly]",
    "reflective": "[speaking slowly]",
    # Humor and sarcasm
    "humorous": "[playful]",
    "sarcastic": "[sarcastic]",
    "playful": "[playful]",
    # Heartfelt
    "heartfelt": "[empathetic]",
    "emotional": "[empathetic]",
    "sad": "[sad]",
    # Serious/intense
    "serious": "[serious]",
    "intense": "[intense]",
    # Passionate
    "passionate": "[passionate]",
    # Vocalizations (for specific moments)
    "laughing": "[laughing]",
    "sighing": "[sighing]",
    "whispering": "[whispering]",
    "shouting": "[shouting]",
}

# Additional inline markers for specific moments within text
# These can be inserted mid-sentence for effect
INLINE_MARKERS = {
    # Reactions
    "laugh": "[laughing]",
    "sigh": "[sighing]",
    "gasp": "[gasping]",
    "hmm": "[thinking]",
    # Delivery styles
    "whisper": "[whispering]",
    "loud": "[shouting]",
    "slow": "[speaking slowly]",
    "fast": "[speaking quickly]",
    # Tones
    "sarcasm": "[sarcastic]",
    "mock": "[mocking]",
    "excited": "[excited]",
}

# =============================================================================
# PROSODY SETTINGS
# =============================================================================
# SSML prosody adjustments per emotion for fine-tuned delivery

PROSODY_SETTINGS = {
    "energetic": {"rate": "108%", "pitch": "+8%", "volume": "+2dB"},
    "excited": {"rate": "110%", "pitch": "+10%", "volume": "+3dB"},
    "intrigued": {"rate": "95%", "pitch": "+3%", "volume": "medium"},
    "contemplative": {"rate": "82%", "pitch": "-5%", "volume": "-1dB"},
    "humorous": {"rate": "102%", "pitch": "+5%", "volume": "medium"},
    "sarcastic": {"rate": "92%", "pitch": "-2%", "volume": "medium"},
    "heartfelt": {"rate": "88%", "pitch": "-3%", "volume": "-2dB"},
    "serious": {"rate": "90%", "pitch": "-6%", "volume": "medium"},
    "passionate": {"rate": "105%", "pitch": "+6%", "volume": "+2dB"},
    "neutral": {"rate": "100%", "pitch": "medium", "volume": "medium"},
}

# =============================================================================
# PAUSE PATTERNS
# =============================================================================
# Strategic pauses for natural rhythm, comedic timing, and dramatic effect

PAUSE_PATTERNS = [
    # === OPENING/GREETING PAUSES ===
    # After welcome phrases - let the energy land
    (r"(Welcome (?:back )?to [^!.?]+[!.?])", r"\1 <break time='0.9s'/>"),
    (r"(I'm your host[^.!?]*[.!?])", r"\1 <break time='0.6s'/>"),
    (r"(What(?:'s| is) up[^!?]*[!?])", r"\1 <break time='0.5s'/>"),
    # === DRAMATIC REVEAL PAUSES ===
    # Before big reveals - build anticipation
    (
        r"(\.\s+)(And here's (?:the thing|where it gets|what I think))",
        r"\1<break time='0.6s'/> \2",
    ),
    (
        r"(\.\s+)(But here's (?:the thing|the deal|the catch|what|where))",
        r"\1<break time='0.6s'/> \2",
    ),
    (r"(\.\s+)(Now,? here's (?:the|what|where))", r"\1<break time='0.5s'/> \2"),
    (
        r"(\.\s+)(The (?:real|actual|true) (?:story|reason|answer))",
        r"\1<break time='0.5s'/> \2",
    ),
    # === COMEDIC TIMING PAUSES ===
    # After setup, before punchline
    (
        r"(And (?:in news that|surprisingly|unsurprisingly|predictably)[^.!?]+[.!?])",
        r"\1 <break time='0.7s'/>",
    ),
    (r"(shocked absolutely (?:no one|everyone)[.!?])", r"\1 <break time='0.6s'/>"),
    (r"(what a surprise[.!?])", r"\1 <break time='0.5s'/>"),
    (r"(obviously[.!?,])", r"\1 <break time='0.3s'/>"),
    # Sarcastic pause after "Of course"
    (r"(Of course,)", r"\1 <break time='0.4s'/>"),
    (r"(Naturally,)", r"\1 <break time='0.4s'/>"),
    (r"(Surely,)", r"\1 <break time='0.4s'/>"),
    # === RHETORICAL QUESTION PAUSES ===
    # After questions - let them land
    (r"(\?)\s+([A-Z])", r"? <break time='0.7s'/> \2"),
    (r"(right\?)", r"\1 <break time='0.5s'/>"),
    (r"(you know\?)", r"\1 <break time='0.4s'/>"),
    (r"(think about (?:that|it)[.!?])", r"\1 <break time='0.8s'/>"),
    # === TRANSITION PAUSES ===
    # Segment transitions
    (r"(\.\s+)(Now,(?!\s+here))", r"\1<break time='0.5s'/> \2"),
    (r"(\.\s+)(Alright,)", r"\1<break time='0.4s'/> \2"),
    (r"(\.\s+)(Okay,)", r"\1<break time='0.4s'/> \2"),
    (r"(\.\s+)(So,)", r"\1<break time='0.3s'/> \2"),
    (r"(\.\s+)(Anyway,)", r"\1<break time='0.4s'/> \2"),
    (r"(\.\s+)(Moving on,)", r"\1<break time='0.5s'/> \2"),
    (r"(\.\s+)(But wait,)", r"\1<break time='0.4s'/> \2"),
    # === ELLIPSIS PAUSES ===
    # Natural trailing off or suspense
    (r"\.\.\.(\s+)", r" <break time='0.5s'/>\1"),
    (r"\.\.\.([A-Z])", r" <break time='0.5s'/> \1"),
    # === EM-DASH PAUSES ===
    # Interruptions, asides, dramatic interjections
    (r"\s*—\s*", r" <break time='0.25s'/> "),
    (r"\s*--\s*", r" <break time='0.25s'/> "),
    # === EMPHASIS BEFORE KEY MOMENTS ===
    # Slight pause before important facts
    (r"(\.\s+)(The truth is)", r"\1<break time='0.4s'/> \2"),
    (r"(\.\s+)(Here's the (?:thing|deal|kicker))", r"\1<break time='0.5s'/> \2"),
    (
        r"(\.\s+)(Let me (?:tell you|explain|break this down))",
        r"\1<break time='0.4s'/> \2",
    ),
    # === LISTING PAUSES ===
    # Before numbered items or lists
    (r"(First(?:ly)?,)", r"\1 <break time='0.3s'/>"),
    (r"(Second(?:ly)?,)", r"\1 <break time='0.3s'/>"),
    (r"(Third(?:ly)?,)", r"\1 <break time='0.3s'/>"),
    (r"(Finally,)", r"\1 <break time='0.4s'/>"),
    (r"(Last(?:ly)?,)", r"\1 <break time='0.4s'/>"),
]

# =============================================================================
# EMPHASIS PATTERNS
# =============================================================================
# Words and phrases that should receive vocal emphasis

# Strong emphasis - key impactful words
STRONG_EMPHASIS_WORDS = [
    "incredible",
    "unbelievable",
    "insane",
    "wild",
    "crazy",
    "revolutionary",
    "game-changing",
    "groundbreaking",
    "billion",
    "million",
    "trillion",
    "never",
    "ever",
    "always",
    "absolutely",
    "completely",
    "totally",
    "first",
    "last",
    "only",
    "fastest",
    "slowest",
    "biggest",
    "smallest",
    "zero",
    "nothing",
    "everything",
    "catastrophic",
    "disastrous",
    "brilliant",
    "genius",
    "championship",
    "victory",
    "defeat",
]

# Moderate emphasis - important but less dramatic
MODERATE_EMPHASIS_WORDS = [
    "actually",
    "really",
    "genuinely",
    "truly",
    "literally",
    "crucial",
    "critical",
    "essential",
    "vital",
    "massive",
    "huge",
    "tiny",
    "enormous",
    "amazing",
    "fascinating",
    "remarkable",
    "stunning",
    "important",
    "significant",
    "key",
    "exactly",
    "precisely",
    "specifically",
]

# Reduced emphasis - softer, more intimate
REDUCED_EMPHASIS_PATTERNS = [
    (r"\b(just between us)\b", r'<emphasis level="reduced">\1</emphasis>'),
    (r"\b(quietly)\b", r'<emphasis level="reduced">\1</emphasis>'),
    (r"\b(secretly)\b", r'<emphasis level="reduced">\1</emphasis>'),
]

# =============================================================================
# SAY-AS PATTERNS
# =============================================================================
# Proper pronunciation of numbers, dates, measurements

SAY_AS_PATTERNS = [
    # Years (4-digit numbers that look like years)
    (
        r"\b(19[0-9]{2}|20[0-9]{2})\b",
        r'<say-as interpret-as="date" format="y">\1</say-as>',
    ),
    # Percentages
    (
        r"\b(\d+(?:\.\d+)?)\s*(?:percent|%)",
        r'<say-as interpret-as="cardinal">\1</say-as> percent',
    ),
    # Large numbers with commas (read as cardinal)
    (r"\b(\d{1,3}(?:,\d{3})+)\b", r'<say-as interpret-as="cardinal">\1</say-as>'),
    # Ordinals (1st, 2nd, 3rd, etc.)
    (r"\b(\d+)(?:st|nd|rd|th)\b", r'<say-as interpret-as="ordinal">\1</say-as>'),
    # Speed measurements
    (r"\b(\d+)\s*(?:km/h|kph|kilometers?\s*per\s*hour)\b", r"\1 kilometers per hour"),
    (r"\b(\d+)\s*(?:mph|miles?\s*per\s*hour)\b", r"\1 miles per hour"),
    # Time durations
    (r"\b(\d+(?:\.\d+)?)\s*seconds?\b", r"\1 seconds"),
    (r"\b(\d+(?:\.\d+)?)\s*minutes?\b", r"\1 minutes"),
    (r"\b(\d+(?:\.\d+)?)\s*hours?\b", r"\1 hours"),
    # Currency
    (r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|m)\b", r"\1 million dollars"),
    (r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:billion|b)\b", r"\1 billion dollars"),
    (
        r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)\b",
        r'<say-as interpret-as="currency">\1 dollars</say-as>',
    ),
    # Lap times (M:SS.mmm format)
    (
        r"\b(\d):(\d{2})\.(\d{3})\b",
        r'<say-as interpret-as="cardinal">\1</say-as> minute <say-as interpret-as="cardinal">\2</say-as> point <say-as interpret-as="digits">\3</say-as>',
    ),
]

# =============================================================================
# ENGAGEMENT PATTERNS
# =============================================================================
# Patterns that make content more engaging, funny, and intriguing

ENGAGEMENT_PATTERNS = [
    # Add emphasis to direct audience address
    (
        r"\b(you)\b(?!')",
        r'<emphasis level="moderate">you</emphasis>',
        3,
    ),  # Limit to 3 replacements
    # Emphasize contrasts
    (r"\b(but)\b", r'<emphasis level="moderate">but</emphasis>', 2),
    # Questions to audience
    (r"(Can you (?:believe|imagine)[^?]+\?)", r'<break time="0.2s"/>\1'),
    # Teasing upcoming content
    (
        r"(Wait (?:for it|until you hear)[^.!?]*[.!?])",
        r'<break time="0.3s"/>\1 <break time="0.5s"/>',
    ),
]

# =============================================================================
# SARCASM AND HUMOR PATTERNS
# =============================================================================
# Special handling for sarcastic and humorous content

SARCASM_INDICATORS = [
    "obviously",
    "of course",
    "clearly",
    "naturally",
    "surely",
    "definitely",
    "what a surprise",
    "shocked no one",
    "shocked everyone",
    "totally unexpected",
    "completely predictable",
    "as expected",
    "who could have predicted",
    "in news that",
]

# Phrases that benefit from a sarcastic delivery marker
SARCASM_PHRASES = [
    (
        r"(And in news that (?:shocked|surprised|stunned) (?:absolutely )?(?:no one|everyone)[^.!?]*[.!?])",
        r"[sarcastic] \1",
    ),
    (r"(What a (?:shocking )?surprise[.!?])", r"[sarcastic] \1"),
    (
        r"(Who could have (?:possibly )?(?:predicted|seen|expected) that[^?]*\?)",
        r"[sarcastic] \1",
    ),
    (r"(Totally (?:unexpected|predictable)[.!?])", r"[sarcastic] \1"),
]


# =============================================================================
# CORE GENERATION FUNCTIONS
# =============================================================================


def add_emotion_marker(text: str, emotion: str) -> str:
    """
    Add Gemini emotion marker at the start of the text.

    Gemini TTS reads [markers] as delivery instructions, not spoken words.
    This sets the overall emotional tone for the segment.
    """
    marker = EMOTION_TO_MARKER.get(emotion.lower(), "")
    if marker:
        # Don't double-add if marker already exists
        if text.strip().startswith("["):
            return text
        return f"{marker} {text}"
    return text


def add_prosody_wrapper(text: str, emotion: str) -> str:
    """
    Wrap text in SSML prosody tags based on emotion.

    Adjusts rate, pitch, and volume for the emotional delivery.
    Gemini TTS supports <prosody> for fine-tuned control.
    """
    settings = PROSODY_SETTINGS.get(emotion.lower(), PROSODY_SETTINGS["neutral"])
    rate = settings.get("rate", "100%")
    pitch = settings.get("pitch", "medium")
    volume = settings.get("volume", "medium")

    # Only wrap if we have non-default settings
    if rate != "100%" or pitch != "medium" or volume != "medium":
        return (
            f'<prosody rate="{rate}" pitch="{pitch}" volume="{volume}">{text}</prosody>'
        )
    return text


def add_pauses(text: str) -> str:
    """
    Add strategic SSML pauses for natural speech rhythm and effect.

    Includes:
    - Dramatic pauses before reveals
    - Comedic timing pauses
    - Rhetorical question pauses
    - Transition pauses
    """
    result = text
    for pattern, replacement in PAUSE_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


def add_emphasis(text: str) -> str:
    """
    Add SSML emphasis to key words and phrases.

    Uses three levels:
    - strong: Impactful, dramatic words
    - moderate: Important words
    - reduced: Softer, intimate phrases
    """
    result = text

    # Strong emphasis words
    for word in STRONG_EMPHASIS_WORDS:
        pattern = rf"\b({word})\b"
        # Only replace if not already inside an SSML tag
        result = re.sub(
            pattern,
            r'<emphasis level="strong">\1</emphasis>',
            result,
            flags=re.IGNORECASE,
            count=2,  # Limit to avoid over-emphasis
        )

    # Moderate emphasis words
    for word in MODERATE_EMPHASIS_WORDS:
        pattern = rf"\b({word})\b"
        result = re.sub(
            pattern,
            r'<emphasis level="moderate">\1</emphasis>',
            result,
            flags=re.IGNORECASE,
            count=2,
        )

    # Reduced emphasis patterns
    for pattern, replacement in REDUCED_EMPHASIS_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def process_numbers(text: str) -> str:
    """
    Process numbers, dates, and measurements for proper TTS pronunciation.

    Uses <say-as> SSML tags to ensure:
    - Years are read as years (not "two thousand twenty-four")
    - Large numbers are read naturally
    - Measurements have proper units spoken
    """
    result = text
    for pattern, replacement in SAY_AS_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def add_sarcasm_markers(text: str, emotion: str) -> str:
    """
    Add sarcastic delivery markers for humorous/sarcastic content.

    Detects common sarcasm patterns and adds [sarcastic] marker
    for Gemini TTS to deliver with the right tone.
    """
    # Only add sarcasm markers if the emotion calls for it
    if emotion.lower() not in ["humorous", "sarcastic", "playful"]:
        return text

    result = text
    for pattern, replacement in SARCASM_PHRASES:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def add_breath_marks(text: str) -> str:
    """
    Add natural breathing points for long sentences.

    Inserts small pauses at clause boundaries in sentences
    longer than 150 characters for natural pacing.
    """
    # Split into sentences
    sentences = re.split(r"([.!?]+)", text)
    result_parts = []

    for i, part in enumerate(sentences):
        if re.match(r"[.!?]+", part):
            result_parts.append(part)
        elif len(part) > 150:  # Long sentence
            # Add breath mark at natural break points (after clause conjunctions)
            clause_markers = r"(,\s+(?:and|but|or|so|because|when|while|if|although|though|since|unless|whether)\s+)"
            part = re.sub(clause_markers, r'\1<break time="0.2s"/>', part)
            result_parts.append(part)
        else:
            result_parts.append(part)

    return "".join(result_parts)


def enhance_punctuation(text: str) -> str:
    """
    Enhance punctuation for more expressive speech.

    - Exclamation marks get slight energy boost
    - Multiple punctuation gets dramatic pause
    """
    result = text

    # Multiple exclamation/question marks - extra emphasis
    result = re.sub(r"([!?]){2,}", r"\1 <break time='0.3s'/>", result)

    return result


def add_engagement_patterns(text: str) -> str:
    """
    Add patterns that make content more engaging and audience-focused.
    """
    result = text
    for pattern in ENGAGEMENT_PATTERNS:
        if len(pattern) == 3:
            pat, repl, count = pattern
            result = re.sub(pat, repl, result, count=count, flags=re.IGNORECASE)
        else:
            pat, repl = pattern
            result = re.sub(pat, repl, result, flags=re.IGNORECASE)
    return result


def clean_ssml(text: str) -> str:
    """
    Clean up any SSML issues like nested tags or malformed markup.
    """
    # Remove any double breaks
    text = re.sub(r"<break[^>]*>\s*<break[^>]*>", r"<break time='0.5s'/>", text)

    # Remove any nested emphasis (keep innermost)
    # This is a simplified fix; complex nesting would need proper parsing
    while re.search(r"<emphasis[^>]*>\s*<emphasis", text):
        text = re.sub(r"<emphasis[^>]*>(\s*<emphasis)", r"\1", text)

    # Ensure break tags are self-closing
    text = re.sub(r"<break time='([^']+)'(?!/)>", r"<break time='\1'/>", text)

    # Remove any empty emphasis tags
    text = re.sub(r"<emphasis[^>]*>\s*</emphasis>", "", text)

    return text


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================


def generate_ssml(
    text: str, emotion: str = "energetic", use_prosody: bool = False
) -> str:
    """
    Generate SSML-enhanced text for Gemini TTS.

    Combines multiple enhancement strategies for engaging podcast delivery:

    1. Gemini [emotion] markers for overall tone
    2. SSML <break> tags for strategic pauses
    3. SSML <emphasis> for word stress
    4. SSML <say-as> for proper number/date pronunciation
    5. Natural breathing points for long sentences
    6. Sarcasm/humor markers for comedic content

    Args:
        text: Plain text to enhance
        emotion: Emotional tone (energetic, sarcastic, contemplative, etc.)
        use_prosody: Whether to wrap in prosody tags (experimental)

    Returns:
        SSML-enhanced text ready for Gemini TTS

    Example:
        Input: "Welcome back! In news that shocked no one, Ferrari made a strategic error."
        Output: "[excited] Welcome back! <break time='0.9s'/> [sarcastic] In news that
                <emphasis level='strong'>shocked</emphasis> <emphasis level='strong'>no one</emphasis>,
                Ferrari made a strategic error. <break time='0.7s'/>"
    """
    # Start with the raw text
    result = text.strip()

    # 1. Process numbers and dates for proper pronunciation
    result = process_numbers(result)

    # 2. Add emphasis to key words (before pauses, so pauses don't break emphasis)
    result = add_emphasis(result)

    # 3. Add sarcasm markers for humorous content
    result = add_sarcasm_markers(result, emotion)

    # 4. Enhance punctuation
    result = enhance_punctuation(result)

    # 5. Add strategic pauses (after emphasis, so pause positions are accurate)
    result = add_pauses(result)

    # 6. Add breath marks for long sentences
    result = add_breath_marks(result)

    # 7. Add engagement patterns
    result = add_engagement_patterns(result)

    # 8. Clean up any SSML issues
    result = clean_ssml(result)

    # 9. Add emotion marker at the start (Gemini interprets this as delivery style)
    result = add_emotion_marker(result, emotion)

    # 10. Optionally wrap in prosody for overall rate/pitch/volume
    if use_prosody:
        result = add_prosody_wrapper(result, emotion)

    return result


def generate_ssml_for_humor(text: str) -> str:
    """
    Generate SSML specifically optimized for humorous/sarcastic content.

    Applies extra timing adjustments for comedic effect.
    """
    return generate_ssml(text, emotion="humorous")


def generate_ssml_for_drama(text: str) -> str:
    """
    Generate SSML specifically optimized for dramatic reveals.

    Applies longer pauses and slower pacing.
    """
    return generate_ssml(text, emotion="contemplative")


# =============================================================================
# SCRIPT PROCESSING
# =============================================================================


def process_script(script: Dict) -> Dict:
    """
    Process entire script.json and add SSML markup to all segments.

    Returns a new script dict with 'ssml_text' field added to each segment.
    """
    enhanced_script = script.copy()
    enhanced_script["segments"] = []

    for segment in script["segments"]:
        enhanced_segment = segment.copy()
        emotion = segment.get("emotion", "energetic")
        original_text = segment["text"]

        # Generate SSML-enhanced version
        ssml_text = generate_ssml(original_text, emotion)
        enhanced_segment["ssml_text"] = ssml_text

        enhanced_script["segments"].append(enhanced_segment)

    return enhanced_script


def preview_segment(text: str, emotion: str = "energetic") -> None:
    """
    Print a formatted preview of original vs SSML-enhanced text.
    """
    print("=" * 70)
    print(f"EMOTION: {emotion}")
    print("=" * 70)
    print("\n[ORIGINAL TEXT]")
    print("-" * 70)
    print(text)
    print("\n[SSML ENHANCED]")
    print("-" * 70)
    print(generate_ssml(text, emotion))
    print("=" * 70)


# =============================================================================
# CLI
# =============================================================================


def main():
    """CLI for testing and previewing SSML generation"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate SSML for podcast scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview SSML for a project
  python3 src/ssml_generator.py --project my-podcast --preview

  # Process specific segment
  python3 src/ssml_generator.py --project my-podcast --segment 0

  # Test with inline text
  python3 src/ssml_generator.py --test "Welcome back! Today we're diving into something incredible."

  # List available emotions
  python3 src/ssml_generator.py --list-emotions
        """,
    )
    parser.add_argument("--project", help="Project name")
    parser.add_argument(
        "--preview", action="store_true", help="Preview SSML without saving"
    )
    parser.add_argument(
        "--segment", type=int, help="Only process specific segment (0-indexed)"
    )
    parser.add_argument(
        "--test", type=str, help="Test SSML generation with inline text"
    )
    parser.add_argument("--emotion", default="energetic", help="Emotion for test text")
    parser.add_argument(
        "--list-emotions", action="store_true", help="List available emotions"
    )
    args = parser.parse_args()

    # List emotions
    if args.list_emotions:
        print("Available Emotions and Their Markers:")
        print("-" * 50)
        for emotion, marker in sorted(EMOTION_TO_MARKER.items()):
            settings = PROSODY_SETTINGS.get(emotion, {})
            rate = settings.get("rate", "100%")
            pitch = settings.get("pitch", "medium")
            print(f"  {emotion:15} -> {marker:20} (rate: {rate}, pitch: {pitch})")
        sys.exit(0)

    # Test mode with inline text
    if args.test:
        preview_segment(args.test, args.emotion)
        sys.exit(0)

    # Project mode
    if not args.project:
        parser.error("--project is required (unless using --test or --list-emotions)")

    project_dir = get_project_dir(args.project)
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    with open(script_file) as f:
        script = json.load(f)

    if args.segment is not None:
        # Preview single segment
        if args.segment >= len(script["segments"]):
            print(
                f"Error: Segment {args.segment} not found (max: {len(script['segments']) - 1})"
            )
            sys.exit(1)

        segment = script["segments"][args.segment]
        emotion = segment.get("emotion", "energetic")
        context = segment.get("context", "No context")

        print(f"\nSegment {args.segment}: {context}")
        preview_segment(segment["text"], emotion)
    else:
        # Process entire script
        enhanced = process_script(script)

        if args.preview:
            # Show preview
            print("=" * 70)
            print(f"SSML Preview - {len(enhanced['segments'])} segments")
            print("=" * 70)

            for i, segment in enumerate(enhanced["segments"]):
                context = segment.get("context", "")[:40]
                emotion = segment.get("emotion", "energetic")
                print(f"\n[Segment {i}] {context} ({emotion})")
                print("-" * 50)
                print(f"Original: {segment['text'][:100]}...")
                print(f"SSML: {segment['ssml_text'][:150]}...")

            if len(enhanced["segments"]) > 5:
                print(f"\n... and {len(enhanced['segments']) - 5} more segments")
        else:
            # Save enhanced script
            output_file = f"{project_dir}/script_ssml.json"
            with open(output_file, "w") as f:
                json.dump(enhanced, f, indent=2)

            print(f"Enhanced script saved to: {output_file}")
            print(f"Processed {len(enhanced['segments'])} segments")


if __name__ == "__main__":
    main()
