'use strict';
const el=id=>document.getElementById(id);
const kinds=['Paragraph','Heading','Quote','Bullet list','Link'];
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
let id=crypto.randomUUID(), original={}, timer, chain=Promise.resolve();
const fields=['title','slug','description','subtitle','caption','alt','date'];
const labels={caption:'cover_caption',alt:'cover_alt',date:'publication_date'};
const status=text=>el('status').textContent=text;
async function call(path,method='GET',body){
  const response=await fetch(path,{method,body:body instanceof File?body:JSON.stringify(body),headers:body instanceof File?{}:{'Content-Type':'application/json'}});
  if(!response.ok)throw Error(response.status===401?'Sign-in expired. Keep this tab open.':response.status===409?'Another version exists. Reopen the published entry to compare.':'Request failed. Your writing is still here. Retry when connected.');
  return response.status===204?null:response.json();
}
function snapshot(){
  const post={...original};
  for(const field of fields)post[labels[field]||field]=el(field).value;
  post.blocks=Array.from(el('blocks').children,row=>[row.dataset.kind,row.querySelector('textarea').value]);
  post.body=post.blocks.map(([k,s])=>k==='Link' && /^https?:\/\/[^\s<>]+$/.test(s)?'<'+s+'>':k==='Heading'?'## '+s:k==='Quote'||k==='Bullet list'?s.split('\n').map(l=>(k==='Quote'?'> ':'- ')+l).join('\n'):s).join('\n\n');
  return post;
}
function flush(){
  clearTimeout(timer);const key=id,payload=snapshot();
  chain=chain.catch(()=>{}).then(()=>call('/draft/'+key,'PUT',payload));return chain;
}
function save(){el('saved').textContent='Saving…';clearTimeout(timer);timer=setTimeout(()=>flush().then(()=>el('saved').textContent='Saved privately').catch(e=>status(e.message)),450);}
function open(post,key){
  original=post;id=key||crypto.randomUUID();history.replaceState(null,'','#'+id);
  for(const f of fields)el(f).value=post[labels[f]||f]||(f==='date'?new Date().toLocaleDateString('en-CA'):'');
  el('slug').readOnly=!!post.source_sha;el('blocks').replaceChildren();
  for(const [k,v] of post.blocks||[['Paragraph',post.body||'']])block(k,v);
  el('file').value='';resize(el('title'));el('saved').textContent='';status('');
}
async function library(){
  const list=el('library');list.replaceChildren(new Option('Open an entry',''));
  for(const d of await call('/drafts'))list.add(new Option('Draft · '+d.title,d.id));
  for(const p of await call('/published')){const o=new Option('Published · '+p.title,'published');o.post=p;list.add(o);}
}
function action(fn){return async()=>{el('desk').inert=true;try{await fn();}catch(e){status(e.message);}finally{el('desk').inert=false;}};}
el('library').onchange=action(async()=>{const o=el('library').selectedOptions[0];if(!o.value)return;if(snapshot().title||snapshot().body)await flush();open(o.post||await call('/draft/'+o.value),o.post?null:o.value);});
el('new').onclick=action(async()=>{await flush();open({});await library();});
el('add').onclick=()=>{block().querySelector('textarea').focus();save();};
el('desk').oninput=save;el('title').oninput=()=>resize(el('title'));
el('file').onchange=action(async()=>{const f=el('file').files[0];if(f){await flush();await call('/cover/'+id,'PUT',f);status('Cover saved privately.');}});
el('preview').onclick=action(async()=>{await flush();location.href='/preview/'+id;});
el('lock').onclick=action(async()=>{await flush();await call('/logout','POST');location.href='https://maniteja.me/journal/';});
el('publish').onclick=action(async()=>{if(!el('slug').value)el('slug').value=el('title').value.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');if(!confirm('Publish this entry and its cover to your public Journal?'))return;await flush();const result=await call('/publish/'+id,'POST');original.source_sha=result.sha;el('slug').readOnly=true;status('Committed. GitHub Pages deployment is pending.');const a=document.createElement('a');a.href='https://github.com/manitejakun/manitejakun.github.io/actions';a.textContent=' Check deployment';el('status').append(a);await library();watchDeployment(result.commit,el('slug').value,id);});
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='s'){e.preventDefault();flush().then(()=>status('Saved privately.')).catch(e=>status(e.message));}});
const resume=location.hash.slice(1);if(/^[0-9a-f-]{36}$/.test(resume)){call('/draft/'+resume).then(p=>open(p,resume)).catch(e=>status(e.message));}else open({});library().catch(e=>status(e.message));

async function watchDeployment(commit,slug,key){
  if(key!==id)return;
  try {
    const result=await call('/deployment/'+commit+'?slug='+encodeURIComponent(slug));
    if(key!==id)return;
    status('Deployment: '+result.state);
    if(result.live){
      const link=document.createElement('a');link.href=result.live;link.textContent=' Open live entry';el('status').append(link);return;
    }
    if(['queued','in_progress','waiting','pending','success'].includes(result.state)){
      setTimeout(()=>watchDeployment(commit,slug,key),10000);
    }else{
      const link=document.createElement('a');link.href='https://github.com/manitejakun/manitejakun.github.io/actions';link.textContent=' Review or retry the deployment';el('status').append(link);
    }
  }catch{status('Committed. Check GitHub Actions for the deployment result.');}
}
