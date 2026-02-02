import asyncio
from playwright.async_api import async_playwright

async def run_radar_test(city, category, max_results=50):
    """
    Scrape Google Maps to find businesses without websites.
    
    Args:
        city: City name (e.g., "Montreal")
        category: Business type (e.g., "Plumbers")
        max_results: Maximum number of businesses to check
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print(f"📡 Radar Scanning: {category} in {city}...")
        
        # Navigate to Google Maps
        search_query = f"{category} in {city}"
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(3)  # Give Maps time to load
        
        leads = []
        checked_count = 0
        
        try:
            # Wait for the results feed to load
            await page.wait_for_selector('div[role="feed"]', timeout=15000)
            await asyncio.sleep(3)  # Allow page to fully render
            
            # Scroll to load more results
            print("📜 Scrolling to load more results...")
            scroll_container = page.locator('div[role="feed"]')
            
            previous_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 10
            
            while checked_count < max_results and scroll_attempts < max_scroll_attempts:
                # Get current listings
                listings = await page.locator('div[role="article"]').all()
                current_count = len(listings)
                
                # If no new listings loaded, try scrolling more
                if current_count == previous_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                
                previous_count = current_count
                
                # Scroll the feed container
                await scroll_container.evaluate('element => element.scrollTop = element.scrollHeight')
                await asyncio.sleep(2)  # Wait for new results to load
                
                # Break if we have enough listings
                if current_count >= max_results:
                    break
            
            # Get all loaded listings
            listings = await page.locator('div[role="article"]').all()
            print(f"📋 Found {len(listings)} listings. Checking for businesses without websites...\n")
            
            for idx, listing in enumerate(listings[:max_results], 1):
                if checked_count >= max_results:
                    break
                    
                try:
                    # Click on the listing to open details panel
                    await listing.click()
                    await asyncio.sleep(1.5)  # Wait for details panel to load
                    
                    # Extract business name from the details panel
                    name_selectors = [
                        'h1[data-attrid="title"]',
                        'h1.DUwDvf',
                        'h1.fontHeadlineLarge',
                        'h1'
                    ]
                    
                    name = None
                    for selector in name_selectors:
                        try:
                            name_elem = page.locator(selector).first
                            if await name_elem.count() > 0:
                                name = await name_elem.inner_text()
                                if name and name.strip():
                                    break
                        except:
                            continue
                    
                    if not name:
                        # Fallback: try to get name from the listing card
                        try:
                            name = await listing.locator('div.qBF1Pd, h3, div.fontHeadlineSmall').first.inner_text()
                        except:
                            print(f"⚠️  Could not extract name for listing {idx}")
                            continue
                    
                    # Check for website in the details panel
                    # Multiple ways to detect website presence
                    website_selectors = [
                        'a[data-value="Website"]',
                        'a[aria-label*="Website"]',
                        'a[href^="http"]:has-text("Website")',
                        'a:has-text("Website")',
                        'a[data-item-id="authority"]'
                    ]
                    
                    has_website = False
                    for selector in website_selectors:
                        try:
                            if await page.locator(selector).count() > 0:
                                has_website = True
                                break
                        except:
                            continue
                    
                    # Also check for http/https links in the details panel
                    if not has_website:
                        try:
                            links = await page.locator('a[href^="http"]').all()
                            # Filter out common non-website links
                            for link in links:
                                href = await link.get_attribute('href')
                                if href and 'google.com' not in href and 'maps.google.com' not in href:
                                    # Check if it's labeled as website
                                    aria_label = await link.get_attribute('aria-label')
                                    if aria_label and 'website' in aria_label.lower():
                                        has_website = True
                                        break
                        except:
                            pass
                    
                    # Extract additional info if no website
                    if not has_website:
                        business_info = {}
                        
                        # Try to get address
                        address_selectors = [
                            'button[data-item-id="address"]',
                            'button[data-value*="address"]',
                            'span[aria-label*="Address"]'
                        ]
                        for selector in address_selectors:
                            try:
                                addr_elem = page.locator(selector).first
                                if await addr_elem.count() > 0:
                                    address = await addr_elem.inner_text()
                                    if address:
                                        business_info['address'] = address
                                        break
                            except:
                                continue
                        
                        # Try to get phone
                        phone_selectors = [
                            'button[data-item-id*="phone"]',
                            'button[data-value*="phone"]',
                            'span[aria-label*="Phone"]'
                        ]
                        for selector in phone_selectors:
                            try:
                                phone_elem = page.locator(selector).first
                                if await phone_elem.count() > 0:
                                    phone = await phone_elem.inner_text()
                                    if phone:
                                        business_info['phone'] = phone
                                        break
                            except:
                                continue
                        
                        # Try to get rating
                        rating = None
                        rating_selectors = [
                            'span[aria-label*="stars"]',
                            'div.fontDisplayLarge',
                            'span[jsaction*="rating"]'
                        ]
                        for selector in rating_selectors:
                            try:
                                rating_elem = page.locator(selector).first
                                if await rating_elem.count() > 0:
                                    rating_text = await rating_elem.get_attribute('aria-label')
                                    if not rating_text:
                                        rating_text = await rating_elem.inner_text()
                                    if rating_text:
                                        rating = rating_text
                                        break
                            except:
                                continue
                        
                        lead_data = {
                            "name": name.strip(),
                            "rating": rating if rating else "No rating",
                            **business_info
                        }
                        
                        leads.append(lead_data)
                        print(f"🚩 [{len(leads)}] FOUND LEAD: {name.strip()}")
                        if business_info:
                            print(f"   📍 {business_info.get('address', 'N/A')}")
                            print(f"   📞 {business_info.get('phone', 'N/A')}")
                    else:
                        print(f"✅ [{idx}] Has Website: {name.strip()}")
                    
                    checked_count += 1
                    
                    # Close the details panel by clicking outside or pressing Escape
                    try:
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(0.5)
                    except:
                        pass
                        
                except Exception as e:
                    print(f"⚠️  Error processing listing {idx}: {str(e)[:50]}")
                    # Try to close any open panels
                    try:
                        await page.keyboard.press('Escape')
                    except:
                        pass
                    continue

            print("\n" + "="*60)
            print("--- RADAR SUMMARY ---")
            print(f"Total businesses checked: {checked_count}")
            print(f"Businesses WITHOUT websites: {len(leads)}")
            print("="*60)
            
            if not leads:
                print("❌ No leads found in this sweep.")
            else:
                print("\n📋 LEAD LIST:\n")
                for i, lead in enumerate(leads, 1):
                    print(f"{i}. {lead['name']}")
                    print(f"   Rating: {lead.get('rating', 'N/A')}")
                    if 'address' in lead:
                        print(f"   Address: {lead['address']}")
                    if 'phone' in lead:
                        print(f"   Phone: {lead['phone']}")
                    print()
                
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            return leads

if __name__ == "__main__":
    leads = asyncio.run(run_radar_test("Montreal, Quebec, Canada", "Plumbers", max_results=30))