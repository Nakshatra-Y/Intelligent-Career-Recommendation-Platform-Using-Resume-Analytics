document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const isLoggedIn = body.getAttribute("data-logged-in") === "true";
  const showUpload = body.getAttribute("data-show-upload") === "true";

  const btnGetStarted = document.getElementById("btnGetStarted");
  const btnUploadHero = document.getElementById("btnUploadHero");
  const uploadSection = document.getElementById("uploadSection");
  const analyzeBtn = document.getElementById("analyzeBtn");

  const scrollToUpload = () => {
    if (!uploadSection) return;
    const rect = uploadSection.getBoundingClientRect();
    const offset = window.scrollY + rect.top - 80;
    window.scrollTo({ top: offset, behavior: "smooth" });
  };

  const goToAuth = () => {
    window.location.href = "/auth";
  };

  if (btnGetStarted) {
    btnGetStarted.addEventListener("click", () => {
      if (isLoggedIn) {
        scrollToUpload();
      } else {
        goToAuth();
      }
    });
  }

  if (btnUploadHero) {
    btnUploadHero.addEventListener("click", () => {
      if (isLoggedIn) {
        scrollToUpload();
      } else {
        goToAuth();
      }
    });
  }

  // If user landed here after login with show_upload=1, scroll automatically
  if (isLoggedIn && showUpload) {
    setTimeout(scrollToUpload, 400);
  }

  // If user is not logged in, clicking "Analyze" should take them to auth
  if (!isLoggedIn && analyzeBtn) {
    analyzeBtn.addEventListener("click", (e) => {
      e.preventDefault();
      goToAuth();
    });
  }

  // Animated score meter (random score each refresh)
  const scoreValueEl = document.getElementById("scoreValue");
  const scoreRing = document.getElementById("scoreRingProgress");

  if (scoreValueEl && scoreRing) {
    const maxCircumference = 389; // matches CSS
    const targetScore = Math.floor(Math.random() * 31) + 70; // 70–100
    let current = 0;

    const duration = 1200;
    const start = performance.now();

    const animate = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      current = Math.round(targetScore * eased);
      scoreValueEl.textContent = String(current);

      const ratio = current / 100;
      const offset = maxCircumference * (1 - ratio);
      scoreRing.style.strokeDashoffset = offset;

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }
});

