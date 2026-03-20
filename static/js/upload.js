document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("resumeFile");
  const fileNameDisplay = document.getElementById("fileName");
  const fileMetaDisplay = document.getElementById("fileMeta");
  const fileStatusPill = document.getElementById("fileStatus");
  const fileInfo = document.getElementById("fileInfo");
  const removeFileBtn = document.getElementById("removeFile");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const loaderOverlay = document.getElementById("loaderOverlay");
  const uploadForm = document.getElementById("uploadForm");

  let selectedFile = null;

  // Drag and Drop Handlers
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const files = e.dataTransfer.files;
    if (files.length) {
      handleFileSelection(files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length) {
      handleFileSelection(e.target.files[0]);
    }
  });

  removeFileBtn.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    fileInfo.classList.add("hidden");
    dropZone.classList.remove("hidden");
    analyzeBtn.disabled = true;
    if (fileMetaDisplay) fileMetaDisplay.textContent = "";
    if (fileStatusPill) fileStatusPill.classList.add("hidden");
  });

  const handleFileSelection = (file) => {
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    const extension = file.name.split(".").pop().toLowerCase();

    if (
      allowedTypes.includes(file.type) ||
      extension === "pdf" ||
      extension === "docx"
    ) {
      selectedFile = file;
      fileNameDisplay.textContent = file.name;

      // Calculate human-readable file size
      const sizeKB = file.size / 1024;
      const sizeText =
        sizeKB > 1024
          ? `${(sizeKB / 1024).toFixed(1)} MB`
          : `${Math.ceil(sizeKB)} KB`;

      const typeText = extension.toUpperCase();
      if (fileMetaDisplay) {
        fileMetaDisplay.textContent = `${typeText} • ${sizeText}`;
      }

      fileInfo.classList.remove("hidden");
      dropZone.classList.add("hidden");
      analyzeBtn.disabled = false;
      if (fileStatusPill) fileStatusPill.classList.remove("hidden");
    } else {
      alert("Please upload only .pdf or .docx files");
      fileInput.value = "";
    }
  };

  analyzeBtn.addEventListener("click", () => {
    if (!selectedFile) return;

    // Show loader and submit the form to the backend,
    // which will render the unified result page.
    loaderOverlay.classList.remove("hidden");
    uploadForm.submit();
  });
});
