/**
 * Local Playwright-based property scraper.
 * Runs in the Electron main process using the user's residential IP.
 */

const { chromium } = require('playwright');

// Detect source from URL
function detectSource(url) {
  const hostname = new URL(url).hostname.toLowerCase();
  if (hostname.includes('zillow.com')) return 'zillow';
  if (hostname.includes('redfin.com')) return 'redfin';
  if (hostname.includes('realtor.com')) return 'realtor';
  return null;
}

// Main scraping function
async function scrapeProperty(url) {
  const source = detectSource(url);
  if (!source) {
    throw new Error(`Unsupported URL: ${url}`);
  }

  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--disable-gpu',
    ],
  });

  try {
    // Create context with user agent and viewport
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1920, height: 1080 },
    });

    const page = await context.newPage();

    // Navigate to the page
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

    // Wait a bit for dynamic content
    await page.waitForTimeout(2000);

    // Parse based on source
    let data;
    switch (source) {
      case 'zillow':
        data = await scrapeZillow(page, url);
        break;
      case 'redfin':
        data = await scrapeRedfin(page, url);
        break;
      case 'realtor':
        data = await scrapeRealtor(page, url);
        break;
    }

    return { ...data, source, source_url: url };
  } finally {
    await browser.close();
  }
}

// Zillow scraper
async function scrapeZillow(page, url) {
  // Try to extract JSON-LD data first
  const jsonLd = await page.evaluate(() => {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
      try {
        const data = JSON.parse(script.textContent);
        if (data['@type'] === 'RealEstateListing') {
          return data;
        }
      } catch (e) {}
    }
    return null;
  });

  if (jsonLd) {
    const itemOffered = jsonLd.offers?.itemOffered || {};
    const address = itemOffered.address || {};

    return {
      address: address.streetAddress || '',
      city: address.addressLocality || '',
      state: address.addressRegion || '',
      zip_code: address.postalCode || '',
      list_price: jsonLd.offers?.price || 0,
      bedrooms: itemOffered.numberOfBedrooms || 0,
      bathrooms: await extractBathroomsFromPage(page),
      sqft: itemOffered.floorSize?.value || null,
      property_type: 'single_family_home',
      latitude: itemOffered.geo?.latitude || null,
      longitude: itemOffered.geo?.longitude || null,
    };
  }

  // Fallback: extract from page content
  return await extractFromPage(page);
}

// Redfin scraper
async function scrapeRedfin(page, url) {
  // Try to extract from the page
  const data = await page.evaluate(() => {
    // Redfin puts data in various places
    const getPriceText = () => {
      const priceEl = document.querySelector('[data-rf-test-id="abp-price"]') ||
                      document.querySelector('.statsValue') ||
                      document.querySelector('.price');
      return priceEl?.textContent || '';
    };

    const getAddressText = () => {
      const addressEl = document.querySelector('[data-rf-test-id="abp-streetLine"]') ||
                        document.querySelector('.street-address');
      return addressEl?.textContent || '';
    };

    const getCityStateZip = () => {
      const el = document.querySelector('[data-rf-test-id="abp-cityStateZip"]') ||
                 document.querySelector('.city-state-zip');
      return el?.textContent || '';
    };

    const getBeds = () => {
      const el = document.querySelector('[data-rf-test-id="abp-beds"]') ||
                 document.querySelector('.beds');
      const match = el?.textContent?.match(/(\d+)/);
      return match ? parseInt(match[1]) : 0;
    };

    const getBaths = () => {
      const el = document.querySelector('[data-rf-test-id="abp-baths"]') ||
                 document.querySelector('.baths');
      const match = el?.textContent?.match(/(\d+\.?\d*)/);
      return match ? parseFloat(match[1]) : 0;
    };

    const getSqft = () => {
      const el = document.querySelector('[data-rf-test-id="abp-sqFt"]') ||
                 document.querySelector('.sqft');
      const match = el?.textContent?.replace(/,/g, '').match(/(\d+)/);
      return match ? parseInt(match[1]) : null;
    };

    const priceText = getPriceText();
    const price = parseInt(priceText.replace(/[^0-9]/g, '')) || 0;

    const address = getAddressText();
    const cityStateZip = getCityStateZip();
    const cszMatch = cityStateZip.match(/(.+),\s*([A-Z]{2})\s*(\d{5})/);

    return {
      address,
      city: cszMatch?.[1]?.trim() || '',
      state: cszMatch?.[2] || '',
      zip_code: cszMatch?.[3] || '',
      list_price: price,
      bedrooms: getBeds(),
      bathrooms: getBaths(),
      sqft: getSqft(),
      property_type: 'single_family_home',
    };
  });

  return data;
}

// Realtor.com scraper
async function scrapeRealtor(page, url) {
  // Try JSON-LD first
  const jsonLd = await page.evaluate(() => {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
      try {
        const data = JSON.parse(script.textContent);
        if (data['@type'] === 'SingleFamilyResidence' || data['@type'] === 'Product') {
          return data;
        }
      } catch (e) {}
    }
    return null;
  });

  if (jsonLd) {
    const address = jsonLd.address || {};
    return {
      address: address.streetAddress || '',
      city: address.addressLocality || '',
      state: address.addressRegion || '',
      zip_code: address.postalCode || '',
      list_price: jsonLd.offers?.price || 0,
      bedrooms: jsonLd.numberOfBedrooms || jsonLd.numberOfRooms || 0,
      bathrooms: jsonLd.numberOfBathroomsTotal || 0,
      sqft: null,
      property_type: 'single_family_home',
    };
  }

  // Fallback
  return await extractFromPage(page);
}

// Helper: extract bathrooms from page (Zillow often omits from JSON-LD)
async function extractBathroomsFromPage(page) {
  return await page.evaluate(() => {
    const text = document.body.innerText;
    // Use word boundary and limit to 1-2 digits to avoid matching prices
    const match = text.match(/\b(\d{1,2}(?:\.\d)?)\s*(?:ba|baths?|bathroom)/i);
    let baths = match ? parseFloat(match[1]) : 0;
    // Sanity check: if > 10, likely a parsing error
    if (baths > 10) {
      // Common error: "3.0" -> "30", fix it
      if ([10, 15, 20, 25, 30, 35, 40, 45, 50].includes(baths)) {
        baths = baths / 10;
      } else {
        baths = 0;
      }
    }
    return baths;
  });
}

// Generic fallback extractor
async function extractFromPage(page) {
  return await page.evaluate(() => {
    const text = document.body.innerText;
    const title = document.title;

    // Extract address from title
    const addrMatch = title.match(/(.+?),\s*(.+?),\s*([A-Z]{2})\s*(\d{5})/);

    // Extract price
    const priceMatch = text.match(/\$[\d,]+/);
    const price = priceMatch ? parseInt(priceMatch[0].replace(/[^0-9]/g, '')) : 0;

    // Extract beds/baths with word boundaries and digit limits
    const bedsMatch = text.match(/\b(\d{1,2})\s*(?:bd|beds?|bedroom|bdrm|BR)\b/i);
    const bathsMatch = text.match(/\b(\d{1,2}(?:\.\d)?)\s*(?:ba|baths?|bathroom)\b/i);

    let beds = bedsMatch ? parseInt(bedsMatch[1]) : 0;
    let baths = bathsMatch ? parseFloat(bathsMatch[1]) : 0;

    // Sanity checks
    if (beds > 20) beds = 0;
    if (baths > 10) {
      // Common error: "3.0" -> "30", fix it
      if ([10, 15, 20, 25, 30, 35, 40, 45, 50].includes(baths)) {
        baths = baths / 10;
      } else {
        baths = 0;
      }
    }

    // Extract sqft - require 3-6 digits
    const sqftMatch = text.match(/\b([\d,]{3,6})\s*(?:sq\.?\s*ft\.?|sqft|square\s*feet?)\b/i);
    const sqft = sqftMatch ? parseInt(sqftMatch[1].replace(/,/g, '')) : null;

    return {
      address: addrMatch?.[1]?.trim() || '',
      city: addrMatch?.[2]?.trim() || '',
      state: addrMatch?.[3] || '',
      zip_code: addrMatch?.[4] || '',
      list_price: price,
      bedrooms: beds,
      bathrooms: baths,
      sqft,
      property_type: 'single_family_home',
    };
  });
}

module.exports = { scrapeProperty, detectSource };
