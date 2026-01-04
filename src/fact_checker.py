#!/usr/bin/env python3
"""
Fact Checker - Validates F1 script content for accuracy
Uses web search to verify claims in each line of the script.
"""
import os
import sys
import json
import argparse
import re
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir

# Try to import web search capabilities
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class FactCheckResult:
    """Result of fact-checking a single claim"""
    claim: str
    verdict: str  # "verified", "unverified", "disputed", "error"
    confidence: float  # 0.0 to 1.0
    sources: List[str]
    notes: str


@dataclass
class LineCheckResult:
    """Result of fact-checking a line"""
    line_number: int
    segment_id: int
    text: str
    claims: List[FactCheckResult]
    overall_verdict: str


# F1 Knowledge Base - Common facts that don't need web verification
F1_KNOWLEDGE_BASE = {
    # World Champions
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
    # Team names and their drivers (2024 season)
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
    # Record holders
    "records": {
        "most_wins": ("hamilton", 104),
        "most_poles": ("hamilton", 104),
        "most_championships": ("schumacher|hamilton", 7),
        "most_podiums": ("hamilton", 197),
        "youngest_champion": ("vettel", "23 years"),
        "oldest_champion": ("fangio", "46 years"),
    },
    # Famous races/moments
    "famous_moments": {
        "multi 21": {"year": "2013", "drivers": ["vettel", "webber"], "race": "malaysia"},
        "spa 2021": {"description": "shortest race, 2 laps behind safety car"},
        "monaco 1996": {"description": "only 3 cars finished"},
        "brazil 2008": {"description": "hamilton won championship on last corner"},
    }
}


def extract_claims(text: str) -> List[str]:
    """Extract verifiable claims from text"""
    claims = []

    # Split into sentences
    sentences = re.split(r'[.!?]', text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Look for specific claim patterns
        patterns = [
            # Year mentions
            r'in (\d{4})',
            # Championship claims
            r'(\w+) (won|became|clinched|secured) .*(championship|title)',
            # Record claims
            r'(first|youngest|oldest|most|fastest|slowest)',
            # Statistical claims
            r'(\d+) (wins?|poles?|podiums?|championships?|points?)',
            # Team affiliations
            r'(\w+) (joined|drove for|raced for|moved to) (\w+)',
            # Race results
            r'(won|finished|crashed|retired) (at|in|during) (\w+)',
        ]

        for pattern in patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                claims.append(sentence)
                break

    return claims


def verify_against_knowledge_base(claim: str) -> Optional[FactCheckResult]:
    """Check claim against built-in F1 knowledge base"""
    claim_lower = claim.lower()

    # Check championship claims
    for driver, years in F1_KNOWLEDGE_BASE["champions"].items():
        if driver in claim_lower:
            for year in years:
                if year in claim:
                    return FactCheckResult(
                        claim=claim,
                        verdict="verified",
                        confidence=1.0,
                        sources=["F1 Official Records"],
                        notes=f"Verified: {driver.title()} was champion in {year}"
                    )

    # Check team affiliations (2024)
    for team, drivers in F1_KNOWLEDGE_BASE["teams_2024"].items():
        if team in claim_lower:
            for driver in drivers:
                if driver in claim_lower:
                    return FactCheckResult(
                        claim=claim,
                        verdict="verified",
                        confidence=0.95,
                        sources=["2024 F1 Team Lineup"],
                        notes=f"Verified: {driver.title()} drives for {team.title()}"
                    )

    # Check records
    for record_type, (holder, value) in F1_KNOWLEDGE_BASE["records"].items():
        record_words = record_type.replace("_", " ")
        if record_words in claim_lower:
            if holder in claim_lower or (isinstance(holder, str) and "|" in holder and
                                         any(h in claim_lower for h in holder.split("|"))):
                return FactCheckResult(
                    claim=claim,
                    verdict="verified",
                    confidence=0.9,
                    sources=["F1 Statistics"],
                    notes=f"Verified: {holder} holds {record_words} record ({value})"
                )

    return None


def verify_with_web_search(claim: str, api_key: Optional[str] = None) -> FactCheckResult:
    """Verify claim using web search (requires API key)"""
    if not HAS_REQUESTS:
        return FactCheckResult(
            claim=claim,
            verdict="unverified",
            confidence=0.0,
            sources=[],
            notes="Web search unavailable (requests library not installed)"
        )

    if not api_key:
        return FactCheckResult(
            claim=claim,
            verdict="unverified",
            confidence=0.0,
            sources=[],
            notes="Web search requires API key (--api-key or SERPAPI_KEY env var)"
        )

    try:
        # Use SerpAPI for web search (free tier available)
        params = {
            "q": f"F1 Formula 1 {claim}",
            "api_key": api_key,
            "engine": "google",
            "num": 5
        }
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            organic_results = data.get("organic_results", [])

            if organic_results:
                sources = [r.get("link", "") for r in organic_results[:3]]
                # Simple heuristic: if multiple results mention similar info, likely true
                snippets = " ".join([r.get("snippet", "") for r in organic_results])

                # Check for contradictions
                contradictions = ["not true", "false", "incorrect", "myth", "debunked"]
                has_contradiction = any(c in snippets.lower() for c in contradictions)

                if has_contradiction:
                    return FactCheckResult(
                        claim=claim,
                        verdict="disputed",
                        confidence=0.5,
                        sources=sources,
                        notes="Found potentially contradicting information"
                    )
                else:
                    return FactCheckResult(
                        claim=claim,
                        verdict="verified",
                        confidence=0.7,
                        sources=sources,
                        notes="Web search found supporting information"
                    )

        return FactCheckResult(
            claim=claim,
            verdict="unverified",
            confidence=0.3,
            sources=[],
            notes="Could not verify through web search"
        )

    except Exception as e:
        return FactCheckResult(
            claim=claim,
            verdict="error",
            confidence=0.0,
            sources=[],
            notes=f"Web search error: {str(e)}"
        )


def check_claim(claim: str, use_web: bool = False, api_key: Optional[str] = None) -> FactCheckResult:
    """Check a single claim using knowledge base and optionally web search"""
    # First try knowledge base
    kb_result = verify_against_knowledge_base(claim)
    if kb_result and kb_result.confidence >= 0.9:
        return kb_result

    # If not found in KB and web search enabled, try web
    if use_web:
        web_result = verify_with_web_search(claim, api_key)
        if web_result.verdict != "error":
            return web_result

    # Return unverified if nothing found
    return FactCheckResult(
        claim=claim,
        verdict="unverified",
        confidence=0.0,
        sources=[],
        notes="Not found in knowledge base; enable --web-search for online verification"
    )


def check_segment(segment: Dict, segment_id: int, use_web: bool = False,
                  api_key: Optional[str] = None) -> List[LineCheckResult]:
    """Check all claims in a segment"""
    results = []
    text = segment.get("text", "")

    # Extract claims from text
    claims = extract_claims(text)

    if not claims:
        # No verifiable claims found
        results.append(LineCheckResult(
            line_number=1,
            segment_id=segment_id,
            text=text,
            claims=[],
            overall_verdict="no_claims"
        ))
        return results

    # Check each claim
    claim_results = []
    for claim in claims:
        result = check_claim(claim, use_web, api_key)
        claim_results.append(result)

    # Determine overall verdict
    verdicts = [c.verdict for c in claim_results]
    if all(v == "verified" for v in verdicts):
        overall = "verified"
    elif any(v == "disputed" for v in verdicts):
        overall = "disputed"
    elif any(v == "verified" for v in verdicts):
        overall = "partially_verified"
    else:
        overall = "unverified"

    results.append(LineCheckResult(
        line_number=1,
        segment_id=segment_id,
        text=text,
        claims=claim_results,
        overall_verdict=overall
    ))

    return results


def validate_references(script: Dict) -> Dict:
    """Validate that all segments have proper references (for long-form videos)"""
    issues = {
        "missing_references": [],
        "incomplete_references": [],
        "total_references": 0,
        "segments_with_refs": 0,
        "segments_without_refs": 0
    }

    segments = script.get("segments", [])

    for idx, segment in enumerate(segments):
        refs = segment.get("references", [])

        if not refs:
            issues["missing_references"].append({
                "segment_id": idx,
                "text": segment.get("text", "")[:80]
            })
            issues["segments_without_refs"] += 1
        else:
            issues["segments_with_refs"] += 1
            issues["total_references"] += len(refs)

            # Check each reference for completeness
            for ref in refs:
                if not ref.get("source") or not ref.get("url"):
                    issues["incomplete_references"].append({
                        "segment_id": idx,
                        "reference": ref
                    })

    return issues


def generate_reference_suggestions(segment: Dict, claim_results: List[FactCheckResult]) -> List[Dict]:
    """Generate reference suggestions based on fact check results"""
    suggestions = []

    for result in claim_results:
        if result.sources:
            suggestions.append({
                "claim": result.claim[:100],
                "suggested_source": result.sources[0] if result.sources else "",
                "confidence": result.confidence,
                "notes": result.notes
            })

    return suggestions


def main():
    parser = argparse.ArgumentParser(description='Fact-check F1 script content')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--segment', type=int, help='Check specific segment only')
    parser.add_argument('--web-search', action='store_true',
                        help='Enable web search for verification (requires API key)')
    parser.add_argument('--api-key', help='SerpAPI key for web search (or set SERPAPI_KEY env var)')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                        help='Output format')
    parser.add_argument('--strict', action='store_true',
                        help='Fail if any claims are unverified or disputed')
    parser.add_argument('--validate-refs', action='store_true',
                        help='Validate references in script (for long-form videos)')
    parser.add_argument('--suggest-refs', action='store_true',
                        help='Suggest references based on web search results')
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    with open(script_file) as f:
        script = json.load(f)

    segments = script.get("segments", [])

    # Get API key
    api_key = args.api_key or os.environ.get("SERPAPI_KEY")

    print("=" * 60)
    print(f"Fact Checker - Project: {args.project}")
    print(f"Web Search: {'Enabled' if args.web_search else 'Disabled'}")
    print("=" * 60)

    # Validate references if requested (for long-form videos)
    if args.validate_refs:
        print("\n📚 REFERENCE VALIDATION")
        print("-" * 40)
        ref_issues = validate_references(script)

        print(f"  Segments with references:    {ref_issues['segments_with_refs']}")
        print(f"  Segments without references: {ref_issues['segments_without_refs']}")
        print(f"  Total references:            {ref_issues['total_references']}")

        if ref_issues['missing_references']:
            print(f"\n  ⚠️  Segments missing references:")
            for issue in ref_issues['missing_references'][:10]:
                print(f"      [Segment {issue['segment_id']}] {issue['text']}...")
            if len(ref_issues['missing_references']) > 10:
                print(f"      ... and {len(ref_issues['missing_references']) - 10} more")

        if ref_issues['incomplete_references']:
            print(f"\n  ⚠️  Incomplete references (missing source/url):")
            for issue in ref_issues['incomplete_references'][:5]:
                print(f"      [Segment {issue['segment_id']}] {issue['reference']}")

        print()

    all_results = []
    stats = {"verified": 0, "unverified": 0, "disputed": 0, "no_claims": 0, "partially_verified": 0}
    reference_suggestions = []

    # Process segments
    if args.segment is not None:
        segments_to_check = [(args.segment, segments[args.segment])]
    else:
        segments_to_check = list(enumerate(segments))

    for idx, segment in segments_to_check:
        print(f"\n[Segment {idx}] {segment.get('context', 'Unknown')}")
        print(f"  Text: {segment.get('text', '')[:80]}...")

        results = check_segment(segment, idx, args.web_search, api_key)
        all_results.extend(results)

        for result in results:
            stats[result.overall_verdict] += 1
            print(f"  Status: {result.overall_verdict.upper()}")

            if result.claims:
                for claim_result in result.claims:
                    icon = {
                        "verified": "[OK]",
                        "unverified": "[??]",
                        "disputed": "[!!]",
                        "error": "[ERR]"
                    }.get(claim_result.verdict, "[??]")
                    print(f"    {icon} {claim_result.claim[:60]}...")
                    if claim_result.notes:
                        print(f"        -> {claim_result.notes}")

                # Generate reference suggestions if requested
                if args.suggest_refs and args.web_search:
                    suggestions = generate_reference_suggestions(segment, result.claims)
                    if suggestions:
                        reference_suggestions.append({
                            "segment_id": idx,
                            "suggestions": suggestions
                        })

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Verified:           {stats['verified']}")
    print(f"  Partially Verified: {stats['partially_verified']}")
    print(f"  Unverified:         {stats['unverified']}")
    print(f"  Disputed:           {stats['disputed']}")
    print(f"  No Claims:          {stats['no_claims']}")

    # Output JSON if requested
    if args.output == 'json':
        output_file = f"{project_dir}/fact_check_results.json"
        json_results = {
            "project": args.project,
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "results": [
                {
                    "segment_id": r.segment_id,
                    "text": r.text,
                    "overall_verdict": r.overall_verdict,
                    "claims": [
                        {
                            "claim": c.claim,
                            "verdict": c.verdict,
                            "confidence": c.confidence,
                            "sources": c.sources,
                            "notes": c.notes
                        }
                        for c in r.claims
                    ]
                }
                for r in all_results
            ]
        }
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        print(f"\nResults saved to: {output_file}")

    # Show reference suggestions if generated
    if reference_suggestions:
        print(f"\n{'=' * 60}")
        print("REFERENCE SUGGESTIONS")
        print(f"{'=' * 60}")
        for seg_suggestions in reference_suggestions:
            print(f"\n[Segment {seg_suggestions['segment_id']}]")
            for suggestion in seg_suggestions['suggestions']:
                print(f"  Claim: {suggestion['claim'][:70]}...")
                print(f"  Source: {suggestion['suggested_source']}")
                print(f"  Confidence: {suggestion['confidence']:.0%}")
                print()

    # Strict mode exit code
    if args.strict:
        if stats['disputed'] > 0:
            print("\nSTRICT MODE: Disputed claims found!")
            sys.exit(2)
        if stats['unverified'] > 0:
            print("\nSTRICT MODE: Unverified claims found!")
            sys.exit(1)

    # Tips
    print("\n💡 Tips:")
    if not args.web_search:
        print("  • Run with --web-search for online verification of unverified claims")
    if not args.validate_refs:
        print("  • Run with --validate-refs to check reference coverage (for long-form videos)")
    if not args.suggest_refs:
        print("  • Run with --suggest-refs --web-search to get source suggestions")


if __name__ == "__main__":
    main()
