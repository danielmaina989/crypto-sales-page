const btc = document.getElementById("bitcoin");
const doge = document.getElementById("dogecoin");
const eth = document.getElementById("ethereum");

const url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin%2Cethereum%2Cdogecoin&vs_currencies=usd";

fetch(url)
  .then(function(response) { return response.json(); })
  .then(function(data) {
      if (btc && data.bitcoin) btc.textContent = data.bitcoin.usd;
      if (doge && data.dogecoin) doge.textContent = data.dogecoin.usd;
      if (eth && data.ethereum) eth.textContent = data.ethereum.usd;
  })
  .catch(function(err) {
      // graceful fallback: leave placeholders empty or show a dash
      if (btc) btc.textContent = '-';
      if (doge) doge.textContent = '-';
      if (eth) eth.textContent = '-';
      console.warn('Failed to fetch crypto prices', err);
  });

