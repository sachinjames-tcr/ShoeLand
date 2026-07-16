/* Shoeland front-end interactions */
document.addEventListener("DOMContentLoaded", function () {

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }
  const csrftoken = getCookie("csrftoken");

  function ajaxPost(url, data) {
    return fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams(data),
    }).then((r) => r.json());
  }

  function showToast(message, type) {
    let container = document.getElementById("toastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "toastContainer";
      container.style.position = "fixed";
      container.style.top = "90px";
      container.style.right = "20px";
      container.style.zIndex = "2000";
      document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = "toast-shoeland p-3 mb-2 rounded shadow";
    toast.style.minWidth = "260px";
    toast.innerHTML = `<i class="bi ${type === "error" ? "bi-exclamation-circle" : "bi-check-circle"} me-2 text-orange"></i>${message}`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = "opacity .4s";
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 400);
    }, 2500);
  }

  /* ---------- AJAX Add to Cart ---------- */
  document.querySelectorAll(".ajax-add-to-cart").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const productId = this.dataset.productId;
      const qtyInput = document.querySelector(`#qty-${productId}`);
      const quantity = qtyInput ? qtyInput.value : 1;

      ajaxPost(`/cart/add/${productId}/`, { quantity }).then((data) => {
        if (data.success) {
          showToast(data.message, "success");
          document.querySelectorAll(".cart-count-badge").forEach((el) => (el.textContent = data.cart_total_items));
        }
      });
    });
  });

  /* ---------- AJAX Wishlist Toggle ---------- */
  document.querySelectorAll(".ajax-wishlist-toggle").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const productId = this.dataset.productId;
      ajaxPost(`/wishlist/toggle/${productId}/`, {}).then((data) => {
        if (data.success) {
          this.classList.toggle("active", data.added);
          showToast(data.added ? "Added to wishlist" : "Removed from wishlist", "success");
          document.querySelectorAll(".wishlist-count-badge").forEach((el) => (el.textContent = data.wishlist_total_items));
        } else {
          window.location.href = "/accounts/login/";
        }
      });
    });
  });

  /* ---------- Quantity increment / decrement ---------- */
  document.querySelectorAll(".qty-decrement").forEach((btn) => {
    btn.addEventListener("click", function () {
      const input = this.parentElement.querySelector(".qty-input");
      let val = parseInt(input.value || "1", 10);
      if (val > 1) input.value = val - 1;
      input.dispatchEvent(new Event("change"));
    });
  });
  document.querySelectorAll(".qty-increment").forEach((btn) => {
    btn.addEventListener("click", function () {
      const input = this.parentElement.querySelector(".qty-input");
      let val = parseInt(input.value || "1", 10);
      input.value = val + 1;
      input.dispatchEvent(new Event("change"));
    });
  });

  /* ---------- Cart page: live quantity update ---------- */
  document.querySelectorAll(".cart-qty-input").forEach((input) => {
    input.addEventListener("change", function () {
      const productId = this.dataset.productId;
      ajaxPost(`/cart/update/${productId}/`, { quantity: this.value }).then((data) => {
        if (data.success) location.reload();
      });
    });
  });

  /* ---------- Live search ---------- */
  const searchInput = document.getElementById("liveSearchInput");
  const resultsBox = document.getElementById("liveSearchResults");
  if (searchInput && resultsBox) {
    let debounceTimer;
    searchInput.addEventListener("input", function () {
      clearTimeout(debounceTimer);
      const q = this.value.trim();
      if (q.length < 2) {
        resultsBox.style.display = "none";
        return;
      }
      debounceTimer = setTimeout(() => {
        fetch(`/search/ajax/?q=${encodeURIComponent(q)}`)
          .then((r) => r.json())
          .then((data) => {
            if (!data.results.length) {
              resultsBox.style.display = "none";
              return;
            }
            resultsBox.innerHTML = data.results
              .map(
                (p) => `<a href="${p.url}">
                  <img src="${p.image}" alt="">
                  <span>${p.name}<br><strong>₹${p.price}</strong></span>
                </a>`
              )
              .join("");
            resultsBox.style.display = "block";
          });
      }, 300);
    });
    document.addEventListener("click", (e) => {
      if (!resultsBox.contains(e.target) && e.target !== searchInput) {
        resultsBox.style.display = "none";
      }
    });
  }

  /* ---------- Bootstrap form validation ---------- */
  document.querySelectorAll(".needs-validation").forEach((form) => {
    form.addEventListener(
      "submit",
      function (event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add("was-validated");
      },
      false
    );
  });

  /* ---------- Scroll to top ---------- */
  const scrollBtn = document.getElementById("scrollTopBtn");
  if (scrollBtn) {
    window.addEventListener("scroll", () => {
      scrollBtn.style.display = window.scrollY > 400 ? "flex" : "none";
    });
    scrollBtn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  }

  /* ---------- Product gallery thumbnail swap ---------- */
  document.querySelectorAll(".gallery-thumb").forEach((thumb) => {
    thumb.addEventListener("click", function () {
      const mainImg = document.getElementById("mainProductImage");
      if (mainImg) mainImg.src = this.dataset.fullImage;
      document.querySelectorAll(".gallery-thumb").forEach((t) => t.classList.remove("active-thumb"));
      this.classList.add("active-thumb");
    });
  });

  /* ---------- Image zoom on hover (product detail) ---------- */
  const zoomWrap = document.querySelector(".zoom-wrap");
  if (zoomWrap) {
    const img = zoomWrap.querySelector("img");
    zoomWrap.addEventListener("mousemove", function (e) {
      const rect = zoomWrap.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      img.style.transformOrigin = `${x}% ${y}%`;
      img.style.transform = "scale(1.6)";
    });
    zoomWrap.addEventListener("mouseleave", () => {
      img.style.transform = "scale(1)";
    });
  }

  /* ---------- Newsletter AJAX (progressive enhancement optional; falls back to normal submit) ---------- */

  /* ---------- Auto-dismiss Django messages after a few seconds ---------- */
  document.querySelectorAll(".alert-dismissible").forEach((alert) => {
    setTimeout(() => {
      alert.classList.remove("show");
      setTimeout(() => alert.remove(), 300);
    }, 4500);
  });
});
