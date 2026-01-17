#!/usr/bin/env python3
"""
Load penny stocks from Polygon.io into the database.
Run with: python -m app.scripts.load_penny_stocks
"""

import asyncio
import httpx
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Stock
from app.database import Base


POLYGON_BASE_URL = "https://api.polygon.io"


async def fetch_tickers(api_key: str, max_price: float = 5.0):
    """Fetch all tickers from Polygon and filter for penny stocks."""
    tickers = []
    next_url = f"{POLYGON_BASE_URL}/v3/reference/tickers?market=stocks&active=true&limit=1000&apiKey={api_key}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        page = 0
        while next_url and page < 50:  # Limit pages to avoid rate limits
            page += 1
            print(f"Fetching page {page}...")

            try:
                response = await client.get(next_url)
                response.raise_for_status()
                data = response.json()

                for ticker in data.get("results", []):
                    tickers.append({
                        "symbol": ticker.get("ticker"),
                        "name": ticker.get("name"),
                        "exchange": ticker.get("primary_exchange"),
                        "market_tier": ticker.get("market", ""),
                        "cik": ticker.get("cik"),
                    })

                # Get next page URL
                next_url = data.get("next_url")
                if next_url:
                    next_url = f"{next_url}&apiKey={api_key}"

                # Rate limiting - Polygon free tier is 5 req/min
                await asyncio.sleep(0.5)

            except httpx.HTTPStatusError as e:
                print(f"HTTP error: {e}")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

    print(f"Fetched {len(tickers)} total tickers")
    return tickers


async def get_stock_price(client: httpx.AsyncClient, symbol: str, api_key: str) -> dict:
    """Get current price for a stock."""
    try:
        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{symbol}/prev?apiKey={api_key}"
        response = await client.get(url)

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                return {
                    "current_price": results[0].get("c"),  # close
                    "previous_close": results[0].get("o"),  # open
                    "day_high": results[0].get("h"),
                    "day_low": results[0].get("l"),
                    "volume": results[0].get("v"),
                }
    except Exception as e:
        pass
    return {}


async def load_penny_stocks(api_key: str, db_url: str):
    """Main function to load penny stocks into database."""

    print("=" * 50)
    print("Penny Stock Loader")
    print("=" * 50)

    # Create database connection
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Fetch all tickers
    print("\nFetching tickers from Polygon.io...")
    all_tickers = await fetch_tickers(api_key)

    if not all_tickers:
        print("No tickers fetched. Check your API key.")
        return

    # Filter and add prices
    print("\nFetching prices for penny stocks...")
    penny_stocks = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, ticker in enumerate(all_tickers):
            symbol = ticker["symbol"]

            # Skip certain types
            if not symbol or len(symbol) > 5:
                continue
            if any(c in symbol for c in ['.', '-', '/']):
                continue

            # Get price
            price_data = await get_stock_price(client, symbol, api_key)

            if price_data and price_data.get("current_price"):
                price = price_data["current_price"]

                # Filter for penny stocks (under $5)
                if 0.01 <= price <= 5.0:
                    ticker.update(price_data)
                    penny_stocks.append(ticker)

                    if len(penny_stocks) % 50 == 0:
                        print(f"Found {len(penny_stocks)} penny stocks...")

            # Rate limiting
            if i % 5 == 0:
                await asyncio.sleep(1)  # 5 requests per second max

            # Limit for free tier
            if len(penny_stocks) >= 500:
                print("Reached 500 penny stocks limit for free tier")
                break

    print(f"\nFound {len(penny_stocks)} penny stocks under $5")

    # Save to database
    print("\nSaving to database...")
    async with async_session() as session:
        added = 0
        updated = 0

        for stock_data in penny_stocks:
            # Check if exists
            result = await session.execute(
                select(Stock).where(Stock.symbol == stock_data["symbol"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update
                existing.current_price = stock_data.get("current_price")
                existing.previous_close = stock_data.get("previous_close")
                existing.day_high = stock_data.get("day_high")
                existing.day_low = stock_data.get("day_low")
                existing.volume = stock_data.get("volume")
                existing.last_updated = datetime.utcnow()
                updated += 1
            else:
                # Create new
                stock = Stock(
                    symbol=stock_data["symbol"],
                    name=stock_data.get("name"),
                    exchange=stock_data.get("exchange"),
                    market_tier=stock_data.get("market_tier"),
                    cik=stock_data.get("cik"),
                    current_price=stock_data.get("current_price"),
                    previous_close=stock_data.get("previous_close"),
                    day_high=stock_data.get("day_high"),
                    day_low=stock_data.get("day_low"),
                    volume=stock_data.get("volume"),
                    is_active=True,
                    is_penny_stock=True,
                    last_updated=datetime.utcnow(),
                )
                session.add(stock)
                added += 1

        await session.commit()
        print(f"Added {added} new stocks, updated {updated} existing stocks")

    print("\nDone!")
    print("=" * 50)


def main():
    """Entry point."""
    import sys

    # Get API key from environment or command line
    api_key = settings.polygon_api_key

    if not api_key or api_key == "your-polygon-api-key":
        print("Error: Polygon API key not configured")
        print("Set POLYGON_API_KEY in your .env file or run:")
        print("  python -m app.scripts.load_penny_stocks YOUR_API_KEY")

        if len(sys.argv) > 1:
            api_key = sys.argv[1]
        else:
            sys.exit(1)

    db_url = str(settings.database_url)

    asyncio.run(load_penny_stocks(api_key, db_url))


if __name__ == "__main__":
    main()
