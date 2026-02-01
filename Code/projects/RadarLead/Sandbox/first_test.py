import asyncio
from playwright_stealth import stealth # Import the base 'stealth'
from playwright.async_api import async_playwright

async def run_radar_test(city, category):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # FIX: Using the standard 'stealth' function
        await stealth(page)
        
        print(f"📡 Radar Scanning: {category} in {city}...")
        
        # Navigate to Google Maps
        search_query = f"{category} in {city}"
        await page.goto(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}")
        
        try:
            # Wait for the result list to load
            await page.wait_for_selector('div[role="feed"]', timeout=10000)
            await asyncio.sleep(2) # Brief pause for UI stability
            
            # Find listing cards
            listings = await page.locator('div[role="article"]').all()
            
            leads = []
            
            for listing in listings[:10]:
                try:
                    # Robust Name Selection: Targets the primary heading in the card
                    name = await listing.locator('div.qBF1Pd, h3').first.inner_text()
                    
                    # Check for Website
                    has_website = await listing.locator('a[aria-label*="website"]').count() > 0
                    
                    if not has_website:
                        # Try to grab reviews
                        aria_label = await listing.locator('span[aria-label*="stars"]').get_attribute("aria-label")
                        
                        leads.append({
                            "name": name,
                            "info": aria_label if aria_label else "No reviews found"
                        })
                        print(f"🚩 FOUND LEAD: {name}")
                    else:
                        print(f"✅ Has Website: {name}")

                except Exception:
                    continue

            print("\n--- RADAR SUMMARY ---")
            if not leads:
                print("No leads found in this sweep.")
            for lead in leads:
                print(f"- {lead['name']} ({lead['info']})")
                
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_radar_test("Montreal", "Plumbers"))