// ── Campaign switcher ──
const switcherToggle = document.getElementById('switcherToggle');
const switcherDropdown = document.getElementById('switcherDropdown');
if (switcherToggle) {
  switcherToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    switcherDropdown.classList.toggle('open');
  });
  document.addEventListener('click', () => switcherDropdown.classList.remove('open'));
}

// ── Initiative panel ──
const initiativePanel = document.getElementById('initiativePanel');
document.getElementById('initiativeToggle')?.addEventListener('click', () => {
  initiativePanel.classList.toggle('open');
});
document.getElementById('initiativeClose')?.addEventListener('click', () => {
  initiativePanel.classList.remove('open');
});

let initiativeList = [];

function renderInitiative() {
  const container = document.getElementById('initiativeList');
  container.innerHTML = '';
  initiativeList.forEach((entry, i) => {
    const row = document.createElement('div');
    row.className = 'initiative-row' + (i === 0 ? ' current' : '');
    row.innerHTML = `
      <span class="init-rank">${entry.init}</span>
      <span class="init-name">${entry.name}</span>
      <button class="init-remove" onclick="removeInitiative(${i})">✕</button>
    `;
    container.appendChild(row);
  });
}

function addInitiative() {
  const name = document.getElementById('initName').value.trim();
  const init = parseInt(document.getElementById('initNumber').value);
  if (!name || isNaN(init)) return;
  initiativeList.push({ name, init });
  document.getElementById('initName').value = '';
  document.getElementById('initNumber').value = '';
  document.getElementById('initName').focus();
  renderInitiative();
}

function sortInitiative() {
  initiativeList.sort((a, b) => b.init - a.init);
  renderInitiative();
}

function removeInitiative(i) {
  initiativeList.splice(i, 1);
  renderInitiative();
}

function clearInitiative() {
  initiativeList = [];
  renderInitiative();
}

// Enter to add
document.getElementById('initNumber')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') addInitiative();
});
