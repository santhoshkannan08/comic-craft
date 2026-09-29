document.addEventListener("DOMContentLoaded", () => {
  // 1. Preset story buttons
  const presetChips = document.querySelectorAll(".preset-chip");
  const promptInput = document.getElementById("story_prompt");
  const charNameInput = document.getElementById("character_name");
  const settingInput = document.getElementById("setting");
  const toneSelect = document.getElementById("tone");
  const artStyleSelect = document.getElementById("art_style");
  const promptCharCount = document.getElementById("promptCharCount");

  const updateCharCount = () => {
    if (promptInput && promptCharCount) {
      promptCharCount.textContent = `${promptInput.value.length} / 2000`;
    }
  };

  if (promptInput) {
    promptInput.addEventListener("input", updateCharCount);
    updateCharCount();
  }

  presetChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.dataset.prompt || "";
      const name = chip.dataset.name || "";
      const setting = chip.dataset.setting || "";
      const tone = chip.dataset.tone || "Dramatic";
      const style = chip.dataset.style || "Comic Book";

      if (promptInput) promptInput.value = prompt;
      if (charNameInput) charNameInput.value = name;
      if (settingInput) settingInput.value = setting;
      if (toneSelect) toneSelect.value = tone;
      if (artStyleSelect) artStyleSelect.value = style;

      updateCharCount();

      // Highlight selected preset chip
      presetChips.forEach((c) => (c.style.backgroundColor = ""));
      chip.style.backgroundColor = "var(--accent-amber-light)";
      chip.style.borderColor = "var(--primary)";

      if (promptInput) {
        promptInput.focus();
      }
    });
  });

  // 2. Form submission and multi-step progress bar
  const form = document.getElementById("comicForm");
  const overlay = document.getElementById("loadingOverlay");
  const button = document.getElementById("generateButton");
  const loadingTitle = document.getElementById("loadingTitle");
  const loadingSub = document.getElementById("loadingSub");
  const progressBar = document.getElementById("progressBar");

  let progressInterval = null;

  const stages = [
    { step: "step1", percent: 25, title: "Structuring 5-Panel Arc...", desc: "Gemini Flash is drafting the panel beats & scene setups" },
    { step: "step2", percent: 50, title: "Writing Script & Dialogue...", desc: "Gemini Pro is crafting narrative captions & character lines" },
    { step: "step3", percent: 75, title: "Illustrating Comic Panels...", desc: "Rendering artwork with high-definition styling & comic palettes" },
    { step: "step4", percent: 95, title: "Assembling Graphic Layout...", desc: "Compiling panel sequence, captions, speech bubbles & printable PDF" },
  ];

  const runProgressStages = () => {
    let currentStageIndex = 0;

    const setStage = (idx) => {
      if (idx >= stages.length) return;
      const stage = stages[idx];

      if (loadingTitle) loadingTitle.textContent = stage.title;
      if (loadingSub) loadingSub.textContent = stage.desc;
      if (progressBar) progressBar.style.width = `${stage.percent}%`;

      // Update step dots
      for (let i = 1; i <= 4; i++) {
        const stepEl = document.getElementById(`step${i}`);
        if (stepEl) {
          if (i <= idx + 1) {
            stepEl.classList.add("active");
          } else {
            stepEl.classList.remove("active");
          }
        }
      }
    };

    setStage(0);

    progressInterval = setInterval(() => {
      currentStageIndex++;
      if (currentStageIndex < stages.length) {
        setStage(currentStageIndex);
      } else {
        clearInterval(progressInterval);
      }
    }, 1800);
  };

  if (form && button) {
    form.addEventListener("submit", (e) => {
      if (!form.checkValidity()) {
        return;
      }
      if (overlay) {
        overlay.hidden = false;
      }
      button.disabled = true;
      const btnText = button.querySelector(".btn-text");
      if (btnText) {
        btnText.textContent = "Creating Comic...";
      }
      runProgressStages();
    });
  }

  // Handle back button / page restore
  window.addEventListener("pageshow", () => {
    if (progressInterval) {
      clearInterval(progressInterval);
    }
    if (overlay) {
      overlay.hidden = true;
    }
    if (button) {
      button.disabled = false;
      const btnText = button.querySelector(".btn-text");
      if (btnText) {
        btnText.textContent = "Generate 5-Panel Comic";
      }
    }
  });

  // 3. Comic Preview View Switcher (Grid vs Strip)
  const gridViewBtn = document.getElementById("gridViewBtn");
  const stripViewBtn = document.getElementById("stripViewBtn");
  const panelContainer = document.getElementById("panelContainer");

  if (gridViewBtn && stripViewBtn && panelContainer) {
    gridViewBtn.addEventListener("click", () => {
      panelContainer.classList.remove("strip-mode");
      panelContainer.classList.add("grid-mode");
      gridViewBtn.classList.add("active");
      stripViewBtn.classList.remove("active");
    });

    stripViewBtn.addEventListener("click", () => {
      panelContainer.classList.remove("grid-mode");
      panelContainer.classList.add("strip-mode");
      stripViewBtn.classList.add("active");
      gridViewBtn.classList.remove("active");
    });
  }

  // 4. Copy Script to Clipboard
  const copyBtn = document.getElementById("copyStoryBtn");
  const copyBtnText = document.getElementById("copyBtnText");
  const rawScript = document.getElementById("rawScriptData");

  if (copyBtn && rawScript) {
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(rawScript.value.trim());
        if (copyBtnText) {
          const originalText = copyBtnText.textContent;
          copyBtnText.textContent = "Copied to Clipboard! ✓";
          setTimeout(() => {
            copyBtnText.textContent = originalText;
          }, 2500);
        }
      } catch (err) {
        console.error("Failed to copy script:", err);
      }
    });
  }
});
