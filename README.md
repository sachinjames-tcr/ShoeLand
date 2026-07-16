# Shoeland — Premium Shoe Store E-Commerce Website

A full-stack e-commerce web application built with **Django 5.1** (the current stable
release — Django 6.x has not been released yet at time of writing, so this project
targets the latest stable 5.x line, which is a drop-in match for everything requested),
Bootstrap 5, and vanilla JavaScript.

Modern, premium sneaker-store identity in black / white / orange, with AJAX cart &
wishlist, a hybrid session+database cart engine, coupon codes, PDF invoices, product
reviews, live search, and a full account/checkout flow.

---

## 1. Quick Start

```bash
# 1. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Load demo data (categories, brands, 48 products, reviews, users, orders, coupons)
python manage.py loaddata fixtures/sample_data.json

# 5. (Optional) Create your own superuser — a demo admin is already included, see below
python manage.py createsuperuser

# 6. Run the dev server
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** for the storefront and **http://127.0.0.1:8000/admin/**
for the admin dashboard.

> **Note on product images:** `loaddata` restores database rows, and the matching
> placeholder JPGs it references are already included under `media/`, so images will
> show up immediately — no extra step needed.

---

## 2. Sample Credentials

| Role          | Username     | Password        |
|---------------|--------------|-----------------|
| Admin         | `admin`      | `AdminShoe@123` |
| Demo customer | `customer1` … `customer20` | `Shoeland@123` |

Two demo coupons are pre-loaded: **`WELCOME10`** (10% off, min. order ₹999) and
**`FLAT200`** (₹200 off, min. order ₹1999).

---

## 3. Project Structure

```
shoeland/
├── shoeland_project/       # Project settings, root urls, sitemaps
├── core/                   # Home, About, Contact, Privacy/Terms, banners, newsletter
├── accounts/                # Register/Login/Logout, profile, addresses, password reset
├── products/                # Category, Brand, Product, Review, Coupon + shop/search/filter views
├── cart/                    # Hybrid session (guest) + DB (logged-in) cart engine
├── wishlist/                 # Wishlist model + views
├── orders/                   # Checkout, orders, PDF invoice generation
├── templates/                # Base layout + shared partials (product card, filters, pagination)
├── static/                   # CSS (style.css), JS (main.js)
├── media/                    # Uploaded/generated images (products, banners, profiles)
├── fixtures/sample_data.json # Demo dataset (loaddata-ready)
├── generate_sample_data.py   # Script used to (re)generate the demo dataset from scratch
├── requirements.txt
└── manage.py
```

Each app follows Django best practices: `models.py`, `views.py`, `urls.py`, `admin.py`,
and its own `templates/<app_name>/` namespace.

---

## 4. Feature Overview

**Storefront (22 pages):** Home, Shop, Categories, Brands, Product Details, Search
Results, Wishlist, Cart, Checkout, Order Success, Login, Register, Forgot Password,
Dashboard, My Orders, My Profile, Change Password, My Addresses, Contact, About,
Privacy Policy, Terms & Conditions, and a custom 404.

**Cart engine (`cart/cart.py`):** guests get a session-based cart; the moment they
register or log in, it's automatically merged into a database-backed `Cart` /
`CartItem` pair so it persists across devices. Supports add / remove / update quantity /
save for later / move back to cart, all with AJAX where relevant.

**Checkout:** address form (pre-filled from saved addresses), coupon codes, Cash on
Delivery, and **placeholder** Razorpay/Stripe payment options (no real transactions are
processed — these are wired up as UI/flow placeholders only, ready for real SDK
integration). Places an `Order` + `OrderItem`s, decrements stock, and generates a
downloadable PDF invoice (via `reportlab`).

**Search & filters:** live AJAX search dropdown in the navbar, plus full search results
page with category/brand/price/rating/availability filters and 5 sort modes.

**Reviews:** authenticated users can add/edit/delete a review per product; the
product's average rating recalculates automatically.

**Admin dashboard:** manage categories, brands, products (with inline image gallery),
customers, orders (with status/payment-status inline editing), coupons, reviews, and
contact messages — all via Django's built-in admin, fully registered in each app's
`admin.py`.

**SEO:** slugged URLs throughout, meta description + Open Graph tags, `sitemap.xml`
(via `django.contrib.sitemaps`), and `robots.txt`.

---

## 5. Configuration Notes

- **Database:** SQLite by default (`db.sqlite3`). A commented-out PostgreSQL config
  block is included in `shoeland_project/settings.py` — swap it in and set the usual
  `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` environment variables.
- **Payments:** `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `STRIPE_PUBLIC_KEY`, and
  `STRIPE_SECRET_KEY` in settings are placeholders. Replace with real test/live keys
  and wire up the respective SDK in `orders/views.py::checkout` before going live.
- **Email:** uses Django's console backend in development (password reset emails print
  to the terminal). Swap `EMAIL_BACKEND` for SMTP in production.
- **Secrets:** `SECRET_KEY` and `DEBUG` are read from environment variables with safe
  local-dev fallbacks — set `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=False` in production.

---

## 6. Regenerating Demo Data

If you want a fresh randomized dataset instead of the bundled fixture:

```bash
python manage.py flush          # wipes the DB (keeps schema)
python manage.py migrate
python generate_sample_data.py  # regenerates categories/brands/products/users/orders
```

This script also generates the placeholder product/banner/brand images programmatically
with Pillow, so it works completely offline.

---

## 7. What's a Placeholder vs. Production-Ready

To be transparent about scope: this is a portfolio-grade, fully runnable build. A few
things are intentionally left as clearly-marked placeholders rather than wired to real
third-party services, since that requires live credentials:

- Razorpay / Stripe checkout — UI and order flow are complete; real payment capture
  needs your API keys and a webhook handler.
- Product/banner images — generated placeholder graphics (Pillow), swap in real photos
  under `media/products/` and `media/banners/`.
- Email sending — console backend for dev; point `EMAIL_BACKEND` at SMTP for real email.

Everything else (models, auth, cart, wishlist, checkout math, coupons, reviews, admin,
search/filter/sort, invoice PDFs) is fully functional against the local database.
