/* Trading Forms - Buy & Sell Page JavaScript */

// Initialize Buy Page
function initBuyPage() {
    const form = document.getElementById('buyForm');
    const coinSelect = document.getElementById('coin');
    const networkSection = document.getElementById('networkSection');
    const networkSelect = document.getElementById('network');
    const amountInput = document.getElementById('amountKes');
    const walletInput = document.getElementById('walletAddress');
    const phoneInput = document.getElementById('phoneNumber');
    const agreeCheckbox = document.getElementById('agreeTerms');
    const ratePanelDiv = document.querySelector('[data-rates-panel]');
    
    if (!form) return; // bail if not on buy page

    // network options per coin
    const coinNetworks = {
        BTC: ['BTC'],
        ETH: ['ERC20'],
        USDT: ['ERC20', 'TRC20', 'BEP20', 'SOLANA'],
        USDC: ['ERC20', 'BEP20']
    };

    // mapping regex validators
    const regexByNetwork = {
        ERC20: /^0x[a-fA-F0-9]{40}$/,
        BEP20: /^0x[a-fA-F0-9]{40}$/,
        TRC20: /^T[a-zA-Z0-9]{33}$/,
        SOLANA: /^[1-9A-HJ-NP-Za-km-z]{32,44}$/,
        BTC: /^[13bc][a-zA-Z0-9]{25,39}$/
    };

    // Real-time calculator
    function updateCalculator() {
        const coin = coinSelect.value;
        const amount = parseFloat(amountInput.value) || 0;
        
        if (!coin || amount <= 0) {
            hideCalculator();
            return;
        }

        const rateItem = document.querySelector(`.rate-item[data-coin="${coin}"]`);
        if (!rateItem) return;

        const rateText = rateItem.querySelector('.rate-row:last-child .rate-value')?.textContent || '';
        const rate = parseFloat(rateText.replace(/[^0-9.]/g, ''));
        
        if (!rate) return;

        const spread = 0.03; // 3% spread
        const cryptoAmount = amount / (rate * (1 + spread));
        const totalRate = rate * (1 + spread);

        updateCalculatorDisplay(coin, amount, cryptoAmount, rate, totalRate);
    }

    function updateCalculatorDisplay(coin, kesAmount, cryptoAmount, rate, totalRate) {
        let calcDiv = document.querySelector('.amount-calculator');
        
        if (!calcDiv) {
            calcDiv = document.createElement('div');
            calcDiv.className = 'amount-calculator';
            amountInput.parentElement.appendChild(calcDiv);
        }

        calcDiv.innerHTML = `
            <div class="calc-row">
                <span class="calc-label">Rate (with spread)</span>
                <span><span class="calc-value">${totalRate.toFixed(2)}</span> <span class="calc-unit">KES</span></span>
            </div>
            <div class="calc-divider"></div>
            <div class="calc-row info">
                <span class="calc-label">You will receive</span>
                <span><span class="calc-value">${cryptoAmount.toFixed(8)}</span> <span class="calc-unit">${coin}</span></span>
            </div>
        `;
        calcDiv.style.display = 'block';
    }

    function hideCalculator() {
        const calcDiv = document.querySelector('.amount-calculator');
        if (calcDiv) calcDiv.style.display = 'none';
    }

    // Phone number normalization
    function normalizePhoneNumber(phone) {
        phone = phone.replace(/\D/g, ''); // Remove non-digits
        if (phone.startsWith('0')) {
            phone = '254' + phone.substring(1);
        } else if (!phone.startsWith('254')) {
            phone = '254' + phone;
        }
        return phone;
    }

    // Wallet validation
    function validateWallet(wallet, coin, network) {
        wallet = wallet.trim();
        
        if (coin === 'BTC') {
            const btcRegex = /^[13bc][a-zA-Z0-9]{25,39}$/;
            return btcRegex.test(wallet);
        }
        if (network && regexByNetwork[network]) {
            return regexByNetwork[network].test(wallet);
        }
        // fallback: if no network selected, try basic ETH pattern for coins using it
        if (['ETH','USDT','USDC'].includes(coin)) {
            return regexByNetwork['ERC20'].test(wallet);
        }
        return false;
    }

    // Form validation
    function validateForm() {
        const errors = {};
        
        if (!coinSelect.value) {
            errors.coin = 'Please select a cryptocurrency';
        }
        
        const amount = parseFloat(amountInput.value);
        if (!amount || amount < 100) {
            errors.amount = 'Minimum amount is KES 100';
        }
        
            const wallet = walletInput.value.trim();
        if (!wallet) {
            errors.wallet = 'Wallet address is required';
        } else {
            const network = networkSelect ? networkSelect.value : '';
            if (!validateWallet(wallet, coinSelect.value, network)) {
                errors.wallet = `Invalid wallet address for ${coinSelect.value}${network? ' ('+network+')':''}`;
            }
        }
        
        const phone = phoneInput.value.trim();
        if (!phone) {
            errors.phone = 'Phone number is required';
        } else if (!/^254\d{9}$/.test(normalizePhoneNumber(phone))) {
            errors.phone = 'Invalid phone number';
        }
        
        if (!agreeCheckbox.checked) {
            errors.agree = 'Please accept the terms and conditions';
        }
        
        return { valid: Object.keys(errors).length === 0, errors };
    }

    // Display form errors
    function displayErrors(errors) {
        // Clear previous errors
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('show'));
        
        // Show new errors
        Object.entries(errors).forEach(([field, message]) => {
            const errorEl = document.getElementById(`${field}Error`);
            if (errorEl) {
                errorEl.textContent = message;
                errorEl.classList.add('show');
            }
        });
    }

    // Update wallet examples and help text based on coin selection
    function updateWalletExamples() {
        const coin = coinSelect.value;
        const coinNameSpan = document.getElementById('coinName');
        const walletHelp = document.getElementById('walletHelp');
        const networkExample = document.getElementById('networkExample');
        
        if (coinNameSpan) coinNameSpan.textContent = coin || 'BTC';
        
        const network = networkSelect ? networkSelect.value : '';
        if (walletHelp) {
            let helpText = 'Make sure this address supports the selected network. Crypto sent to the wrong network cannot be recovered.';
            if (network) {
                helpText = `Network: ${network} — ${helpText}`;
            }
            walletHelp.textContent = helpText;
        }
        
        if (networkExample) {
            if (coin === 'BTC') {
                networkExample.textContent = 'BTC address: 3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy';
            } else if (network === 'ERC20') {
                networkExample.textContent = 'Ethereum address (ERC-20): 0x742d35Cc6634C0532925a3b844Bc9e7595f42bE';
            } else if (network === 'TRC20') {
                networkExample.textContent = 'TRON address (TRC-20): TQ59aS9PdVnwr1hGvzXh7K8WxsQnG2XY8M';
            } else if (network === 'BEP20') {
                networkExample.textContent = 'BEP20 address (same format as ERC20, BSC): 0x742d35Cc6634C0532925a3b844Bc9e7595f42bE';
            } else if (network === 'SOLANA') {
                networkExample.textContent = 'Solana address (44 chars) e.g. 4v4QT83PZ85AkcD9R27fjQ4QrQ2v6ZbfzP27T4ssf9s';
            } else {
                networkExample.textContent = '';
            }
        }
    }

    // Event listeners
    coinSelect.addEventListener('change', () => {
        // show network dropdown if needed
        const coin = coinSelect.value;
        if (coinNetworks[coin] && coinNetworks[coin].length > 1) {
            networkSection.style.display = 'block';
            networkSelect.innerHTML = coinNetworks[coin].map(n=>`<option value="${n}">${n}</option>`).join('');
            networkSelect.required = true;
        } else {
            networkSection.style.display = 'none';
            if (networkSelect) {
                networkSelect.innerHTML = '';
                networkSelect.required = false;
            }
        }
        updateCalculator();
        updateWalletExamples();
    });
    if (networkSelect) {
        networkSelect.addEventListener('change', updateWalletExamples);
    }
    amountInput.addEventListener('input', updateCalculator);
    
    // Initialize wallet/examples on load
    updateWalletExamples();
    // set initial network options based on default coin
    coinSelect.dispatchEvent(new Event('change'));

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const validation = validateForm();
        if (!validation.valid) {
            displayErrors(validation.errors);
            return;
        }

        const formBtn = form.querySelector('button[type="submit"]');
        const originalText = formBtn.textContent;
        formBtn.disabled = true;
        formBtn.textContent = 'Processing...';

        try {
            const response = await fetch('/api/buy/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    coin: coinSelect.value,
                    amount_kes: parseFloat(amountInput.value),
                    wallet_address: walletInput.value.trim(),
                    phone_number: normalizePhoneNumber(phoneInput.value)
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                showErrorModal(errorData.detail || 'An error occurred');
                return;
            }

            const data = await response.json();
            showSuccessModal(data);
            form.reset();
            hideCalculator();
        } catch (error) {
            showErrorModal(error.message || 'Network error. Please try again.');
        } finally {
            formBtn.disabled = false;
            formBtn.textContent = originalText;
        }
    });

    updateCalculator();
}

// Initialize Sell Page
function initSellPage() {
    const form = document.getElementById('sellForm');
    const coinSelect = document.getElementById('coin');
    const amountInput = document.getElementById('cryptoAmount');
    const phoneInput = document.getElementById('phoneNumber');
    const agreeCheckbox = document.getElementById('agreeTerms');
    
    if (!form) return;

    // Real-time calculator
    function updateCalculator() {
        const coin = coinSelect.value;
        const amount = parseFloat(amountInput.value) || 0;
        
        if (!coin || amount <= 0) {
            hideCalculator();
            return;
        }

        const rateItem = document.querySelector(`.rate-item[data-coin="${coin}"]`);
        if (!rateItem) return;

        const rateText = rateItem.querySelector('.rate-row:last-child .rate-value')?.textContent || '';
        const rate = parseFloat(rateText.replace(/[^0-9.]/g, ''));
        
        if (!rate) return;

        const spread = 0.03; // 3% spread
        const kesAmount = amount * rate * (1 - spread);

        updateCalculatorDisplay(coin, amount, kesAmount, rate);
    }

    function updateCalculatorDisplay(coin, cryptoAmount, kesAmount, rate) {
        let calcDiv = document.querySelector('.amount-calculator');
        
        if (!calcDiv) {
            calcDiv = document.createElement('div');
            calcDiv.className = 'amount-calculator';
            amountInput.parentElement.appendChild(calcDiv);
        }

        calcDiv.innerHTML = `
            <div class="calc-row">
                <span class="calc-label">Rate (with spread)</span>
                <span><span class="calc-value">${(rate * 0.97).toFixed(2)}</span> <span class="calc-unit">KES</span></span>
            </div>
            <div class="calc-divider"></div>
            <div class="calc-row info">
                <span class="calc-label">You will receive</span>
                <span><span class="calc-value">${kesAmount.toFixed(2)}</span> <span class="calc-unit">KES</span></span>
            </div>
        `;
        calcDiv.style.display = 'block';
    }

    function hideCalculator() {
        const calcDiv = document.querySelector('.amount-calculator');
        if (calcDiv) calcDiv.style.display = 'none';
    }

    // Phone number normalization
    function normalizePhoneNumber(phone) {
        phone = phone.replace(/\D/g, '');
        if (phone.startsWith('0')) {
            phone = '254' + phone.substring(1);
        } else if (!phone.startsWith('254')) {
            phone = '254' + phone;
        }
        return phone;
    }

    // Form validation
    function validateForm() {
        const errors = {};
        
        if (!coinSelect.value) {
            errors.coin = 'Please select a cryptocurrency';
        }
        
        const amount = parseFloat(amountInput.value);
        if (!amount || amount <= 0) {
            errors.amount = 'Amount must be greater than 0';
        } else if (amount < 0.001) {
            errors.amount = 'Minimum amount is 0.001 ' + coinSelect.value;
        }
        
        const phone = phoneInput.value.trim();
        if (!phone) {
            errors.phone = 'Phone number is required';
        } else if (!/^254\d{9}$/.test(normalizePhoneNumber(phone))) {
            errors.phone = 'Invalid phone number';
        }
        
        if (!agreeCheckbox.checked) {
            errors.agree = 'Please accept the deposit instructions';
        }
        
        return { valid: Object.keys(errors).length === 0, errors };
    }

    // Display form errors
    function displayErrors(errors) {
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('show'));
        
        Object.entries(errors).forEach(([field, message]) => {
            const errorEl = document.getElementById(`${field}Error`);
            if (errorEl) {
                errorEl.textContent = message;
                errorEl.classList.add('show');
            }
        });
    }

    // Event listeners
    coinSelect.addEventListener('change', updateCalculator);
    amountInput.addEventListener('input', updateCalculator);

    // Copy to clipboard
    document.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const addressBox = btn.parentElement;
            const address = addressBox.querySelector('code').textContent;
            try {
                await navigator.clipboard.writeText(address);
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            } catch (err) {
                alert('Failed to copy');
            }
        });
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const validation = validateForm();
        if (!validation.valid) {
            displayErrors(validation.errors);
            return;
        }

        const formBtn = form.querySelector('button[type="submit"]');
        const originalText = formBtn.textContent;
        formBtn.disabled = true;
        formBtn.textContent = 'Processing...';

        try {
            const response = await fetch('/api/sell/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    coin: coinSelect.value,
                    amount_crypto: parseFloat(amountInput.value),
                    phone_number: normalizePhoneNumber(phoneInput.value)
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                showErrorModal(errorData.detail || 'An error occurred');
                return;
            }

            const data = await response.json();
            showSellSuccessModal(data);
            form.reset();
            hideCalculator();
        } catch (error) {
            showErrorModal(error.message || 'Network error. Please try again.');
        } finally {
            formBtn.disabled = false;
            formBtn.textContent = originalText;
        }
    });

    updateCalculator();
}

// Modal Functions
function showSuccessModal(trade) {
    const modal = document.getElementById('successModal');
    if (!modal) return;

    const tradeSummary = document.querySelector('.trade-summary');
    if (tradeSummary) {
        tradeSummary.innerHTML = `
            <div class="summary-row">
                <span class="summary-label">Order ID</span>
                <span class="summary-value">#${trade.id}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Coin</span>
                <span class="summary-value">${trade.coin}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Amount (KES)</span>
                <span class="summary-value">KES ${trade.amount_kes != null ? Number(trade.amount_kes).toLocaleString() : '0'}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Crypto to Receive</span>
                <span class="summary-value">${trade.amount_crypto} ${trade.coin}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Status</span>
                <span class="summary-value">${trade.status}</span>
            </div>
        `;
    }

    modal.style.display = 'flex';
}

function showSellSuccessModal(deposit) {
    const modal = document.getElementById('successModal');
    if (!modal) return;

    const tradeInfo = document.querySelector('.trade-summary');
    if (tradeInfo) {
        tradeInfo.innerHTML = `
            <div class="summary-row">
                <span class="summary-label">Deposit ID</span>
                <span class="summary-value">#${deposit.id}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Coin to Deposit</span>
                <span class="summary-value">${deposit.coin}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Status</span>
                <span class="summary-value">${deposit.status}</span>
            </div>
        `;
    }

    const addressBox = document.querySelector('.address-box');
    if (addressBox && deposit.deposit_address) {
        addressBox.innerHTML = `
            <code>${deposit.deposit_address}</code>
            <button type="button" class="btn-copy">Copy Address</button>
        `;
        
        addressBox.querySelector('.btn-copy').addEventListener('click', async (e) => {
            try {
                await navigator.clipboard.writeText(deposit.deposit_address);
                const btn = e.target;
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            } catch (err) {
                alert('Failed to copy');
            }
        });
    }

    modal.style.display = 'flex';
}

function showErrorModal(message) {
    const modal = document.getElementById('errorModal');
    if (!modal) return;

    const errorMsg = modal.querySelector('p');
    if (errorMsg) {
        errorMsg.textContent = message;
    }

    modal.style.display = 'flex';
}

// Show Terms and Conditions Modal
function showTermsModal(event) {
    event?.preventDefault();
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'termsModal';
    modal.innerHTML = `
        <div class="modal-content modal-lg">
            <div class="modal-header">
                <h2>Terms of Service</h2>
                <button class="modal-close" onclick="closeModal('termsModal')">&times;</button>
            </div>
            <div class="modal-body" style="max-height: 60vh; overflow-y: auto; text-align: left;">
                <h3>1. Trading Agreement</h3>
                <p>By using this platform, you acknowledge that you understand the risks of cryptocurrency trading. Cryptocurrency prices are volatile and trading may result in loss of funds.</p>

                <h3>2. User Responsibilities</h3>
                <p>You are responsible for:</p>
                <ul>
                    <li>Keeping your wallet addresses and personal information secure</li>
                    <li>Verifying all transaction details before confirmation</li>
                    <li>Ensuring your MPESA account is active and in good standing</li>
                    <li>Complying with all applicable laws and regulations</li>
                </ul>

                <h3>3. Transaction Limits</h3>
                <p>Daily and monthly transaction limits may apply based on your account status and regulatory requirements.</p>

                <h3>4. No Liability</h3>
                <p>We are not liable for:</p>
                <ul>
                    <li>Cryptocurrency price fluctuations</li>
                    <li>Loss of funds due to incorrect wallet addresses</li>
                    <li>Network delays or blockchain congestion</li>
                    <li>Loss of access to your account</li>
                </ul>

                <h3>5. Fees and Spreads</h3>
                <p>We charge a 3% spread on all transactions. Additional fees may apply for certain transaction types.</p>

                <h3>6. Risk Acknowledgment</h3>
                <p><strong>Cryptocurrency is highly volatile and speculative.</strong> Only invest what you can afford to lose. Trading is not suitable for everyone.</p>

                <h3>7. Modification of Terms</h3>
                <p>We reserve the right to modify these terms at any time. Continued use of the platform constitutes acceptance of modified terms.</p>

                <div style="margin-top: 20px; padding: 15px; background: #f0f4ff; border-radius: 8px; border-left: 4px solid #4f46e5;">
                    <strong>Last Updated:</strong> February 2026<br>
                    By checking the "I agree" checkbox, you confirm that you have read and understood these terms.
                </div>
            </div>
            <div style="padding: 20px; border-top: 1px solid #e5e7eb; text-align: right;">
                <button class="btn btn-primary" onclick="closeModal('termsModal')">Close</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Helper function to close modals by ID
function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'none';
        if (modal.id === 'termsModal') {
            modal.remove();
        }
    }
}

// Modal close handlers
function closeModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', closeModals);
});

document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModals();
        }
    });
});

// CSRF Token Helper
function getCookie(name) {
    let value = '';
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.substring(0, name.length + 1) === name + '=') {
                value = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return value;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initBuyPage();
    initSellPage();
});
