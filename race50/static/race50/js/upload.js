const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('sessionFile');
const fileNameDisplay = document.getElementById('file-name');

// clicking the box triggers the file input
dropzone.addEventListener('click', () => fileInput.click());

// highlight dropzone on drag
dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('bg-light');
});
dropzone.addEventListener('dragleave', () => {
  dropzone.classList.remove('bg-light');
});

// handle drop
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('bg-light');
  if (e.dataTransfer.files.length) {
    fileInput.files = e.dataTransfer.files;  // attach files to hidden input
    fileNameDisplay.textContent = "Selected: " + e.dataTransfer.files[0].name;
  }
});

// handle normal selection
fileInput.addEventListener('change', (e) => {
  if (e.target.files.length) {
    fileNameDisplay.textContent = "Selected: " + e.target.files[0].name;
  }
});
