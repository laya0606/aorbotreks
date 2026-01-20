/* static/js/main.js
   - Handles cookie banner Accept & Decline
   - Sets cookie "cookiesAccepted" to "true" or "false" for 365 days
   - Example: conditionally load analytics when accepted
*/

(function () {
  // helper: set cookie (days optional)
  function setCookie(name, value, days) {
    let expires = "";
    if (typeof days === "number") {
      const d = new Date();
      d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
      expires = "; expires=" + d.toUTCString();
    }
    // SameSite=Lax is a good default; add ; Secure when serving over HTTPS in production
    document.cookie = name + "=" + encodeURIComponent(value) + expires + "; path=/; SameSite=Lax";
  }

  // helper: get cookie
  function getCookie(name) {
    const match = document.cookie.split("; ").find(row => row.startsWith(name + "="));
    return match ? decodeURIComponent(match.split("=")[1]) : null;
  }

  // helper: delete cookie
  function deleteCookie(name) {
    document.cookie = name + "=; Max-Age=0; path=/; SameSite=Lax";
  }

  // Example functions to enable/disable third-party scripts (analytics, trackers)
  // Replace or extend with your real initialization code.
  function enableThirdParty() {
    // Example dynamic load for Google Analytics (replace ID with yours)
    if (!window.__aorbo_analytics_loaded) {
      const gaId = "G-XXXXXXXXXX"; // <- replace with your GA ID (or leave commented if not used)
      if (gaId && gaId.indexOf("G-") === 0) {
        const s = document.createElement("script");
        s.src = "https://www.googletagmanager.com/gtag/js?id=" + gaId;
        s.async = true;
        document.head.appendChild(s);

        window.dataLayer = window.dataLayer || [];
        function gtag(){ window.dataLayer.push(arguments); }
        window.gtag = gtag;
        gtag("js", new Date());
        gtag("config", gaId);
      }
      window.__aorbo_analytics_loaded = true;
    }
  }

  function disableThirdParty() {
    // Example: remove common GA cookies if present.
    // Add other cookie names used by your trackers as needed.
    deleteCookie("_ga");
    deleteCookie("_gid");
    deleteCookie("_gat");
    // flag to prevent init
    window.__aorbo_analytics_loaded = false;
  }

  // DOM ready
  document.addEventListener("DOMContentLoaded", function () {
    const banner = document.getElementById("cookie-banner");
    const acceptBtn = document.getElementById("accept-cookies");
    const declineBtn = document.getElementById("decline-cookies");

    // If element missing, safely exit
    if (!banner) return;

    // Check saved consent
    const consent = getCookie("cookiesAccepted"); // "true", "false", or null

    if (consent === null) {
      // first-time visitor -> show banner
      banner.classList.remove("d-none");
    } else {
      // already chosen: if accepted, init third-party services
      if (consent === "true") {
        enableThirdParty();
      } else {
        // explicit decline -> make sure trackers not loaded
        disableThirdParty();
      }
      // don't show banner
    }

    // Accept handler
    if (acceptBtn) {
      acceptBtn.addEventListener("click", function () {
        setCookie("cookiesAccepted", "true", 365);
        banner.classList.add("d-none");
        enableThirdParty();
      });
    }

    // Decline handler
    if (declineBtn) {
      declineBtn.addEventListener("click", function () {
        setCookie("cookiesAccepted", "false", 365);
        banner.classList.add("d-none");
        disableThirdParty();
      });
    }

    // Optional: Allow keyboard interaction (Esc to close)
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        banner.classList.add("d-none");
      }
    });
  });
})();
