
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ====== CONFIG ======
const USE_PROXY = false; // true if we use proxy residential
const PROXY_URL = 'http://user:pass@host:port'; // change if we use proxy
const COOKIES_FILE = 'maps_cookies.json';
const csv_path = '../mapURLs.csv';
const DB_PATH = '../result/reviews.db';
const DB_TABLE = 'reviews';

// ====================
// Setup dirname (using ES module)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Enable stealth
puppeteer.use(StealthPlugin());

// ========= UTILS =========
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function randomInt(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

// delay like human
async function humanPause(min = 300, max = 1200) {
  await sleep(randomInt(min, max));
}

// random viewport for each page
function randomViewport() {
  return {
    width: randomInt(1200, 1600),
    height: randomInt(700, 900),
  };
}

// ========= COOKIE PERSISTENCE ==============
async function loadCookies(page) {
  try {
    const cookiePath = path.join(__dirname, COOKIES_FILE);
    if (fs.existsSync(cookiePath)) {
      const cookies = JSON.parse(fs.readFileSync(cookiePath, 'utf8'));
      if (Array.isArray(cookies) && cookies.length > 0) {
        await page.setCookie(...cookies);
        console.log('[Cookies] Loaded existing cookies.');
      }
    }
  } catch (err) {
    console.log('[Cookies] Could not load cookies:', err.message);
  }
}

async function saveCookies(page) {
  try {
    const cookies = await page.cookies();
    const cookiePath = path.join(__dirname, COOKIES_FILE);
    fs.writeFileSync(cookiePath, JSON.stringify(cookies, null, 2), 'utf8');
    console.log('[Cookies] Saved cookies.');
  } catch (err) {
    console.log('[Cookies] Could not save cookies:', err.message);
  }
}

// ========= SCRAPE HELPERS =================

async function getOpenHours(page) {
  try {
    const btn = await page.waitForSelector(
      'span[aria-label*="open hours" i], span[aria-label*="Hours" i]',
      { timeout: 3000 }
    );
    await btn.click();
    await humanPause(500, 1000);

    await page.waitForSelector('table.eK4R0e.fontBodyMedium tr.y0skZc', {
      timeout: 3000,
    });

    const rows = await page.$$eval(
      'table.eK4R0e.fontBodyMedium tr.y0skZc',
      trs =>
        trs.map(tr => {
          const dayEle = tr.querySelector('.ylH6lf');
          const day = dayEle ? dayEle.innerText.trim() : '';

          const timeEle = tr.querySelector('.mxowUb');
          const time = timeEle ? timeEle.innerText.trim() : '';

          return `${day}: ${time}`;
        })
    );

    return rows; // array
  } catch (err) {
    console.log('Can not take open hours:', err.message);
    return []; // always return array 
  }
}

// extract latitude and longitude from url
function extractLatLon(url) {
  const m = url.match(/!3d([0-9.\-]+)!4d([0-9.\-]+)/);
  if (m) {
    return {
      lat: parseFloat(m[1]),
      lon: parseFloat(m[2]),
    };
  }
  return null;
}

function getPlaceNameFromUrl(url) {
  try {
    const u = new URL(url);
    const pathName = u.pathname;
    const match = pathName.match(/\/place\/([^/]+)/);
    if (!match) return null;
    let encodedName = match[1];
    encodedName = encodedName.replace(/\+/g, ' ');
    return decodeURIComponent(encodedName);
  } catch {
    return null;
  }
}

async function scrapeImages(mapPage) {
  const browser = mapPage.browser();
  const newPage = await browser.newPage();
  await newPage.setViewport(randomViewport());

  try {
    await newPage.goto(mapPage.url(), {
      waitUntil: 'networkidle2',
      timeout: 20000,
    });

    await humanPause(400, 900);

    // selector fallback cho thumbnail
    const thumb = await newPage.waitForSelector(
      'button.aoRNLd img, div.Wj6x2e img',
      { timeout: 4000 }
    );
    await thumb.click();
    await humanPause(600, 1200);

    const img = await newPage.waitForSelector('div.U39Pmb[role="img"]', {
      timeout: 4000,
    });
    const style = await img.evaluate(el => el.getAttribute('style') || '');
    const m = style.match(/url\("([^"]+)"\)/);
    if (!m) return '';

    const rawUrl = m[1];

    function toFullSize(u) {
      return u.replace(/=[^=]*$/, '=s0');
    }

    return toFullSize(rawUrl);
  } catch (err) {
    console.log('Cannot take zoomed image:', err.message);
    return '';
  } finally {
    await newPage.close();
  }
}

async function getReviews(page, limit = 3) {
  try {
    try {
      let clicked = false;

      // Strategy 1: CSS selector role=tab + aria-label chứa "Reviews"
      try {
        const btnReviews = await page.waitForSelector(
          'button[role="tab"][aria-label*="Reviews" i]',
          { timeout: 2000 }
        );
        await btnReviews.click();
        clicked = true;
      } catch {
        // Strategy 2: evaluate tìm theo aria-label
        clicked = await page.evaluate(() => {
          const buttons = Array.from(
            document.querySelectorAll('button[role="tab"]')
          );
          const btn = buttons.find(b => {
            const label = (b.getAttribute('aria-label') || '').toLowerCase();
            return label.includes('review');
          });
          if (btn) {
            btn.click();
            return true;
          }
          return false;
        });
      }

      if (clicked) {
        await humanPause(800, 1500);
      } else {
        console.log('No reviews button found, skip.');
      }
    } catch {
      console.log('No reviews button found, skip.');
    }

    await page.waitForSelector('div.jftiEf.fontBodyMedium', { timeout: 4000 });

    // Expand "More" in first N reviews
    await page.$$eval(
      'div.jftiEf.fontBodyMedium',
      (cards, maxCount) => {
        cards.slice(0, maxCount).forEach(card => {
          const moreBtn = card.querySelector(
            '[jsaction*="review.expandReview"]'
          );
          if (moreBtn) moreBtn.click();
        });
      },
      limit
    );

    await humanPause(400, 800);

    // check if there are such reviews
    const reviews = await page.$$eval(
      'div.jftiEf.fontBodyMedium',
      (cards, maxCount) => {
        function extract(card) {
          const starSpan = card.querySelector('.kvMYJc[role="img"]');
          const starLabel = starSpan ? starSpan.getAttribute('aria-label') : '';
          const m = starLabel ? starLabel.match(/([\d.]+)/) : null;
          const rating = m ? parseFloat(m[1]) : null;

          const text =
            (card.querySelector('.wiI7pd') &&
              card.querySelector('.wiI7pd').innerText.trim()) ||
            (card.querySelector('.MyEned') &&
              card.querySelector('.MyEned').innerText.trim()) ||
            '';

          const author =
            (card.querySelector('.d4r55.fontTitleMedium') &&
              card
                .querySelector('.d4r55.fontTitleMedium')
                .innerText.trim()) ||
            '';

          const time =
            (card.querySelector('.rsqaWe') &&
              card.querySelector('.rsqaWe').innerText.trim()) ||
            '';
          
          // collect all image urls
          const elements = card.querySelectorAll('.Tya61d');
          const imageUrls = [];

          // 2. Iterate through each found element
          elements.forEach(element => {
              // 3. Safely check for the background image style
              if (element && element.style && element.style.backgroundImage) {
                  
                  // 4. Attempt to match the URL pattern
                  const match = element.style.backgroundImage.match(/url\("([^"]+)"\)/);
                  
                  // 5. If successful, extract and push the URL to the array
                  if (match && match[1]) {
                      imageUrls.push(match[1]);
                  }
              }
          });

          return { author, rating, time, text, imageUrls };
        }

        return cards.slice(0, maxCount).map(extract);
      },
      limit
    );

    return reviews; // trả array object
  } catch (err) {
    console.log('Can not take reviews:', err.message);
    return [];
  }
}

// ========= BROWSER & MAP ACCESS =========

async function accessBrowser() {
  const args = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-blink-features=AutomationControlled',
  ];
  if (USE_PROXY && PROXY_URL) {
    args.push(`--proxy-server=${PROXY_URL}`);
  }

  const browser = await puppeteer.launch({
    headless: false,
    args,
  });

  return browser;
}

async function accessMapURL(browser, mapURL) {
  const page = await browser.newPage();
  await page.setViewport(randomViewport());

  // Random-ish UA gần Chrome thật
  const userAgents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  ];
  await page.setUserAgent(
    userAgents[randomInt(0, userAgents.length - 1)]
  );

  try {
    // load cookies before goto
    await loadCookies(page);

    console.log('Opening Google Maps based on URL: ' + mapURL);
    await page.goto(mapURL, {
      waitUntil: 'networkidle2',
      timeout: 30000,
    });

    await humanPause(1000, 2000);

    return page;
  } catch (err) {
    console.error('ERROR opening Google Maps based on URL: ' + mapURL, err.message);
    await page.close();
    return null;
  }
}

async function searchMap(mapPage, query) {
  try {
    // class fontBodyMedium searchboxinput xiQnY 
    const searchInput = await mapPage.waitForSelector(
      '.fontBodyMedium.searchboxinput.xiQnY',
      {
        timeout: 8000,
      }
    ).catch(() => null);

    if (!searchInput) {
      console.error('No search input found, skip this query.');
      return;
    }

    await searchInput.click({ clickCount: 3 });
    await humanPause(200, 600);
    await searchInput.press('Backspace');

    for (const ch of query) {
      await searchInput.type(ch, { delay: randomInt(80, 160) });
    }

    console.log('Searching:', query);
    await searchInput.press('Enter');

    await humanPause(2000, 4000);
  } catch (err) {
    console.error('ERROR searchMap:', err.message);
  }
}

// ========= MULTI RESULT HANDLING =========

async function IterativeScrape(mapPage, limitMultipleResult) {
  await mapPage.waitForSelector('a.hfpxzc', { timeout: 8000 }).catch(() => {});

  const results = await mapPage.$$('a.hfpxzc');
  const links = [];

  for (const result of results) {
    if (links.length >= limitMultipleResult) break;
    const href = await result.evaluate(el => el.href);
    if (href && href.startsWith('http') && !links.includes(href)) {
      links.push(href);
    }
  }

  const scraped = [];
  for (const link of links) {
    await mapPage.goto(link, {
      waitUntil: 'networkidle2',
      timeout: 30000,
    });
    await humanPause(1200, 2500);
    const result = await Scrape(mapPage);
    scraped.push(result);
  }

  return scraped;
}

async function Scrape(mapPage, mapURL) {

//   if (currentUrl.includes('/maps/search/')) {
//     // search result page
//     return await IterativeScrape(mapPage, limitMultipleResult);
//   }
//// remove iterative scrape since we are scraping based on mapURL



  // rating
  let rating = 'N/A';
  try {
    const ratingElement = await mapPage.waitForSelector('div.fontDisplayLarge', {
      timeout: 6000,
    });
    rating = await ratingElement.evaluate(el => el.textContent.trim());
  } catch {}

  // open hours
  const openHours = await getOpenHours(mapPage);
  // reviews
  const firstReviews = await getReviews(mapPage, 3);

  console.log('\n=================================');
  console.log(`- Page URL: ${mapURL}`);
  console.log(`- Rating: ${rating}`);
  console.log(
    `- Opening hours:\n${
      Array.isArray(openHours) ? openHours.join('\n') : openHours
    }`
  );
  console.log(`- First reviews:\n${JSON.stringify(firstReviews, null, 2)}`);
  console.log('=================================\n');

  return {
    mapURL,
    rating,
    openHours,        // array
    firstReviews,     // array
  };
}

async function queryScrape(browser, mapURL) {
  const page = await accessMapURL(browser, mapURL);
  if (!page) return null;

  try {
    await humanPause(1500, 3000);
    const results = await Scrape(page, mapURL);
    await saveCookies(page);
    return results;
  } catch (err) {
    console.error('ERROR in queryScrape for mapURL:', mapURL, err.message);
    return null;
  } finally {
    await page.close();
  }
}

// ========= DATABASE =========

function insertOne(db, dbname, r) {
  if (!r) return;

  const stmt = db.prepare(`
    INSERT INTO ${dbname} (mapURL, rating, openHours, firstReviews)
    VALUES (?, ?, ?, ?)
  `);

  stmt.run(
    r.mapURL,
    r.rating,
    Array.isArray(r.openHours) ? r.openHours.join('\n') : r.openHours,
    JSON.stringify(r.firstReviews ?? [])
  );
}

async function queryScrapeAll(mapURLs, dbPath = DB_PATH, dbname = DB_TABLE) {
  const browser = await accessBrowser();
  const db = new Database(dbPath);

  try {
    for (let i = 0; i < mapURLs.length; i++) {
      const mapURL = mapURLs[i];
      console.log(`===== SCRAPING: ${i+1}/${mapURLs.length} =====`);
      console.log(`===== SCRAPING: ${mapURL} =====`);

      let result;
      try {
        result = await queryScrape(browser, mapURL);
      } catch (err) {
        console.error(`Error scraping mapURL ${i+1}/${mapURLs.length}:`, mapURL, err.message);
        continue;
      }

      if (Array.isArray(result)) {
        for (const r of result) {
          insertOne(db, dbname, r);
        }
      } else if (result) {
        insertOne(db, dbname, result);
      }

      console.log(`Saved to DB: ${i+1}/${mapURLs.length}`);
      // open csv to delete the rowid, mapURL
      // trick to avoid CAPTCHA
      await humanPause(2000, 5000);
    }

    // deduplicate
    db.prepare(`
      DELETE FROM ${dbname} WHERE id NOT IN (
        SELECT MIN(id) FROM ${dbname} GROUP BY mapURL
      )
    `).run();
  } finally {
    await browser.close();
    db.close();
  }
}

async function readCSV() {
    // don't read the first row
    const rows = fs.readFileSync(csv_path, 'utf8').split('\n').slice(1);
    const validRows = rows.filter(row => row !== null && row !== undefined && row.trim() !== '');

    // delete those have already in the database
    const db = new Database(DB_PATH);
    db.prepare(`
      CREATE TABLE IF NOT EXISTS ${DB_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mapURL TEXT,
        rating REAL,
        openHours TEXT,
        firstReviews TEXT
      )
    `).run();
  
    let existingMapURLs = db.prepare(`SELECT mapURL FROM ${DB_TABLE}`).all();
    existingMapURLs = existingMapURLs.map(row => row['mapURL'].trim());
    const validMapURLs = validRows.filter(row => {
        const [_, mapURL] = row.split(',');
        return !existingMapURLs.includes(mapURL);
    });
    const finalMapURLs = validMapURLs.map(row => {
        const [_, mapURL] = row.split(',');
        return mapURL;
    });
    console.log(finalMapURLs);
    console.log(finalMapURLs.length);
    db.close();
    return finalMapURLs;
}
// ========= MAIN =========

async function main() {
  // const queries = fs.readFileSync(csv_path, 'utf8').split('\n');
  // console.log(queries);
  // console.log(queries.length);

  // const queries = ["Ben Thanh Market"];
  // queryScrapeAll(queries, 3, DB_PATH, DB_TABLE);

  const mapURLs = await readCSV();
  queryScrapeAll(mapURLs, DB_PATH, DB_TABLE);
}

main();