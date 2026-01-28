# Amadeus Travel API Skill - Integration Proposal

**Author:** Mr. Mojo Risin  
**Date:** 2026-01-28  
**Status:** Draft  
**Approved by:** Pending CTO approval

---

## Executive Summary

This proposal outlines the integration of Amadeus for Developers APIs into Tailor Made's operations workflow. The skill will enable flight search, price analysis, hotel search, and destination insights to support proposal drafting and client expense optimization.

**Primary Use Case:** Research and insight generation for client travel proposals  
**Not in Scope (This Iteration):** Booking, ticketing, or payment processing

---

## Business Objectives

1. **Price Optimization** — Find best flight/hotel options across dates and routes
2. **Proposal Efficiency** — Accelerate research phase for client itineraries
3. **Competitive Edge** — Provide data-driven recommendations that demonstrate value
4. **Scalability** — Build foundation for future booking capabilities

---

## API Scope

### Core APIs (Phase 1 - MVP)

| API | Endpoint | Purpose |
|-----|----------|---------|
| **Flight Offers Search** | `GET /v2/shopping/flight-offers` | Search available flights with pricing |
| **Flight Price Analysis** | `GET /v1/analytics/itinerary-price-metrics` | Historical pricing, optimal date recommendations |
| **Airport & City Search** | `GET /v1/reference-data/locations` | Resolve location queries, find alternatives |
| **Hotel Search** | `GET /v3/shopping/hotel-offers` | Search hotel availability and pricing |
| **Hotel List by City** | `GET /v1/reference-data/locations/hotels/by-city` | Find hotels in a destination |
| **Points of Interest** | `GET /v1/reference-data/locations/pois` | Attractions, restaurants, landmarks |
| **POI by Category** | `GET /v1/reference-data/locations/pois/by-square` | Filter POIs by type and area |

### Enhanced APIs (Phase 2 - Future)

| API | Endpoint | Purpose |
|-----|----------|---------|
| **Flight Inspiration** | `GET /v1/shopping/flight-destinations` | Cheapest destinations from origin |
| **Flight Cheapest Date** | `GET /v1/shopping/flight-dates` | Find cheapest travel dates |
| **Hotel Ratings** | `GET /v2/e-reputation/hotel-sentiments` | Sentiment analysis for hotels |
| **Safe Place** | `GET /v1/safety/safety-rated-locations` | Safety ratings for destinations |
| **Travel Recommendations** | `GET /v1/reference-data/recommended-locations` | AI-powered destination suggestions |

---

## Architecture

### Skill Structure

```
skills/amadeus/
├── SKILL.md                          # Main skill documentation
├── scripts/
│   ├── flights/
│   │   ├── search_flights.py         # Flight offers search
│   │   ├── analyze_prices.py         # Price analysis & trends
│   │   └── find_airports.py          # Airport/city lookup
│   ├── hotels/
│   │   ├── search_hotels.py          # Hotel availability search
│   │   └── list_hotels.py            # Hotels by destination
│   ├── destinations/
│   │   ├── points_of_interest.py     # POI search
│   │   └── destination_info.py       # Combined destination data
│   └── lib/
│       ├── __init__.py
│       ├── client.py                 # Amadeus API client wrapper
│       ├── auth.py                   # Authentication handling
│       ├── cache.py                  # Response caching
│       └── models.py                 # Data models & validation
└── references/
    ├── api-reference.md              # API endpoint documentation
    ├── iata-codes.md                 # Common airport/city codes
    └── error-handling.md             # Error codes & recovery
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Tailor Made Workflow                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Client Request ──▶ Mr. Mojo Risin ──▶ Amadeus Skill               │
│                           │                   │                     │
│                           │                   ▼                     │
│                           │         ┌─────────────────┐             │
│                           │         │  API Client     │             │
│                           │         │  (lib/client.py)│             │
│                           │         └────────┬────────┘             │
│                           │                  │                      │
│                           │         ┌────────▼────────┐             │
│                           │         │  Amadeus APIs   │             │
│                           │         │  (External)     │             │
│                           │         └────────┬────────┘             │
│                           │                  │                      │
│                           │         ┌────────▼────────┐             │
│                           │         │  Response Cache │             │
│                           │         │  (TTL: 15 min)  │             │
│                           │         └────────┬────────┘             │
│                           │                  │                      │
│                           ◀──────────────────┘                      │
│                           │                                         │
│                           ▼                                         │
│   Proposal Draft ◀── Analysis & Formatting                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Credential Management

| Requirement | Implementation |
|-------------|----------------|
| **Storage** | Environment variables only (`AMADEUS_API_KEY`, `AMADEUS_API_SECRET`) |
| **Never** | Hardcoded in scripts, logged, or stored in version control |
| **Access** | Credentials loaded at runtime via `lib/auth.py` |
| **Rotation** | Support credential refresh without code changes |

### Authentication Flow

```python
# lib/auth.py - Conceptual implementation
class AmadeusAuth:
    """
    OAuth 2.0 Client Credentials flow.
    Tokens cached in memory with automatic refresh.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('AMADEUS_API_KEY')
        self.api_secret = os.environ.get('AMADEUS_API_SECRET')
        self._token = None
        self._token_expiry = None
        
        if not self.api_key or not self.api_secret:
            raise SecurityError("Amadeus credentials not configured")
    
    def get_token(self) -> str:
        """Get valid access token, refreshing if needed."""
        if self._is_token_valid():
            return self._token
        return self._refresh_token()
    
    def _refresh_token(self) -> str:
        """Request new token from Amadeus OAuth endpoint."""
        # Token endpoint: https://api.amadeus.com/v1/security/oauth2/token
        # Grant type: client_credentials
        # Returns: access_token with expiry
        pass
```

### API Security Controls

| Control | Description |
|---------|-------------|
| **Rate Limiting** | Respect Amadeus rate limits; implement exponential backoff |
| **Request Validation** | Validate all inputs before API calls |
| **Response Sanitization** | Strip sensitive data before logging or caching |
| **TLS Only** | All API calls over HTTPS (enforced) |
| **Error Handling** | Never expose raw API errors to external surfaces |

### Data Handling

| Data Type | Handling |
|-----------|----------|
| **API Responses** | Cache in memory only (TTL: 15 min), no disk persistence |
| **Search Queries** | Log sanitized queries for debugging (no PII) |
| **Pricing Data** | May be included in proposals (client-facing) |
| **Client Data** | Never sent to Amadeus APIs without explicit consent |

---

## Compliance Documentation

### Data Processing

| Aspect | Details |
|--------|---------|
| **Data Source** | Amadeus GDS (Global Distribution System) |
| **Data Types** | Flight schedules, pricing, hotel availability, POI data |
| **Personal Data** | None collected or transmitted in research phase |
| **Data Retention** | In-memory cache only; no persistent storage |
| **Third-Party Sharing** | Amadeus only; no other third parties |

### Amadeus Terms Compliance

| Requirement | Our Implementation |
|-------------|-------------------|
| **API Key Security** | Environment variables, never committed |
| **Rate Limits** | Client-side throttling with backoff |
| **Attribution** | Display "Powered by Amadeus" where required |
| **Usage Restrictions** | Research/display only; no booking in this iteration |
| **Test vs Production** | Clear environment separation |

### Audit Trail

All API interactions will be logged with:
- Timestamp
- Endpoint called
- Request parameters (sanitized)
- Response status
- Latency metrics

Logs stored in: `logs/amadeus/YYYY-MM-DD.log`  
Retention: 90 days  
Format: JSON lines

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Deliverables:**
1. Skill directory structure created
2. `lib/client.py` - Core API client with auth
3. `lib/auth.py` - OAuth 2.0 token management
4. `lib/cache.py` - In-memory response caching
5. Environment setup documentation

**Security Checkpoint:**
- [ ] Credential management reviewed
- [ ] No secrets in codebase
- [ ] TLS enforcement verified

### Phase 2: Flight APIs (Week 2)

**Deliverables:**
1. `scripts/flights/search_flights.py`
2. `scripts/flights/analyze_prices.py`
3. `scripts/flights/find_airports.py`
4. Unit tests for flight scripts

**Acceptance Criteria:**
- Search flights by route and date
- Compare prices across date ranges
- Resolve city names to airport codes
- Handle multi-city queries

### Phase 3: Hotel APIs (Week 3)

**Deliverables:**
1. `scripts/hotels/search_hotels.py`
2. `scripts/hotels/list_hotels.py`
3. Unit tests for hotel scripts

**Acceptance Criteria:**
- Search hotels by destination and dates
- Filter by price range and rating
- Return availability and pricing

### Phase 4: Destinations & POI (Week 4)

**Deliverables:**
1. `scripts/destinations/points_of_interest.py`
2. `scripts/destinations/destination_info.py`
3. Integration tests
4. Complete SKILL.md documentation

**Acceptance Criteria:**
- Find POIs by location
- Filter by category (restaurants, attractions, etc.)
- Combine flight + hotel + POI for destination overview

### Phase 5: Integration & Testing (Week 5)

**Deliverables:**
1. End-to-end workflow testing
2. Notion integration (if applicable)
3. Performance optimization
4. Final documentation review

**Security Review:**
- [ ] Penetration testing (API client)
- [ ] Credential rotation tested
- [ ] Error handling audit
- [ ] Logging sanitization verified

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| API rate limits exceeded | Medium | Low | Implement caching, backoff |
| Credentials exposed | Low | Critical | Env vars only, pre-commit hooks |
| Amadeus API changes | Low | Medium | Version pinning, monitoring |
| Pricing data stale | Medium | Low | Short cache TTL, refresh on demand |
| Test/Prod environment mix-up | Low | High | Clear env separation, different credentials |

---

## Dependencies

### External
- Amadeus for Developers account (free tier for test, certification for production)
- Python 3.10+
- `requests` or `httpx` for HTTP client
- `pydantic` for data validation (optional)

### Internal
- Clawdbot skill infrastructure
- Environment variable configuration
- Logging infrastructure

---

## Success Metrics

| Metric | Target |
|--------|--------|
| API response time (avg) | < 2 seconds |
| Search success rate | > 95% |
| Cache hit rate | > 60% for repeated queries |
| Proposal research time reduction | 50% vs manual |

---

## Open Questions

1. **Notion Integration** — Should results feed directly into Notion proposal templates?
2. **Multi-currency** — Display prices in client's preferred currency?
3. **Caching Strategy** — Redis for shared cache across sessions, or in-memory per-session?
4. **Historical Data** — Store past searches for trend analysis?

---

## Appendix A: Environment Configuration

```bash
# Required environment variables
export AMADEUS_API_KEY="your_api_key_here"
export AMADEUS_API_SECRET="your_api_secret_here"

# Optional configuration
export AMADEUS_ENV="test"  # or "production"
export AMADEUS_LOG_LEVEL="INFO"
export AMADEUS_CACHE_TTL="900"  # seconds
```

---

## Appendix B: Example Outputs

### Flight Search Result (JSON)

```json
{
  "search": {
    "origin": "BCN",
    "destination": "JFK",
    "date": "2026-03-15",
    "passengers": 2
  },
  "results": [
    {
      "airline": "Iberia",
      "flight": "IB6251",
      "departure": "10:30",
      "arrival": "13:45",
      "duration": "9h 15m",
      "stops": 0,
      "price_per_person": 485.00,
      "total_price": 970.00,
      "currency": "EUR",
      "cabin": "economy"
    }
  ],
  "price_analysis": {
    "trend": "typical",
    "cheapest_nearby_date": "2026-03-12",
    "cheapest_price": 420.00
  },
  "metadata": {
    "fetched_at": "2026-01-28T14:30:00Z",
    "source": "amadeus",
    "cache_hit": false
  }
}
```

### Hotel Search Result (JSON)

```json
{
  "search": {
    "destination": "New York",
    "check_in": "2026-03-15",
    "check_out": "2026-03-20",
    "guests": 2
  },
  "results": [
    {
      "name": "The Standard High Line",
      "rating": 4,
      "location": "Meatpacking District",
      "price_per_night": 285.00,
      "total_price": 1425.00,
      "currency": "USD",
      "amenities": ["wifi", "gym", "restaurant"]
    }
  ],
  "metadata": {
    "fetched_at": "2026-01-28T14:32:00Z",
    "source": "amadeus"
  }
}
```

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| CTO | Álv | | Pending |
| Engineer | Mr. Mojo Risin | 2026-01-28 | ✓ |

---

*Document Version: 1.0*  
*Last Updated: 2026-01-28*
