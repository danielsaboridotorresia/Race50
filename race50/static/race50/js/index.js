document.getElementById('upload-button').onclick = function () {
  const url = this.dataset.url;
  window.location.href = url;
};