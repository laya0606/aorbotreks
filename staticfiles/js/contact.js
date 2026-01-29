function handleUserType() {
        const userType = document.getElementById("user_type").value;
        const trekCategory = document.getElementById("trek_category_div");
        const vendorInfo = document.getElementById("vendor_info_div");

        // Hide all first
        trekCategory.classList.add("hidden");
        vendorInfo.classList.add("hidden");

        if (userType === "trekker") {
            trekCategory.classList.remove("hidden");
        }

        if (userType === "organizer") {
            vendorInfo.classList.remove("hidden");
        }
    }

    // Initialize Lottie animation
    let lottieInstance = null;

    function initLottieAnimation() {
        if (!lottieInstance) {
            lottieInstance = lottie.loadAnimation({
                container: document.getElementById('lottieContainer'),
                renderer: 'svg',
                loop: false,
                autoplay: false,
                path: '{% static "lottiefile/aorbo.json" %}'
            });
        }
        return lottieInstance;
    }

document.addEventListener("DOMContentLoaded", function () {

    const contactForm = document.getElementById("contactForm");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");
    const lottieContainer = document.getElementById("lottieAnimation");
    const emailField = document.getElementById("email");

    // 🔹 Live Gmail validation
    emailField.addEventListener("input", function () {
        const email = emailField.value.trim().toLowerCase();
        emailField.setCustomValidity(
            email && !email.endsWith("@gmail.com")
                ? "Only Gmail addresses ending with @gmail.com are allowed."
                : ""
        );
    });

    // 🔹 CSRF helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 🔹 Submit handler
    contactForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        // Prevent double submit
        if (submitBtn.disabled) return;

        // HTML5 validation
        if (!contactForm.checkValidity()) {
            contactForm.classList.add("was-validated");
            return;
        }

        const csrftoken = getCookie("csrftoken");
        const formData = new FormData(contactForm);

        // UI state
        submitBtn.disabled = true;
        btnText.innerText = "Submitting...";
        lottieContainer.classList.remove("show");

        try {
            const response = await fetch(contactForm.action, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken
                },
                body: formData
            });

            let result = {};
            const contentType = response.headers.get("Content-Type") || "";
            if (contentType.includes("application/json")) {
                result = await response.json();
            }

            if (response.ok) {
                // Show Lottie animation popup
                lottieContainer.classList.add("show");
                const animation = initLottieAnimation();
                if (animation) {
                    animation.play();
                }

                contactForm.reset();
                contactForm.classList.remove("was-validated");
                handleUserType();
                btnText.innerText = "Submit";
                submitBtn.disabled = false;
                
                // Auto-hide popup after 10 seconds
                setTimeout(() => {
                    lottieContainer.classList.remove("show");
                    lottieContainer.classList.add("fadeOut");
                    setTimeout(() => {
                        lottieContainer.classList.remove("fadeOut");
                    }, 300);
                }, 4000);

            } else {
                const errorMsg = result.error || "Submission failed ❌";

                btnText.innerText = errorMsg;
                
                // Reset button after 3 seconds
                setTimeout(() => {
                    btnText.innerText = "Submit";
                    submitBtn.disabled = false;
                }, 3000);
            }

        } catch (error) {
            console.error("Form submission error:", error);

            const errorMessage = error.message || "Network error ❌";
            btnText.innerText = errorMessage;
            
            // Reset button after 3 seconds
            setTimeout(() => {
                btnText.innerText = "Submit";
                submitBtn.disabled = false;
            }, 3000);
        }
    });
});