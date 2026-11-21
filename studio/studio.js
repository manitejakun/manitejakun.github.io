'use strict';
const el = id => document.getElementById(id);
const owner = 'manitejakun';
const repo = '/repos/' + owner + '/manitejakun.github.io';
const storageKey = 'mani-journal-studio-v1';
const kinds = ['Paragraph', 'Heading', 'Quote', 'Bullet list'];
let credential = '';
let busy = false;
function status(message) { el('status').textContent = message; }
async function api(path, token, options = {}) {
  const response = await fetch('https://api.github.com' + path, {
    ...options, redirect: 'error', credentials: 'omit', cache: 'no-store',
    headers: {Authorization: 'Bearer ' + token, 'Content-Type': 'application/json'}
  });
  if (!response.ok) throw new Error(response.status === 401 ? 'GitHub rejected the key.' :
    response.status === 422 || response.status === 409 ? 'That URL may already exist. Check the Journal before retrying.' :
    'GitHub returned ' + response.status + '. Check the key, repository access, and connection.');
  return response.json();
}
function resize(node) { node.style.height = 'auto'; node.style.height = node.scrollHeight + 3 + 'px'; }
function block(kind = 'Paragraph', value = '') {
  const row = document.createElement('div');
  row.className = 'block';
  const select = document.createElement('select');
  select.setAttribute('aria-label','Block type');
  for (const name of kinds) select.add(new Option(name,name));
  select.value = kinds.includes(kind) ? kind : kinds[0];
  const area = document.createElement('textarea');
  area.rows = 1; area.placeholder = 'Start writing…'; area.value = value;
  function style() { row.dataset.kind = select.value; area.setAttribute('aria-label',select.value + ' text'); resize(area); }
  select.onchange = () => { style(); save(); area.focus(); };
  area.oninput = () => { resize(area); if (area.value === '/') { area.value = ''; select.focus(); } };
  area.onkeydown = event => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing && area.selectionEnd === area.value.length) {
      event.preventDefault(); const next = block(); row.after(next); next.querySelector('textarea').focus(); save();
    } else if (event.key === 'Backspace' && !area.value && row.previousElementSibling) {
      event.preventDefault(); row.previousElementSibling.querySelector('textarea').focus(); row.remove(); save();
    }
  };
  row.append(select,area); el('blocks').append(row); style(); return row;
}
const fields = ['title','date','slug','description','cover','alt'];
function snapshot() {
  return {...Object.fromEntries(fields.map(id => [id,el(id).value])),
    blocks:Array.from(el('blocks').children, row => [row.dataset.kind,row.querySelector('textarea').value])};
}
function save() {
  if (!credential) return;
  try { localStorage.setItem(storageKey,JSON.stringify(snapshot())); el('saved').textContent = 'Draft saved on this device'; }
  catch { el('saved').textContent = 'Device storage unavailable'; }
}
function openDesk() {
  let draft = {};
  try { draft = JSON.parse(localStorage.getItem(storageKey)) || {}; } catch {}
  el('gate').hidden = true; el('desk').hidden = false;
  for (const id of fields) el(id).value = draft[id] || '';
  if (!el('date').value) { const d = new Date(); d.setMinutes(d.getMinutes()-d.getTimezoneOffset()); el('date').value = d.toISOString().slice(0,10); }
  el('blocks').replaceChildren(); for (const [kind,value] of draft.blocks?.length ? draft.blocks : [['Paragraph','']]) block(kind,value);
  resize(el('title')); el('title').focus();
}
el('auth').onsubmit = async event => {
  event.preventDefault(); const token = el('key').value.trim(); el('key').value = '';
  try {
    const user = await api('/user',token);
    if (user.login.toLowerCase() !== owner) throw new Error('This studio belongs to Mani Teja.');
    const access = await api(repo,token);
    if (!access.permissions?.push) throw new Error('Repository write access is required.');
    credential = token; status(''); openDesk();
  } catch (error) { status(error.message); }
};
el('desk').oninput = save;
el('title').oninput = () => resize(el('title'));
el('add').onclick = () => { block().querySelector('textarea').focus(); save(); };
el('lock').onclick = () => { if (!busy) location.reload(); };
el('publish').onclick = async () => {
  if (busy || !credential) return;
  const draft = snapshot();
  const slug = draft.slug.trim() || draft.title.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  const body = draft.blocks.filter(([,s]) => s.trim()).map(([kind,s]) =>
    kind === 'Heading' ? '## ' + s : kind === 'Quote' || kind === 'Bullet list' ?
    s.split('\n').map(line => (kind === 'Quote' ? '> ' : '- ') + line).join('\n') : s).join('\n\n');
  if (!draft.title.trim() || !body.trim() || !draft.date || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
    status('Add a title, writing, date and a valid URL slug.'); return;
  }
  if (!confirm('Publish this entry to your public Journal?')) return;
  const entry = {title:draft.title.trim(),slug,publication_date:draft.date,description:draft.description,cover:draft.cover,cover_alt:draft.alt,body,status:'published'};
  busy = true; el('desk').inert = true; status('Publishing…');
  try {
    const bytes = new TextEncoder().encode(JSON.stringify(entry,null,2) + '\n');
    const content = btoa(Array.from(bytes,b => String.fromCharCode(b)).join(''));
    await api(repo + '/contents/content/writing/' + slug + '.json',credential,
      {method:'PUT',body:JSON.stringify({message:'Publish Journal entry: ' + entry.title,branch:'main',content})});
    localStorage.removeItem(storageKey); openDesk(); el('saved').textContent = '';
    status('Published to GitHub. Your Journal will update after deployment.');
  } catch (error) { status(error.message); } finally { busy = false; el('desk').inert = false; }
};
