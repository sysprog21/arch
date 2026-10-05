const prefix = document.getElementById('prefix');
const picker = document.getElementById('fork-picker');
const selected = document.getElementById('selected');
const rows = [...document.querySelectorAll('#fork-list tr')];

function filterForks() {
  const query = prefix.value.trim().toLowerCase();
  picker.length = 1;
  selected.hidden = true;
  let count = 0;
  for (const row of rows) {
    row.hidden = !row.dataset.owner.toLowerCase().startsWith(query);
    if (!row.hidden) {
      const link = row.querySelector('a');
      picker.add(new Option(link.textContent, link.href));
      count++;
    }
  }
  picker.disabled = count === 0;
  document.getElementById('matches').textContent = `${count} matching / ${rows.length} total forks`;
}

prefix.addEventListener('input', filterForks);
picker.addEventListener('change', () => {
  selected.hidden = !picker.value;
  if (picker.value) {
    selected.href = picker.value;
    selected.textContent = `Open ${picker.selectedOptions[0].textContent}`;
  }
});
filterForks();
