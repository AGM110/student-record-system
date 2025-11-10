
(function () {
  const pwd = document.getElementById("new_password");
  const meter = document.getElementById("pwdStrength");
  const hint = document.getElementById("pwdHint");
  if (!pwd || !meter || !hint) return; 

  pwd.addEventListener("input", () => {
    const v = pwd.value || "";
    let score = 0;

    // Evaluate strength
    if (v.length >= 8) score++;
    if (/[A-Z]/.test(v)) score++;
    if (/[0-9]/.test(v)) score++;
    if (/[^A-Za-z0-9]/.test(v)) score++;

    // Update meter and text
    meter.value = score;
    const msgs = ["Very weak", "Weak", "Fair", "Good", "Strong"];
    const colors = ["#991b1b", "#b45309", "#a16207", "#065f46", "#166534"];

    hint.textContent = msgs[score];
    hint.style.color = colors[score];
  });
})();


document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll('form[action*="delete_confirmed"]');
  forms.forEach(form => {
    form.addEventListener("submit", (e) => {
      const code = form.querySelector('input[name="code"]')?.value || "";
      const msg = code
        ? `Are you sure you want to delete this student (code: ${code})? This cannot be undone.`
        : `Are you sure you want to delete this student? This cannot be undone.`;
      if (!window.confirm(msg)) e.preventDefault();
    });
  });
});



document.addEventListener("DOMContentLoaded", () => {
  const flashes = document.querySelectorAll(".flash-success, .flash-error, .alert");
  flashes.forEach((msg) => {
    setTimeout(() => {
      msg.style.transition = "opacity 0.6s ease";
      msg.style.opacity = "0";
      setTimeout(() => msg.remove(), 600); 
    }, 3500); 
  });
});
