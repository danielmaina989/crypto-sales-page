const btc = document.getElementById("bitcoin");
const doge = document.getElementById("dogecoin");
const eth = document.getElementById("ethereum");

const CACHE_KEY = 'cryptoPrices';
const CACHE_TTL_MS = 45 * 1000; // 45 seconds cache TTL

// Helper: load cached object { time, prices: {bitcoin: num,...}, fx: rate }
function loadCached(){
  try{
    const raw = localStorage.getItem(CACHE_KEY);
    if(!raw) return null;
    const parsed = JSON.parse(raw);
    if(parsed && parsed.data) return parsed.data;
  }catch(e){ console.warn('Failed to read crypto cache', e); }
  return null;
}
function saveCache(data){
  try{
    localStorage.setItem(CACHE_KEY, JSON.stringify({ time: Date.now(), data }));
  }catch(e){ console.warn('Failed to save crypto cache', e); }
}

// Fetch forex rate USD -> KES using exchangerate.host (no API key)
async function fetchForexRate(){
  try{
    const res = await fetch('https://api.exchangerate.host/latest?base=USD&symbols=KES', { cache: 'no-store' });
    if(!res.ok) throw new Error('FX fetch failed: ' + res.status);
    const j = await res.json();
    return j && j.rates && j.rates.KES ? Number(j.rates.KES) : null;
  }catch(err){
    console.warn('Forex fetch error:', err);
    return null;
  }
}

// Fetch crypto prices from Coinbase public API (no key required)
async function fetchCryptoPrices(){
  const coins = [ { id: 'bitcoin', symbol: 'BTC' }, { id: 'ethereum', symbol: 'ETH' }, { id: 'dogecoin', symbol: 'DOGE' } ];
  try{
    const promises = coins.map(c => fetch(`https://api.coinbase.com/v2/prices/${c.symbol}-USD/spot`, { cache: 'no-store' }).then(r => {
      if(!r.ok) throw new Error('Coinbase fetch failed: ' + r.status);
      return r.json();
    }).then(j => ({ id: c.id, price: Number(j.data.amount) })) );

    const results = await Promise.all(promises);
    const prices = {};
    results.forEach(r => prices[r.id] = r.price);
    return prices;
  }catch(err){
    console.warn('Crypto price fetch error:', err);
    return null;
  }
}

// Apply prices to DOM (shows USD values)
function applyPricesToDom(prices){
  if(!prices) return;
  if(btc && prices.bitcoin != null) btc.textContent = prices.bitcoin.toLocaleString(undefined, {maximumFractionDigits: 2});
  if(doge && prices.dogecoin != null) doge.textContent = prices.dogecoin.toLocaleString(undefined, {maximumFractionDigits: 6});
  if(eth && prices.ethereum != null) eth.textContent = prices.ethereum.toLocaleString(undefined, {maximumFractionDigits: 2});
}

// Convert USD -> KES using cached FX or fresh fetch
async function convertUsdToKes(usdAmount){
  try{
    const cached = loadCached();
    let rate = cached && cached.fx ? Number(cached.fx) : null;
    // if no cached fx or stale, fetch a fresh rate
    if(!rate){
      const fetched = await fetchForexRate();
      if(fetched) rate = fetched;
    }
    if(!rate) return null;
    return Number(usdAmount) * Number(rate);
  }catch(e){
    console.warn('Conversion failed', e);
    return null;
  }
}

// Main updater: gets crypto prices and FX, applies to DOM and caches result
async function updatePricesAndFx(){
  // Try to reuse cache if recent
  const rawCache = loadCached();
  if(rawCache && rawCache._ts && (Date.now() - rawCache._ts) < CACHE_TTL_MS){
    applyPricesToDom(rawCache.prices);
    return rawCache; // still return cached
  }

  const [prices, fx] = await Promise.all([fetchCryptoPrices(), fetchForexRate()]);

  if(prices){
    applyPricesToDom(prices);
  } else {
    // fallback to previous cached prices if available
    if(rawCache && rawCache.prices) applyPricesToDom(rawCache.prices);
  }

  const dataToCache = { prices: prices || (rawCache && rawCache.prices) || null, fx: fx || (rawCache && rawCache.fx) || null, _ts: Date.now() };
  saveCache(dataToCache);
  return dataToCache;
}

// initial load and periodic refresh
(async function initPriceLoop(){
  await updatePricesAndFx();
  setInterval(updatePricesAndFx, 45000);
})();

// Expose helper for other scripts (e.g., modal) to convert USD->KES and access cached prices
window.cryptoPriceHelpers = {
  convertUsdToKes: convertUsdToKes,
  getCached: () => loadCached()
};
