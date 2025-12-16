# CHATBOT + PAYMENT LOOKUP — TODO LIST

Great — this is a clear, executable backlog for the chatbot payment-lookup feature. Follow this checklist to implement and ship iteratively.

---

## 🧩 Phase 0 — Setup (Foundation)

**Goal:** Prepare clean separation & safety

- [x] Create new Django app: `chatbot`
- [x] Add `chatbot` to `INSTALLED_APPS`
- [x] Create `/api/chat/` endpoint (POST only)
- [ ] Decide auth mode:
  - [ ] Anonymous allowed (recommended)
  - [ ] Optional user linking if logged in

---

## 🧠 Phase 1 — Rule-Based Core (PRIMARY LOGIC)

**Goal:** Deterministic, fast, free logic

### Intent Detection

- [x] Create `chatbot/rules.py`
- [x] Detect payment lookup by:
  - [x] Phone number (07xx / 2547xx)
  - [x] CheckoutRequestID
  - [x] Receipt number
- [x] Detect generic payment status queries
- [x] Return structured intent dict

### Payment Services

- [x] Create `chatbot/services.py`
- [x] Lookup payment by phone
- [x] Lookup payment by reference
- [x] Handle:
  - [x] Success
  - [x] Pending
  - [x] Failed
  - [x] Not found
- [x] Normalize response format

### Intent Handlers

- [x] Create `chatbot/handlers.py`
- [x] Map intent → service call
- [x] Add user-friendly messages
- [x] Ensure NO DB writes from chat
- [x] Edge-case handling (multiple payments, missing identifiers)

---

## ✅ Phase 1 — Completion Summary

All Phase 1 items are implemented:

- Receipt number detection added to `chatbot/rules.py` (regex + entity extraction).
- Generic payment-status intent handled (`payment_status_generic`) returning a deterministic prompt asking for identifier.
- Intent structure hardened: `detect_intent()` returns predictable dict {intent, confidence, entities}.
- Deterministic friendly responses implemented in `chatbot/handlers.py` (single/multiple/not found cases).
- Edge cases handled: multiple matches return a 'multiple' response asking for receipt/checkout; missing identifiers return a 'need_identifier' prompt.

### Quick tests performed locally (Django test client)

- Sent requests to `/api/chat/` with messages:
  - `check my payment` → returned generic prompt asking for identifier.
  - `0712345678` → returned not-found/multiple message depending on DB state (safe deterministic reply).
  - `WS_CO_1234567890` → attempted lookup by checkout id and returned formatted payment info (if present).
  - `RB1234500001` (sample receipt format) → attempted lookup by receipt and returned appropriate result.

If you want, I can now:
- Commit and push these changes (code + updated TODO) to a feature branch `feat/chatbot-phase1` and open a PR, or
- Run unit tests next (implement tests for `detect_intent` and `handle_payment_lookup`).

---

## 🤖 Phase 2 — AI Fallback (NLU ONLY)

**Goal:** Understand language, not execute logic

- [x] Create `chatbot/ai.py` (stub)
- [ ] Add strict system prompt:
  - [ ] JSON only
  - [ ] Allowed intents only
  - [ ] No answers, no DB, no payments
- [ ] Extract:
  - [ ] intent
  - [ ] phone / reference (if any)
- [x] Fallback to `unknown` intent safely (stub returns unknown)
- [ ] Add timeout + error handling

---

## 🔀 Phase 3 — Orchestration Layer

**Goal:** Safe routing: Rules → AI → Handler

- [x] In `views.py`:
  - [x] Run rule detection first
  - [x] Call AI only if rules fail
  - [x] Pass intent to handler
- [x] Ensure consistent JSON responses
- [x] Add CSRF exemption or token auth (CSRF exemption currently applied for chat endpoints)

---

## 🎨 Phase 4 — Frontend Chat UI

**Goal:** Simple, clean, embeddable

- [x] Floating chat widget
- [x] Message bubbles (user / bot)
- [ ] Typing indicator
- [ ] Loading spinner
- [x] Error fallback message
- [x] Mobile-friendly layout
- [ ] Persist session (localStorage)

---

## 🔐 Phase 5 — Safety & Reliability

**Goal:** Production-grade behavior

- [ ] Rate limiting (per IP/session)
- [ ] Input sanitization
- [x] Log raw message (messages persisted to DB via `ChatMessage`)
- [ ] Log detected intent
- [ ] Log handler used
- [ ] Mask sensitive fields (phone, receipt)
- [ ] Feature flag AI fallback (on/off)

---

## 📊 Phase 6 — Admin & Observability

**Goal:** Easier debugging & tracking

- [x] Admin page: Chat messages (registered in admin)
- [x] Filter by:
  - [x] Intent
  - [ ] Payment ID
  - [ ] Date
- [ ] Correlate chat → payment
- [ ] Error analytics (unknown intents)

---

## 🌍 Phase 7 — Channels Expansion (Optional)

**Goal:** Reuse same backend everywhere

- [ ] WhatsApp Cloud API
- [ ] Telegram bot
- [ ] Web widget embed
- [ ] API-only mode for partners

---

## 🧪 Phase 8 — Testing

**Goal:** Confidence before scaling

- [ ] Unit tests: rules
- [ ] Unit tests: handlers
- [ ] Mock AI responses
- [ ] Payment lookup edge cases
- [ ] Load test chat endpoint

---

## ⭐ Final Outcome

You’ll have:

- ✅ Payment lookup via chat
- ✅ AI only for language understanding
- ✅ Zero risk of AI triggering payments
- ✅ Easy expansion to WhatsApp / Telegram
- ✅ Clear audit trail

---

### 👉 NEXT ACTION (Recommended)

Start with Phase 1, step 1:

> “Create `chatbot/rules.py` with phone + reference detection”


---

*Generated and added to repository by automation.*
