(() => {
  const navToggle = document.querySelector("[data-nav-toggle]");
  const nav = document.getElementById("site-nav");

  if (navToggle && nav) {
    navToggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
      navToggle.classList.toggle("is-open", isOpen);
    });

    nav.addEventListener("click", (event) => {
      if (event.target.closest("a") && window.innerWidth <= 820) {
        nav.classList.remove("is-open");
        navToggle.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.querySelectorAll("[data-dismiss-flash]").forEach((button) => {
    button.addEventListener("click", () => {
      button.closest(".flash")?.remove();
    });
  });

  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const value = button.getAttribute("data-copy");
      if (!value) return;

      try {
        await navigator.clipboard.writeText(value);
      } catch {
        const helper = document.createElement("textarea");
        helper.value = value;
        helper.setAttribute("readonly", "");
        helper.style.position = "fixed";
        helper.style.opacity = "0";
        document.body.appendChild(helper);
        helper.select();
        document.execCommand("copy");
        helper.remove();
      }

      const original = button.textContent;
      button.textContent = "Copied";
      button.classList.add("is-copied");
      window.setTimeout(() => {
        button.textContent = original;
        button.classList.remove("is-copied");
      }, 1800);
    });
  });

  const fileInput = document.querySelector("[data-file-input]");
  const fileName = document.querySelector("[data-file-name]");
  if (fileInput && fileName) {
    fileInput.addEventListener("change", () => {
      const file = fileInput.files && fileInput.files[0];
      fileName.textContent = file ? file.name : "No photo selected";
      fileName.classList.toggle("has-file", Boolean(file));
    });
  }

  const description = document.getElementById("description");
  const descriptionCount = document.querySelector("[data-description-count]");
  if (description && descriptionCount) {
    const updateCount = () => {
      descriptionCount.textContent = `${description.value.length} / 3000`;
    };
    description.addEventListener("input", updateCount);
    updateCount();
  }

  const passwordChecks = [
    (value) => value.length >= 12,
    (value) => /[A-Z]/.test(value),
    (value) => /[a-z]/.test(value),
    (value) => /[0-9]/.test(value),
    (value) => /[^A-Za-z0-9]/.test(value),
  ];

  document.querySelectorAll("[data-password-form]").forEach((form) => {
    const input = form.querySelector("[data-password-input]");
    const confirm = form.querySelector("[data-password-confirm]");
    const meter = form.querySelector("[data-password-meter]");
    const matchNote = form.querySelector("[data-password-match]");
    const rules = Array.from(form.querySelectorAll("[data-password-rules] li"));
    if (!input) return;

    const updatePasswordHints = () => {
      const value = input.value;
      let met = 0;

      rules.forEach((rule, index) => {
        const check = passwordChecks[index];
        const passed = check ? check(value) : false;
        rule.classList.toggle("is-met", passed);
        if (passed) met += 1;
      });

      if (meter) {
        meter.style.width = `${Math.round((met / passwordChecks.length) * 100)}%`;
        meter.classList.toggle("is-medium", met >= 3 && met < passwordChecks.length);
        meter.classList.toggle("is-strong", met === passwordChecks.length);
      }

      if (confirm && matchNote) {
        const mismatch = confirm.value.length > 0 && confirm.value !== value;
        matchNote.hidden = !mismatch;
      }
    };

    input.addEventListener("input", updatePasswordHints);
    confirm?.addEventListener("input", updatePasswordHints);
    updatePasswordHints();
  });
})();
