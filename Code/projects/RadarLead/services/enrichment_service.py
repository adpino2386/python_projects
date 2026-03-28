"""
AI Enrichment Service - RadarLead
Enriches raw business leads with AI-generated outreach insights using Claude.
"""
import os
import json
from typing import Optional, Callable
import anthropic
from dotenv import load_dotenv

load_dotenv()


class EnrichmentService:
    """Enriches business leads with AI-generated sales intelligence."""

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Add it to your .env file."
            )
        self.client = anthropic.Anthropic(api_key=key)
        self.model = "claude-sonnet-4-6"

    def enrich_lead(self, business: dict) -> dict:
        """
        Enrich a single business with AI-generated outreach data.

        Args:
            business: Raw business dict from PlacesService

        Returns:
            Dict with enrichment fields added. Never raises — returns
            {'is_enriched': False, 'enrichment_error': '...'} on failure.
        """
        try:
            types_str = (
                ", ".join(business.get("types", []))
                if business.get("types")
                else "Unknown"
            )
            prompt = f"""You are a B2B sales researcher helping a digital agency find businesses that need websites.

Analyze this business and return outreach intelligence:

Business:
- Name: {business.get('name', 'Unknown')}
- Categories: {types_str}
- Rating: {business.get('rating', 'N/A')} ({business.get('total_ratings', 0)} reviews)
- Address: {business.get('address', 'Unknown')}
- Phone: {business.get('phone', 'Not listed')}
- Price Level: {business.get('price_level', 'Unknown')}

This business has NO website. Return ONLY a valid JSON object with these exact keys:
{{
  "website_pitch": "One compelling sentence why THIS specific business needs a website (reference their type and location)",
  "decision_maker_title": "Most likely decision-maker title (Owner / Manager / Director / etc.)",
  "personalized_opener": "2-sentence cold email opener referencing something specific about their business — do NOT use the word 'website' in the opener itself",
  "lead_score": <integer 1-10, where 10 = highest priority based on review volume, rating, and business type>,
  "niche_tag": "single lowercase slug tag (e.g. restaurant, plumber, nail-salon, hotel)",
  "pain_points": ["pain point 1", "pain point 2", "pain point 3"]
}}

Return ONLY the JSON object. No markdown, no explanation, no code fences."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=700,
                messages=[{"role": "user", "content": prompt}],
            )

            raw = response.content[0].text.strip()

            # Strip accidental markdown fences
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.lower().startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            data = json.loads(raw)

            # Validate required keys exist
            required = [
                "website_pitch",
                "decision_maker_title",
                "personalized_opener",
                "lead_score",
                "niche_tag",
                "pain_points",
            ]
            for k in required:
                if k not in data:
                    raise ValueError(f"Missing key in response: {k}")

            # Clamp lead_score to valid range
            data["lead_score"] = max(1, min(10, int(data["lead_score"])))

            # Ensure pain_points is a list
            if not isinstance(data["pain_points"], list):
                data["pain_points"] = [str(data["pain_points"])]

            return {**data, "is_enriched": True, "enrichment_error": None}

        except json.JSONDecodeError as e:
            return {"is_enriched": False, "enrichment_error": f"JSON parse error: {e}"}
        except Exception as e:
            return {"is_enriched": False, "enrichment_error": str(e)}

    def enrich_leads_batch(
        self,
        businesses: list,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> list:
        """
        Enrich a list of businesses sequentially.

        Args:
            businesses: List of raw business dicts
            progress_callback: Optional callable(completed: int, total: int)

        Returns:
            List of business dicts with enrichment fields merged in.
        """
        results = []
        total = len(businesses)

        for i, biz in enumerate(businesses):
            enrichment = self.enrich_lead(biz)
            results.append({**biz, **enrichment})

            if progress_callback:
                progress_callback(i + 1, total)

        return results

    def pain_points_str(self, pain_points) -> str:
        """Format pain_points list for DB storage or display."""
        if isinstance(pain_points, list):
            return json.dumps(pain_points)
        return str(pain_points) if pain_points else "[]"
