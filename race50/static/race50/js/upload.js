// Block default drop anywhere on the page
['dragover', 'drop'].forEach(evt => {
  window.addEventListener(evt, e => e.preventDefault(), false);
  document.addEventListener(evt, e => e.preventDefault(), false);
});

document.addEventListener('DOMContentLoaded', function () {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('sessionFile');
  const fileNameDisplay = document.getElementById('file-name');
  if (!dropzone || !fileInput || !fileNameDisplay) return;

  // Stop bubbling when you drop on the zone
  dropzone.addEventListener('dragover', e => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add('bg-light');
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy';
  });

  dropzone.addEventListener('dragleave', e => {
    e.stopPropagation();
    dropzone.classList.remove('bg-light');
  });

  dropzone.addEventListener('drop', e => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('bg-light');
    if (e.dataTransfer && e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      fileNameDisplay.textContent = 'Selected: ' + e.dataTransfer.files[0].name;
    }
  });

  // Click to open chooser
  dropzone.addEventListener('click', () => fileInput.click());

  // Normal selection
  fileInput.addEventListener('change', e => {
    if (e.target.files.length) {
      fileNameDisplay.textContent = 'Selected: ' + e.target.files[0].name;
    }
  });
});