document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("hero-search-input");
    if (!input) return;

    const box = input.closest(".hero-search-wrapper")
                     .querySelector(".search-suggestions");

    let debounceTimer = null;
    let currentIndex = -1;

    function clearSuggestions() {
        box.innerHTML = "";
        box.style.display = "none";
        currentIndex = -1;
    }

    function escapeRegex(text) {
        return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function highlight(text, query) {
        const re = new RegExp(`(${escapeRegex(query)})`, "ig");
        return text.replace(re, "<strong>$1</strong>");
    }

    function renderSuggestions(results, query) {
        if (!results.length) return clearSuggestions();

        box.innerHTML = "";
        results.forEach((item, i) => {
            const el = document.createElement("div");
            el.className = "search-suggestion-item";
            el.innerHTML = `
                <span class="search-suggestion-main">
                    ${highlight(item.label, query)}
                </span>
                <span class="search-suggestion-secondary">${item.type}</span>
            `;
            el.addEventListener("mousedown", () => location.href = item.url);
            box.appendChild(el);
        });
        box.style.display = "block";
    }

    input.addEventListener("input", () => {
        const q = input.value.trim();
        clearTimeout(debounceTimer);

        if (q.length < 2) return clearSuggestions();

        debounceTimer = setTimeout(() => {
            fetch(`/search-suggestions/?q=${encodeURIComponent(q)}`)
                .then(r => r.json())
                .then(d => renderSuggestions(d.results || [], q))
                .catch(clearSuggestions);
        }, 220);
    });

});
