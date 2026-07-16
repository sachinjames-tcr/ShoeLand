"""
One-off script to populate Shoeland with realistic demo data:
categories, brands, products (with generated placeholder images),
banners, testimonials, a coupon, demo users, and a couple of orders.

Run with: python manage.py shell < generate_sample_data.py
(This file is also dumped to fixtures/sample_data.json via dumpdata
 so it can be reloaded any time with `python manage.py loaddata`.)
"""
import os
import random
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shoeland_project.settings")
django.setup()

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont
import io

from core.models import Banner, Testimonial, InstagramPost
from products.models import Category, Brand, Product, ProductImage, Review, Coupon
from accounts.models import Profile, Address

random.seed(42)

PALETTE = ["#0d0d0d", "#ff6b00", "#161616", "#cc4e00", "#2b2b2b"]

def make_placeholder_image(text, size=(800, 800), bg=None):
    bg = bg or random.choice(PALETTE)
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
    except Exception:
        font = ImageFont.load_default()
    # wrap text
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) > size[0] - 80:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    total_h = len(lines) * 56
    y = (size[1] - total_h) / 2
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((size[0] - w) / 2, y), line, fill="#ff6b00" if bg != "#ff6b00" else "#0d0d0d", font=font)
        y += 56
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return ContentFile(buf.getvalue())


print("Clearing old demo data (products/categories/brands only)...")
Product.objects.all().delete()
Category.objects.all().delete()
Brand.objects.all().delete()
Banner.objects.all().delete()
Testimonial.objects.all().delete()
Coupon.objects.all().delete()

# ---------------- Categories ----------------
CATEGORY_NAMES = [
    "Sneakers", "Running Shoes", "Sports Shoes", "Casual Shoes", "Boots",
    "Sandals", "Slippers", "Formal Shoes", "Women's Shoes", "Men's Shoes", "Kids Shoes",
]
categories = []
for name in CATEGORY_NAMES:
    cat = Category.objects.create(name=name, description=f"Shop the best {name.lower()} at Shoeland.")
    cat.image.save(f"{cat.slug}.jpg", make_placeholder_image(name), save=True)
    categories.append(cat)
print(f"Created {len(categories)} categories")

# ---------------- Brands ----------------
BRAND_NAMES = ["Nike", "Adidas", "Puma", "Reebok", "Skechers", "Converse", "New Balance", "ASICS", "Woodland", "Bata"]
brands = []
for name in BRAND_NAMES:
    brand = Brand.objects.create(name=name, description=f"{name} — quality footwear trusted worldwide.")
    brand.logo.save(f"{brand.slug}.jpg", make_placeholder_image(name, size=(400, 200)), save=True)
    brands.append(brand)
print(f"Created {len(brands)} brands")

# ---------------- Products ----------------
ADJECTIVES = ["Air", "Pro", "Ultra", "Ignite", "Ridge", "Storm", "Flex", "Trail", "Ace", "Ghost", "Blaze", "Prime", "Swift", "Nova", "Peak"]
NOUNS = ["Runner", "Strike", "Glide", "Boost", "Court", "Trekker", "Racer", "Sprint", "Cruiser", "Voyager"]

PRODUCT_COUNT = 48
products = []
for i in range(PRODUCT_COUNT):
    category = random.choice(categories)
    brand = random.choice(brands)
    name = f"{brand.name} {random.choice(ADJECTIVES)} {random.choice(NOUNS)} {i+1}"
    price = Decimal(random.choice([1499, 1999, 2499, 2999, 3499, 3999, 4999, 5999, 6999]))
    has_discount = random.random() < 0.4
    discount_price = (price * Decimal("0.8")).quantize(Decimal("1")) if has_discount else None

    product = Product.objects.create(
        name=name,
        sku=f"SHO-{1000+i}",
        category=category,
        brand=brand,
        price=price,
        discount_price=discount_price,
        description=(
            f"The {name} combines premium materials with all-day comfort. "
            f"Engineered for {category.name.lower()} enthusiasts who refuse to compromise on style or performance."
        ),
        features="Breathable mesh upper\nCushioned midsole for all-day comfort\nDurable rubber outsole\nLightweight design\nReinforced heel support",
        specifications=f"Material: Mesh & Synthetic\nSole: Rubber\nClosure: Lace-up\nWeight: {random.randint(220,340)}g\nCare: Wipe with a damp cloth",
        stock=random.choice([0, 5, 12, 20, 35, 50]),
        status="active",
        is_featured=random.random() < 0.25,
        is_best_seller=random.random() < 0.2,
        is_new_arrival=random.random() < 0.25,
        is_trending=random.random() < 0.2,
        sold_count=random.randint(0, 300),
    )
    for img_i in range(3):
        pi = ProductImage(product=product, is_primary=(img_i == 0), order=img_i)
        pi.image.save(f"{product.slug}-{img_i}.jpg", make_placeholder_image(name), save=True)
    products.append(product)

print(f"Created {len(products)} products")

# ---------------- Users ----------------
demo_users = []
for i in range(20):
    username = f"customer{i+1}"
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username, email=f"{username}@example.com", password="Shoeland@123",
            first_name=random.choice(["Arjun", "Priya", "Rahul", "Sneha", "Anand", "Divya", "Kiran", "Meera", "Vishnu", "Athira"]),
            last_name=random.choice(["Nair", "Menon", "Pillai", "Kumar", "Varma", "Das"]),
        )
        Profile.objects.get_or_create(user=user, defaults={"phone": f"98765{10000+i}"})
        demo_users.append(user)
print(f"Created {len(demo_users)} demo users")

# ---------------- Reviews ----------------
review_comments = [
    "Extremely comfortable, wore them all day with no soreness.",
    "Great quality for the price. Would buy again.",
    "Runs slightly small, order half a size up.",
    "Stylish and durable — my daily go-to now.",
    "Perfect for running, great cushioning.",
    "Arrived quickly and looked exactly like the photos.",
]
review_count = 0
for _ in range(50):
    product = random.choice(products)
    user = random.choice(demo_users) if demo_users else None
    if not user:
        break
    if Review.objects.filter(product=product, user=user).exists():
        continue
    Review.objects.create(
        product=product, user=user, rating=random.randint(3, 5),
        title=random.choice(["Great fit!", "Love it", "Solid purchase", "Would recommend", ""]),
        comment=random.choice(review_comments),
    )
    review_count += 1

for product in products:
    reviews = product.reviews.all()
    if reviews:
        avg = sum(r.rating for r in reviews) / reviews.count()
        product.rating = round(avg, 2)
        product.rating_count = reviews.count()
        product.save(update_fields=["rating", "rating_count"])
print(f"Created {review_count} reviews")

# ---------------- Banners ----------------
banner_data = [
    ("Step Into Your Power", "Premium sneakers built for everyday greatness.", "Shop Sneakers"),
    ("Run Further, Feel Lighter", "Discover our new running shoe collection.", "Shop Running"),
    ("Boots Built To Last", "Rugged, weatherproof, and always in style.", "Shop Boots"),
]
for i, (title, subtitle, btn) in enumerate(banner_data):
    banner = Banner(title=title, subtitle=subtitle, button_text=btn, button_link="/shop/", order=i)
    banner.image.save(f"banner-{i}.jpg", make_placeholder_image(title, size=(1600, 700)), save=True)
print("Created banners")

# ---------------- Testimonials ----------------
testimonial_data = [
    ("Arjun Menon", "Marathon Runner", "Shoeland's running shoes changed my training completely. Lightweight and supportive.", 5),
    ("Priya Nair", "Fashion Blogger", "The sneaker collection is unmatched — always on trend and true to size.", 5),
    ("Kiran Das", "College Student", "Affordable, comfortable, and stylish. My whole friend group shops here now.", 4),
]
for name, role, msg, rating in testimonial_data:
    t = Testimonial(name=name, designation=role, message=msg, rating=rating)
    t.photo.save(f"{name.replace(' ','-').lower()}.jpg", make_placeholder_image(name, size=(300, 300)), save=True)
print("Created testimonials")

# ---------------- Instagram posts ----------------
for i in range(6):
    post = InstagramPost(order=i)
    post.image.save(f"insta-{i}.jpg", make_placeholder_image(f"#Shoeland {i+1}", size=(500, 500)), save=True)
print("Created instagram posts")

# ---------------- Coupons ----------------
Coupon.objects.create(
    code="WELCOME10", discount_type="percent", discount_value=Decimal("10"),
    minimum_order_amount=Decimal("999"), valid_from=timezone.now() - timedelta(days=1),
    valid_to=timezone.now() + timedelta(days=90), usage_limit=500,
)
Coupon.objects.create(
    code="FLAT200", discount_type="flat", discount_value=Decimal("200"),
    minimum_order_amount=Decimal("1999"), valid_from=timezone.now() - timedelta(days=1),
    valid_to=timezone.now() + timedelta(days=90), usage_limit=200,
)
print("Created coupons: WELCOME10, FLAT200")

# ---------------- Sample Orders ----------------
from orders.models import Order, OrderItem

order_count = 0
for user in demo_users[:10]:
    for _ in range(random.randint(1, 3)):
        chosen = random.sample(products, k=random.randint(1, 3))
        subtotal = sum(p.current_price for p in chosen)
        shipping = Decimal("0.00") if subtotal >= Decimal("1999") else Decimal("99.00")
        tax = (subtotal * Decimal("5") / Decimal("100")).quantize(Decimal("0.01"))
        grand_total = subtotal + shipping + tax
        order = Order.objects.create(
            user=user, full_name=user.get_full_name() or user.username, phone="9876543210",
            email=user.email, shipping_line1="123 MG Road", shipping_city="Kochi",
            shipping_state="Kerala", shipping_postal_code="682001", shipping_country="India",
            subtotal=subtotal, shipping_charge=shipping, tax_amount=tax, grand_total=grand_total,
            payment_method=random.choice(["cod", "razorpay", "stripe"]),
            payment_status=random.choice(["paid", "pending"]),
            status=random.choice(["pending", "confirmed", "processing", "shipped", "delivered"]),
        )
        for p in chosen:
            OrderItem.objects.create(order=order, product=p, product_name=p.name, product_sku=p.sku, price=p.current_price, quantity=1)
        order_count += 1
print(f"Created {order_count} sample orders")

print("\n✅ Sample data generation complete!")
