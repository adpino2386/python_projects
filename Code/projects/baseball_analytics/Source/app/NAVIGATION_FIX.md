# Navigation Fix Explanation

## Issue 1: Top-left Menu vs Sidebar Navigation

**The Problem:** Streamlit automatically creates a navigation menu in the top-left when you have a `pages/` folder structure. This menu shows all pages, but clicking them doesn't work with our custom routing logic.

**The Solution:** 
- The top-left menu (under "main") is Streamlit's automatic navigation - it works, but shows all pages
- The "Navigate" section in the sidebar is our custom navigation - this is the one that properly routes to pages
- Both work, but the sidebar "Navigate" section is the recommended one to use as it integrates with our custom routing logic

**To Use:** Click on the radio buttons in the "Navigate" section in the sidebar (bottom left), not the links in the top-left menu.

## Issue 2: "Home" vs "Main" Page

- **"Home"** = The main landing page (our custom page)
- **"Main"** = Not a separate page - it's just the label for Streamlit's automatic navigation menu
- When you see "main" in the top-left, it's just grouping the pages - there's no separate "Main" page

The actual pages are:
- Home (landing page)
- Dashboard
- Predictions (premium)
- Comparisons (premium)  
- Standings
- Payment (login/upgrade)

