// Run this in your terminal: node test-hiring-cafe.js
// Tests different hiring.cafe API endpoints to find what works

import fetch from "node-fetch";

const endpoints = [
  "https://hiring.cafe/api/jobs?q=data+analyst&location=montreal",
  "https://hiring.cafe/api/jobs?q=data+analyst",
  "https://hiring.cafe/api/search?q=data+analyst",
  "https://hiring.cafe/api/v1/jobs?query=data+analyst",
  "https://api.hiring.cafe/jobs?q=data+analyst",
];

console.log("Testing hiring.cafe API endpoints...\n");

for (const url of endpoints) {
  try {
    const res = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
      },
      signal: AbortSignal.timeout(5000),
    });
    const text = await res.text();
    console.log(`✅ ${url}`);
    console.log(`   Status: ${res.status}`);
    console.log(`   Response: ${text.substring(0, 150)}\n`);
  } catch (err) {
    console.log(`❌ ${url}`);
    console.log(`   Error: ${err.message}\n`);
  }
}