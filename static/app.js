(function () {
  var spectrum = document.getElementById('moodSpectrum');
  if (!spectrum) return;

  spectrum.addEventListener('change', function (e) {
    var radio = e.target.closest('input[type="radio"]');
    if (!radio) return;
    spectrum.querySelectorAll('.spectrum-item').forEach(function (el) {
      el.classList.remove('active');
    });
    radio.closest('.spectrum-item').classList.add('active');
  });

  var tagGrid = document.querySelector('.tag-grid');
  if (tagGrid) {
    tagGrid.addEventListener('change', function (e) {
      var cb = e.target.closest('input[type="checkbox"]');
      if (!cb) return;
      cb.closest('.tag-select').classList.toggle('active', cb.checked);
    });
  }
})();
