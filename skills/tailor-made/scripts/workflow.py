#!/usr/bin/env python3
"""
Tailor Made Workflow Engine

Orchestrates RÁPIDO and PROFUNDO travel analyses using Amadeus APIs,
formats results for Telegram delivery, and documents everything in Notion.

Usage:
    # RÁPIDO analysis (quick options)
    python workflow.py rapido --from MEX --to CUN --date 2026-03-15 \
        --return-date 2026-03-20 --adults 2 --budget 30000 --currency MXN

    # PROFUNDO analysis (comprehensive)
    python workflow.py profundo --from MEX --to CUN --date 2026-03-15 \
        --return-date 2026-03-20 --adults 2 --budget 30000 --currency MXN \
        --client "Pareja joven, primera vez en Cancún" --notion

    # Parse a briefing from Mar
    python workflow.py briefing --text "Cliente: Pareja 28 años..."
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add Amadeus lib to path
AMADEUS_LIB = Path(__file__).resolve().parent.parent.parent / "amadeus" / "lib"
sys.path.insert(0, str(AMADEUS_LIB))

from client import AmadeusClient, APIError
from auth import AuthError

# Active Notion database IDs (verified accessible & not archived)
NOTION_DBS = {
    "operations": "2f7a81f6-c8ba-801b-bb52-dae3895517ee",
    "proposals": "2f7a81f6-c8ba-8026-b70b-fcf4e9e9549f",
}


def load_notion_db_ids() -> dict:
    """Load Notion DB IDs — prefers hardcoded active IDs, falls back to config file."""
    return NOTION_DBS


# ─── Formatters ───────────────────────────────────────────────────────────────

def fmt_duration(iso: str) -> str:
    if not iso:
        return ""
    d = iso.replace("PT", "")
    parts = []
    if "H" in d:
        h, d = d.split("H", 1)
        parts.append(f"{h}h")
    if "M" in d:
        m = d.replace("M", "")
        if m:
            parts.append(f"{m}m")
    return " ".join(parts)


def fmt_time(iso_dt: str) -> str:
    if not iso_dt:
        return ""
    try:
        return datetime.fromisoformat(iso_dt).strftime("%H:%M")
    except (ValueError, TypeError):
        return iso_dt


def fmt_price(amount, currency="MXN") -> str:
    try:
        return f"${float(amount):,.0f} {currency}"
    except (ValueError, TypeError):
        return f"${amount} {currency}"


# ─── Data Fetchers ────────────────────────────────────────────────────────────

def fetch_flights(client, origin, dest, date, return_date=None, adults=1,
                  children=0, seat="economy", currency=None, limit=10, direct=False):
    """Fetch and format flight offers."""
    seat_map = {"economy": "ECONOMY", "premium-economy": "PREMIUM_ECONOMY",
                "business": "BUSINESS", "first": "FIRST"}
    try:
        resp = client.search_flights(
            origin=origin, destination=dest, departure_date=date,
            return_date=return_date, adults=adults, children=children,
            travel_class=seat_map.get(seat), non_stop=direct,
            currency=currency, max_results=limit,
        )
        dicts = resp.get("dictionaries", {})
        carriers = dicts.get("carriers", {})
        aircraft = dicts.get("aircraft", {})
        offers = []
        for offer in resp.get("data", []):
            price = offer.get("price", {})
            travelers = offer.get("travelerPricings", [])
            total = float(price.get("total", 0))
            cur = price.get("currency", "EUR")
            itins = []
            for itin in offer.get("itineraries", []):
                segs = itin.get("segments", [])
                airlines = set()
                seg_list = []
                for seg in segs:
                    cc = seg.get("carrierCode", "")
                    name = carriers.get(cc, cc)
                    airlines.add(name)
                    seg_list.append({
                        "flight": f"{cc}{seg.get('number', '')}",
                        "airline": name,
                        "from": seg.get("departure", {}).get("iataCode", ""),
                        "to": seg.get("arrival", {}).get("iataCode", ""),
                        "dep": fmt_time(seg.get("departure", {}).get("at", "")),
                        "arr": fmt_time(seg.get("arrival", {}).get("at", "")),
                        "duration": fmt_duration(seg.get("duration", "")),
                    })
                stops = len(segs) - 1
                itins.append({
                    "direction": "outbound" if len(itins) == 0 else "return",
                    "duration": fmt_duration(itin.get("duration", "")),
                    "stops": stops,
                    "airlines": sorted(airlines),
                    "segments": seg_list,
                })
            cabin = "ECONOMY"
            if travelers:
                cabin = travelers[0].get("fareDetailsBySegment", [{}])[0].get("cabin", "ECONOMY")
            offers.append({
                "total": total, "per_person": round(total / max(len(travelers), 1), 2),
                "currency": cur, "cabin": cabin, "itineraries": itins,
            })
        return {"ok": True, "offers": offers}
    except (APIError, AuthError) as e:
        return {"ok": False, "error": str(e)}


def fetch_hotels(client, city, checkin, checkout, guests=1, currency=None, limit=5):
    """Fetch and format hotel offers."""
    try:
        hotels_data = client.search_hotels_by_city(city)
        hotel_ids = [h.get("hotelId") for h in hotels_data.get("data", [])[:20]]
        if not hotel_ids:
            return {"ok": True, "offers": []}
        offers_data = client.search_hotel_offers(
            hotel_ids=hotel_ids, check_in=checkin, check_out=checkout,
            adults=guests, currency=currency,
        )
        hotels = []
        for o in offers_data.get("data", [])[:limit]:
            h = o.get("hotel", {})
            room_offers = o.get("offers", [])
            best = room_offers[0] if room_offers else {}
            price = best.get("price", {})
            room = best.get("room", {})
            hotels.append({
                "name": h.get("name", "Unknown"),
                "rating": h.get("rating"),
                "city_code": h.get("cityCode", ""),
                "total": price.get("total"),
                "currency": price.get("currency", "EUR"),
                "room_type": room.get("typeEstimated", {}).get("category", ""),
                "bed_type": room.get("typeEstimated", {}).get("bedType", ""),
                "board": best.get("boardType", ""),
                "cancellation": "FREE" if best.get("policies", {}).get("cancellations") else "NON_REFUNDABLE",
            })
        return {"ok": True, "offers": hotels}
    except (APIError, AuthError) as e:
        return {"ok": False, "error": str(e)}


# ─── RÁPIDO Formatter ─────────────────────────────────────────────────────────

def format_rapido(params, flights, hotels) -> str:
    """Format RÁPIDO analysis for Telegram."""
    origin = params["origin"]
    dest = params["destination"]
    date = params["date"]
    return_date = params.get("return_date", "")
    adults = params.get("adults", 1)
    children = params.get("children", 0)
    budget = params.get("budget")
    currency = params.get("currency", "MXN")

    lines = []
    lines.append(f"🔍 RÁPIDO — {origin} → {dest}")
    lines.append("")

    # Trip info
    pax = f"{adults} adulto{'s' if adults > 1 else ''}"
    if children:
        pax += f", {children} niño{'s' if children > 1 else ''}"
    date_str = f"{date}"
    if return_date:
        date_str += f" → {return_date}"
    lines.append(f"📅 {date_str}")
    lines.append(f"👥 {pax}")
    if budget:
        lines.append(f"💵 Presupuesto: {fmt_price(budget, currency)}")
    lines.append("")

    # Flights
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("✈️ VUELOS")
    lines.append("")

    if flights.get("ok") and flights.get("offers"):
        for i, f in enumerate(flights["offers"][:3], 1):
            emoji = ["1️⃣", "2️⃣", "3️⃣"][i - 1]
            cur = f["currency"]
            lines.append(f"{emoji} {fmt_price(f['total'], cur)} total ({fmt_price(f['per_person'], cur)}/persona)")
            for itin in f["itineraries"]:
                direction = "🛫" if itin["direction"] == "outbound" else "🛬"
                airlines = ", ".join(itin["airlines"])
                stops = "Directo" if itin["stops"] == 0 else f"{itin['stops']} escala{'s' if itin['stops'] > 1 else ''}"
                lines.append(f"   {direction} {itin['duration']} · {stops}")
                lines.append(f"   {airlines}")
                for seg in itin["segments"]:
                    lines.append(f"   {seg['from']} {seg['dep']} → {seg['to']} {seg['arr']}")
            lines.append("")
    elif flights.get("error"):
        lines.append(f"⚠️ {flights['error']}")
        lines.append("")
    else:
        lines.append("Sin vuelos disponibles")
        lines.append("")

    # Hotels
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🏨 HOSPEDAJE")
    lines.append("")

    if hotels.get("ok") and hotels.get("offers"):
        for i, h in enumerate(hotels["offers"][:3], 1):
            emoji = ["1️⃣", "2️⃣", "3️⃣"][i - 1]
            rating = f" ⭐{h['rating']}" if h.get("rating") else ""
            cancel = " ✅ Cancelación gratis" if h["cancellation"] == "FREE" else ""
            lines.append(f"{emoji} {h['name']}{rating}")
            if h.get("total"):
                lines.append(f"   {fmt_price(h['total'], h['currency'])} total{cancel}")
            if h.get("room_type") or h.get("bed_type"):
                lines.append(f"   {h.get('room_type', '')} {h.get('bed_type', '')}".strip())
            lines.append("")
    elif hotels.get("error"):
        lines.append(f"⚠️ {hotels['error']}")
        lines.append("")
    else:
        lines.append("Sin hoteles disponibles")
        lines.append("")

    # Budget analysis
    if budget and flights.get("ok") and flights.get("offers"):
        best_flight = flights["offers"][0]["total"]
        best_flight_cur = flights["offers"][0]["currency"]
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 INSIGHT")
        lines.append(f"Vuelo más económico: {fmt_price(best_flight, best_flight_cur)}")
        if hotels.get("ok") and hotels.get("offers") and hotels["offers"][0].get("total"):
            best_hotel = float(hotels["offers"][0]["total"])
            hotel_cur = hotels["offers"][0]["currency"]
            estimated = best_flight + best_hotel
            lines.append(f"Hotel más accesible: {fmt_price(best_hotel, hotel_cur)}")
            lines.append(f"Estimado total: {fmt_price(estimated, best_flight_cur)} (vuelo + hotel)")
        lines.append("")

    lines.append("¿Quieres que profundice en alguna de estas opciones?")

    return "\n".join(lines)


# ─── PROFUNDO Formatter ───────────────────────────────────────────────────────

def format_profundo(params, flights, hotels) -> str:
    """Format PROFUNDO analysis for Telegram."""
    origin = params["origin"]
    dest = params["destination"]
    date = params["date"]
    return_date = params.get("return_date", "")
    adults = params.get("adults", 1)
    children = params.get("children", 0)
    budget = params.get("budget")
    currency = params.get("currency", "MXN")
    client_desc = params.get("client", "")

    lines = []
    lines.append(f"🔎 ANÁLISIS PROFUNDO — {origin} → {dest}")
    lines.append("")

    # Executive summary
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📋 RESUMEN EJECUTIVO")
    if budget:
        lines.append(f"• Presupuesto: {fmt_price(budget, currency)}")
    lines.append(f"• Fechas: {date}" + (f" → {return_date}" if return_date else ""))
    pax = f"{adults} adulto{'s' if adults > 1 else ''}"
    if children:
        pax += f", {children} niño{'s' if children > 1 else ''}"
    lines.append(f"• Viajeros: {pax}")
    if client_desc:
        lines.append(f"• Perfil: {client_desc}")
    lines.append("")

    # Flights
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("✈️ VUELOS")
    lines.append("")

    if flights.get("ok") and flights.get("offers"):
        labels = ["Recomendada", "Alternativa", "Premium", "Opción 4", "Opción 5"]
        for i, f in enumerate(flights["offers"][:5], 1):
            cur = f["currency"]
            label = labels[i - 1] if i <= len(labels) else f"Opción {i}"
            cabin = f["cabin"].replace("_", " ").title()
            lines.append(f"[Opción {i} — {label}]")
            lines.append(f"💰 {fmt_price(f['total'], cur)} total ({fmt_price(f['per_person'], cur)}/persona)")
            lines.append(f"Cabina: {cabin}")
            for itin in f["itineraries"]:
                direction = "🛫 Ida" if itin["direction"] == "outbound" else "🛬 Vuelta"
                stops = "Directo" if itin["stops"] == 0 else f"{itin['stops']} escala{'s' if itin['stops'] > 1 else ''}"
                airlines = ", ".join(itin["airlines"])
                lines.append(f"{direction}: {itin['duration']} · {stops} · {airlines}")
                for seg in itin["segments"]:
                    lines.append(f"  {seg['flight']}: {seg['from']} {seg['dep']} → {seg['to']} {seg['arr']} ({seg['duration']})")
            lines.append("")
    elif flights.get("error"):
        lines.append(f"⚠️ Error en búsqueda: {flights['error']}")
        lines.append("")
    else:
        lines.append("Sin vuelos disponibles para estas fechas.")
        lines.append("")

    # Hotels
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🏨 HOSPEDAJE")
    lines.append("")

    if hotels.get("ok") and hotels.get("offers"):
        labels = ["Mejor valor", "Premium", "Económico", "Alternativa", "Lujo"]
        for i, h in enumerate(hotels["offers"][:5], 1):
            label = labels[i - 1] if i <= len(labels) else f"Opción {i}"
            rating = f"⭐{h['rating']}" if h.get("rating") else ""
            cancel = "✅ Cancelación gratis" if h["cancellation"] == "FREE" else "⚠️ No reembolsable"
            lines.append(f"[{label}] {h['name']} {rating}")
            if h.get("total"):
                lines.append(f"💰 {fmt_price(h['total'], h['currency'])} total")
            room_info = " ".join(filter(None, [h.get("room_type", ""), h.get("bed_type", "")]))
            if room_info:
                lines.append(f"🛏️ {room_info}")
            lines.append(f"📋 {cancel}")
            lines.append("")
    elif hotels.get("error"):
        lines.append(f"⚠️ Error en búsqueda: {hotels['error']}")
        lines.append("")
    else:
        lines.append("Sin hoteles disponibles para estas fechas.")
        lines.append("")

    # Cost breakdown
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💰 DESGLOSE DE COSTOS")
    lines.append("")

    if flights.get("ok") and flights.get("offers"):
        best_f = flights["offers"][0]
        f_cur = best_f["currency"]
        lines.append(f"Vuelos ({adults} persona{'s' if adults > 1 else ''}): {fmt_price(best_f['total'], f_cur)}")

        if hotels.get("ok") and hotels.get("offers") and hotels["offers"][0].get("total"):
            best_h = hotels["offers"][0]
            h_total = float(best_h["total"])
            h_cur = best_h["currency"]
            lines.append(f"Hospedaje: {fmt_price(h_total, h_cur)}")
            lines.append("Actividades: Por definir")
            lines.append("Traslados: Por definir")
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            estimated = best_f["total"] + h_total
            lines.append(f"TOTAL ESTIMADO: {fmt_price(estimated, f_cur)}")

            if budget:
                diff = budget - estimated
                if diff > 0:
                    lines.append(f"✅ Dentro de presupuesto (sobran ~{fmt_price(diff, currency)})")
                else:
                    lines.append(f"⚠️ Excede presupuesto por ~{fmt_price(abs(diff), currency)}")
        lines.append("")

    # Recommendation
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📝 MI RECOMENDACIÓN")
    lines.append("")
    if flights.get("ok") and flights.get("offers"):
        best = flights["offers"][0]
        airline = best["itineraries"][0]["airlines"][0] if best["itineraries"] and best["itineraries"][0]["airlines"] else "N/A"
        stops_info = best["itineraries"][0]["stops"] if best["itineraries"] else 0
        stops_txt = "directo" if stops_info == 0 else f"con {stops_info} escala"
        lines.append(
            f"La opción 1 ({airline}, {stops_txt}) ofrece el mejor balance entre "
            f"precio y comodidad para este perfil de viajero."
        )
    else:
        lines.append("Se requiere ajustar fechas o destino para encontrar mejores opciones.")
    lines.append("")
    lines.append("¿Procedemos con esta opción? ¿Ajustamos algo?")

    return "\n".join(lines)


# ─── Notion Documentation ────────────────────────────────────────────────────

def document_in_notion(params, flights, hotels, analysis_type, formatted_text) -> dict:
    """Create Notion entries for the analysis."""
    try:
        from notion_helper import NotionHelper, NotionError
    except ImportError:
        return {"ok": False, "error": "notion_helper not available"}

    try:
        notion = NotionHelper()
    except Exception as e:
        return {"ok": False, "error": str(e)}

    db_ids = load_notion_db_ids()
    results = {"ok": True, "entries": {}}

    origin = params["origin"]
    dest = params["destination"]
    date = params["date"]
    title = f"{origin} → {dest} ({date})"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Create Analysis entry in operations DB
    analysis_db = db_ids.get("operations")
    if analysis_db:
        try:
            page = notion.create_page(
                parent_id=analysis_db,
                title=f"[{analysis_type.upper()}] {title}",
                is_database_parent=True,
            )
            page_id = page["id"]

            blocks = []
            blocks.append(NotionHelper.heading_block(f"Análisis {analysis_type.upper()}", level=1))
            blocks.append(NotionHelper.paragraph_block(f"Fecha: {now}"))
            blocks.append(NotionHelper.divider_block())

            # Search params
            blocks.append(NotionHelper.heading_block("Parámetros", level=2))
            blocks.append(NotionHelper.code_block(json.dumps(params, indent=2, ensure_ascii=False), language="json"))
            blocks.append(NotionHelper.divider_block())

            # Formatted analysis
            blocks.append(NotionHelper.heading_block("Análisis", level=2))
            # Split long text into chunks (Notion has 2000 char limit per block)
            for chunk in _split_text(formatted_text, 1900):
                blocks.append(NotionHelper.paragraph_block(chunk))
            blocks.append(NotionHelper.divider_block())

            # Raw data
            blocks.append(NotionHelper.heading_block("Datos Crudos", level=2))
            raw = {
                "flights_count": len(flights.get("offers", [])) if flights.get("ok") else 0,
                "hotels_count": len(hotels.get("offers", [])) if hotels.get("ok") else 0,
                "errors": [],
            }
            if not flights.get("ok"):
                raw["errors"].append(flights.get("error", "flights failed"))
            if not hotels.get("ok"):
                raw["errors"].append(hotels.get("error", "hotels failed"))
            blocks.append(NotionHelper.code_block(json.dumps(raw, indent=2), language="json"))

            notion.append_blocks(page_id, blocks)
            results["entries"]["analysis"] = {
                "id": page_id,
                "url": f"https://notion.so/{page_id.replace('-', '')}",
            }
        except Exception as e:
            results["entries"]["analysis"] = {"error": str(e)}

    # Create Proposal entry
    proposals_db = db_ids.get("proposals")
    if proposals_db:
        try:
            page = notion.create_page(
                parent_id=proposals_db,
                title=f"Propuesta: {title}",
                is_database_parent=True,
            )
            page_id = page["id"]

            blocks = []
            blocks.append(NotionHelper.heading_block(f"Propuesta — {title}", level=1))
            blocks.append(NotionHelper.paragraph_block(f"Tipo: {analysis_type.upper()} | Fecha: {now}"))
            blocks.append(NotionHelper.divider_block())

            for chunk in _split_text(formatted_text, 1900):
                blocks.append(NotionHelper.paragraph_block(chunk))

            notion.append_blocks(page_id, blocks)
            results["entries"]["proposal"] = {
                "id": page_id,
                "url": f"https://notion.so/{page_id.replace('-', '')}",
            }
        except Exception as e:
            results["entries"]["proposal"] = {"error": str(e)}

    return results


def _split_text(text: str, max_len: int = 1900) -> list:
    """Split text into chunks respecting line boundaries."""
    chunks = []
    current = []
    current_len = 0
    for line in text.split("\n"):
        if current_len + len(line) + 1 > max_len and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_rapido(args) -> dict:
    """Execute RÁPIDO analysis."""
    client = AmadeusClient()
    params = {
        "origin": args.origin.upper(),
        "destination": args.destination.upper(),
        "date": args.date,
        "return_date": args.return_date,
        "adults": args.adults,
        "children": args.children,
        "budget": args.budget,
        "currency": args.currency or "MXN",
        "client": getattr(args, "client", ""),
    }

    flights = fetch_flights(
        client, params["origin"], params["destination"], params["date"],
        return_date=params["return_date"], adults=params["adults"],
        children=params["children"], currency=params["currency"], limit=5,
    )
    hotels = fetch_hotels(
        client, params["destination"], params["date"],
        params["return_date"] or params["date"],
        guests=params["adults"], currency=params["currency"], limit=3,
    )

    formatted = format_rapido(params, flights, hotels)

    result = {
        "success": True,
        "type": "rapido",
        "formatted": formatted,
        "data": {
            "flights": flights,
            "hotels": hotels,
        },
        "params": params,
    }

    # Notion documentation
    if getattr(args, "notion", False):
        notion_result = document_in_notion(params, flights, hotels, "rápido", formatted)
        result["notion"] = notion_result

    return result


def cmd_profundo(args) -> dict:
    """Execute PROFUNDO analysis."""
    client = AmadeusClient()
    params = {
        "origin": args.origin.upper(),
        "destination": args.destination.upper(),
        "date": args.date,
        "return_date": args.return_date,
        "adults": args.adults,
        "children": args.children,
        "budget": args.budget,
        "currency": args.currency or "MXN",
        "client": getattr(args, "client", ""),
    }

    # More results for profundo
    flights = fetch_flights(
        client, params["origin"], params["destination"], params["date"],
        return_date=params["return_date"], adults=params["adults"],
        children=params["children"], currency=params["currency"], limit=10,
    )
    hotels = fetch_hotels(
        client, params["destination"], params["date"],
        params["return_date"] or params["date"],
        guests=params["adults"], currency=params["currency"], limit=5,
    )

    formatted = format_profundo(params, flights, hotels)

    result = {
        "success": True,
        "type": "profundo",
        "formatted": formatted,
        "data": {
            "flights": flights,
            "hotels": hotels,
        },
        "params": params,
    }

    # Notion documentation
    if getattr(args, "notion", False):
        notion_result = document_in_notion(params, flights, hotels, "profundo", formatted)
        result["notion"] = notion_result

    return result


# ─── CLI ──────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        description="Tailor Made Workflow Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Shared args
    def add_common(p):
        p.add_argument("--from", dest="origin", required=True, help="Origin IATA code")
        p.add_argument("--to", dest="destination", required=True, help="Destination IATA code")
        p.add_argument("--date", required=True, help="Departure date YYYY-MM-DD")
        p.add_argument("--return-date", dest="return_date", help="Return date YYYY-MM-DD")
        p.add_argument("--adults", type=int, default=1)
        p.add_argument("--children", type=int, default=0)
        p.add_argument("--budget", type=float, help="Budget amount")
        p.add_argument("--currency", default="MXN")
        p.add_argument("--client", default="", help="Client description")
        p.add_argument("--notion", action="store_true", help="Document in Notion")
        p.add_argument("--json", action="store_true", help="Output full JSON (default: formatted text)")

    rap = sub.add_parser("rapido", help="Quick RÁPIDO analysis (2-3 options)")
    add_common(rap)

    prof = sub.add_parser("profundo", help="Comprehensive PROFUNDO analysis")
    add_common(prof)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "rapido":
            result = cmd_rapido(args)
        elif args.command == "profundo":
            result = cmd_profundo(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        if getattr(args, "json", False):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Print formatted text (for Telegram)
            print(result["formatted"])
            # Print Notion links if created
            notion = result.get("notion", {})
            if notion.get("ok"):
                for name, entry in notion.get("entries", {}).items():
                    if "url" in entry:
                        print(f"\n📝 Notion ({name}): {entry['url']}", file=sys.stderr)

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
