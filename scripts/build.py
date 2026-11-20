#!/usr/bin/env python3
"""Genera public/index.html a partir de Wive.html (diseno original) conectado a Supabase.
Falla (assert) si alguna sustitucion no encuentra su objetivo, para no publicar a medias."""
import re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
s = (ROOT / 'Wive.html').read_text(encoding='utf-8')


def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, f'rep: esperaba {n}, hubo {c}: {old[:80]!r}'
    s = s.replace(old, new)


def rx(pat, new, flags=re.S):
    global s
    s, c = re.subn(pat, lambda m: new, s, flags=flags)
    assert c == 1, f'rx: esperaba 1, hubo {c}: {pat[:80]!r}'


# ---------- 1. supabase-js + CSS extra ----------
rep('<script>\nconst I={edit:', '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>\n<script>\nconst I={edit:')
rep('</style><link rel="stylesheet" href="https://fonts', r'''.xt{width:100%;border-collapse:collapse;font-size:13px}.xt td,.xt th{padding:5px 8px;border-bottom:1px solid var(--bd);text-align:left;white-space:nowrap}.xt td.m{white-space:normal;color:#ff8a8a}
</style><link rel="stylesheet" href="https://fonts''')

# ---------- 2. datos: Supabase en lugar de localStorage ----------
INIT = r'''const SB_URL='https://bndafmmgjwpfcpjiwyfo.supabase.co',SB_KEY='sb_publishable_Xntjbs5rOA0HPYYF5wnUKw_QiNs71nk';
const sb=supabase.createClient(SB_URL,SB_KEY,{auth:{flowType:'pkce',persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});
const CL='wive_cart_v2';
let S={cats:[],prods:[],orders:[],revs:[],links:[],about:'',wa:'',email:'',car:[],cart:[]};
let lim=60,ordKey=null,sending=false,loadErr=false,XP=null;
try{const c=JSON.parse(localStorage.getItem(CL));if(Array.isArray(c))S.cart=c.filter(x=>x&&typeof x.id=='string')}catch(e){}
const save=()=>{try{localStorage.setItem(CL,JSON.stringify(S.cart))}catch(e){}};
const run=f=>f().catch(e=>alert('Error: '+((e&&e.message)||e)));
async function fetchAll(mk){const out=[];for(let f=0;;f+=1000){const {data,error}=await mk().range(f,f+999);if(error)throw error;out.push(...data);if(data.length<1000)break}return out}
const mapP=r=>({id:r.id,code:r.sku,n:r.name,d:r.description||'',p:+r.price,o:r.old_price?+r.old_price:undefined,c:(r.categories&&r.categories.name)||'',col:r.colors||[],sz:r.sizes||[],f:r.featured?1:0,i:r.icon||'tag',img:(r.images||[])[0]||null,imgs:r.images||[],act:r.active});
async function loadPublic(){
 const [c,p,st,rv]=await Promise.all([
  sb.from('categories').select('*').order('sort').order('name'),
  fetchAll(()=>sb.from('products').select('*,categories(name)').order('sku').order('id')),
  sb.from('settings').select('*').eq('id',1).maybeSingle(),
  sb.from('reviews').select('*').order('created_at')]);
 if(c.error)throw c.error;
 S.cats=c.data.map(x=>({id:x.id,n:x.name,i:x.icon||iconFor(x.name)}));
 S.prods=p.map(mapP);
 const t=st.data||{};S.about=t.about||'';S.wa=t.whatsapp||'';S.email=t.email||'';S.links=(t.links||[]).filter(l=>l&&l.k!='mail');S.car=t.carousel||[];
 S.revs=(rv.data||[]).map(x=>({id:x.id,n:x.name,t:x.body,s:x.stars}));
 S.cart=S.cart.filter(c=>S.prods.some(p=>p.id==c.id));
 loadErr=false;
}
async function loadAdmin(){
 const {data,error}=await sb.from('orders').select('*,order_items(*)').order('created_at',{ascending:false}).limit(500);
 if(error)throw error;
 S.orders=data.reverse().map(o=>({id:o.number,uid:o.id,d:o.created_at,nm:o.customer_name,tel:o.phone,dir:o.address,t:+o.total,st:o.status,it:(o.order_items||[]).map(i=>({c:i.sku,n:i.name,v:i.variant,q:i.qty,p:+i.unit_price}))}));
}
async function checkAdmin(){try{const {data:{session}}=await sb.auth.getSession();if(!session){authed=false;return}const {data}=await sb.from('admins').select('user_id').eq('user_id',session.user.id).maybeSingle();authed=!!data;if(authed)await loadAdmin()}catch(e){authed=false}}
async function setSet(p){const {error}=await sb.from('settings').update(p).eq('id',1);if(error)throw error;if(p.links)S.links=p.links;if(p.carousel)S.car=p.carousel}
const shrink=(f,mx,qa)=>new Promise(ok=>{const r=new FileReader();r.onload=()=>{const im=new Image();im.onload=()=>{const k=Math.min(1,mx/Math.max(im.width,im.height)),c=document.createElement('canvas');c.width=Math.round(im.width*k);c.height=Math.round(im.height*k);c.getContext('2d').drawImage(im,0,0,c.width,c.height);c.toBlob(b=>ok(b),'image/jpeg',qa)};im.onerror=()=>ok(null);im.src=r.result};r.onerror=()=>ok(null);r.readAsDataURL(f)});
async function upImg(blob,folder){const path=`${folder}/${crypto.randomUUID()}.jpg`;const {error}=await sb.storage.from('product-images').upload(path,blob,{contentType:'image/jpeg',cacheControl:'31536000'});if(error)throw error;return sb.storage.from('product-images').getPublicUrl(path).data.publicUrl}
function locP(){try{if(localStorage.getItem('wive_v2_migrated'))return[];const o=JSON.parse(localStorage.getItem('wive_v2'));if(!o||!Array.isArray(o.prods))return[];const have=new Set(S.prods.map(p=>p.code));return o.prods.filter(p=>p&&p.n&&p.p>0&&!have.has(String(p.code||'').toUpperCase()))}catch(e){return[]}}
const locBanner=()=>{const L=locP();return L.length?`<div class="sec"><h3>Datos locales detectados</h3><p class="mut">Este navegador tiene ${L.length} producto(s) guardado(s) antes de la migraciÃ³n que no estÃ¡n en la base de datos.</p><button class="btn w" data-act="migloc">Migrar ${L.length} producto(s)</button></div>`:''};
'''
rx(r"const LS='wive_v2';.*?(?=const NET=)", INIT)

# ---------- 3. WhatsApp con ventana pre-abierta ----------
rep(r'''const wa=t=>{const o=$('#wo');o.classList.add('on');setTimeout(()=>o.classList.remove('on'),1600);window.open(`https://wa.me/${S.wa}?text=${encodeURIComponent(t)}`,'_blank')};''',
r'''const wa=(t,w)=>{const o=$('#wo');o.classList.add('on');setTimeout(()=>o.classList.remove('on'),1600);const u=`https://wa.me/${S.wa}?text=${encodeURIComponent(t)}`;if(w&&!w.closed){try{w.location.href=u;return}catch(e){}}window.open(u,'_blank')};''')

# ---------- 4. Excel: vista previa, validacion, duplicados, lotes ----------
XLS = r'''function xlsHTML(){return `<h2>Cargar con Excel</h2><div class="sec"><h3>1. DescargÃ¡ la plantilla</h3><p class="mut">Columnas: ${COLS.join(', ')}. SeparÃ¡ colores y talles con coma. "Destacado": SÃ­ o No. "Descuento %": 0 a 99.</p><button class="btn" data-act="xtpl">Descargar plantilla</button></div><div class="sec"><h3>2. SubÃ­ tu archivo</h3><p class="mut">Acepta .xlsx, .xls y .csv (hasta 20.000 filas). VerÃ¡s una vista previa antes de guardar. Si el cÃ³digo (SKU) ya existe se actualiza ese producto; si no, se crea. Si dejÃ¡s el cÃ³digo vacÃ­o se genera uno nuevo. Las fotos se agregan despuÃ©s desde Productos.</p><input type="file" id="xf" accept=".xlsx,.xls,.csv"><div id="xr" class="mut" style="margin-top:10px"></div></div><div class="sec"><h3>Exportar productos actuales</h3><button class="btn" data-act="xexp">Descargar Excel</button></div>`}
const NUMP=v=>{let t=String(v==null?'':v).trim();if(/[.,]\d{1,2}$/.test(t))t=t.replace(/[.,]\d{1,2}$/,'');t=t.replace(/\D/g,'');return t?parseInt(t,10):NaN};
async function xlsImport(file){const r=$('#xr');XP=null;r.textContent='Leyendo archivoâ¦';
 try{await XL();const wb=XLSX.read(await file.arrayBuffer(),{type:'array'}),rows=XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]],{defval:'',raw:false});
  if(!rows.length){r.textContent='El archivo estÃ¡ vacÃ­o.';return}
  if(rows.length>20000){r.textContent='El archivo supera 20.000 filas. Dividilo en partes.';return}
  const K={codigo:'code',sku:'code',nombre:'n',producto:'n',categoria:'c',precio:'p','descuento %':'dp',descuento:'dp',descripcion:'d',colores:'col',talles:'sz',destacado:'f'};
  const L=t=>String(t||'').split(/[,;]/).map(u=>u.trim()).filter(Boolean);
  const have=new Set(S.prods.map(p=>p.code)),seen=new Set();let nx=S.prods.reduce((a,q)=>Math.max(a,+(/^SK(\d+)$/.exec(q.code||'')||[0,0])[1]),0);
  const items=rows.map((raw,ix)=>{const x={};for(const k in raw){const mk=K[norm(k)];if(mk)x[mk]=raw[k]}
   const er=[],n=String(x.n||'').trim(),p=NUMP(x.p);
   if(!n)er.push('falta el nombre');else if(n.length>200)er.push('nombre de mÃ¡s de 200 caracteres');
   if(!(p>0))er.push('precio invÃ¡lido');
   let dp=0;if(String(x.dp==null?'':x.dp).trim()!==''){dp=parseFloat(String(x.dp).replace('%','').replace(',','.'));if(!(dp>=0&&dp<100))er.push('descuento invÃ¡lido (0 a 99)')}
   const code=String(x.code||'').trim().toUpperCase();if(code.length>40)er.push('cÃ³digo de mÃ¡s de 40 caracteres');
   const cat=String(x.c||'').trim()||(S.cats[0]||{}).n||'General';if(cat.length>80)er.push('categorÃ­a de mÃ¡s de 80 caracteres');
   let st='Nuevo';
   if(code){if(seen.has(code))er.push('cÃ³digo repetido en el archivo (se omite)');seen.add(code);if(have.has(code))st='Actualiza'}
   if(er.length)st='Error';
   const row=er.length?null:{sku:code,name:n,description:String(x.d||'').trim(),price:p,old_price:dp>0?Math.round(p/(1-dp/100)):null,category:cat,icon:iconFor(n+' '+cat),cat_icon:iconFor(cat),colors:L(x.col),sizes:L(x.sz),featured:/^(si|s|1|true|x|yes)$/i.test(norm(x.f))};
   return{ix:ix+2,st,msg:er.join('; '),code,n,p,row}});
  items.forEach(it=>{if(it.st=='Nuevo'&&!it.code){do{nx++;it.code='SK'+String(nx).padStart(3,'0')}while(seen.has(it.code)||have.has(it.code));seen.add(it.code);it.row.sku=it.code}});
  XP=items;const bad=items.filter(i=>i.st=='Error'),ok=items.length-bad.length,nw=items.filter(i=>i.st=='Nuevo').length,up=ok-nw;
  const show=bad.slice(0,60).concat(items.filter(i=>i.st!='Error').slice(0,100-Math.min(60,bad.length)));
  r.innerHTML=`<b>Vista previa:</b> ${items.length} filas Â· <span style="color:#6fd08c">${nw} nuevos</span> Â· <span style="color:#ffb347">${up} a actualizar</span> Â· <span style="color:#ff8a8a">${bad.length} con error (se omiten)</span><div style="overflow:auto;margin:10px 0;max-height:320px"><table class="xt"><tr><th>Fila</th><th>Estado</th><th>CÃ³digo</th><th>Nombre</th><th>Precio</th><th>Detalle</th></tr>${show.map(i=>`<tr><td>${i.ix}</td><td>${i.st}</td><td>${esc(i.code)}</td><td>${esc(i.n.slice(0,40))}</td><td>${isNaN(i.p)?'â':gs(i.p)}</td><td class="m">${esc(i.msg)}</td></tr>`).join('')}</table></div>${items.length>show.length?`<p class="mut">Mostrando ${show.length} de ${items.length} filas.</p>`:''}${ok?`<button class="btn w" data-act="xgo">Confirmar importaciÃ³n (${ok})</button><br><br>`:''}<button class="chip" data-act="xcancel">Cancelar</button>`
 }catch(e){r.textContent='Error: '+e.message}}
'''
rx(r"function xlsHTML\(\)\{.*?(?=document\.addEventListener\('change',e=>\{const t=e\.target;if\(t\.id=='xf')", XLS)
rx(r"document\.addEventListener\('change',e=>\{const t=e\.target;if\(t\.id=='xf'[^\n]*",
r'''document.addEventListener('change',e=>{const t=e.target;if(t.id=='xf'&&t.files[0])xlsImport(t.files[0]);else if(t.dataset&&t.dataset.ost){const o=S.orders.find(x=>x.id==t.dataset.ost);if(o){const prev=o.st,v=t.value;sb.from('orders').update({status:v}).eq('id',o.uid).then(({error})=>{if(error){alert('No se pudo actualizar el estado: '+error.message);t.value=prev}else o.st=v})}}});''')

# ---------- 5. grilla con "ver mÃ¡s" y listado admin acotado ----------
rep(r'''g.innerHTML=l.length?l.map(card).join(''):''',
    r'''g.innerHTML=l.length?l.slice(0,lim).map(card).join('')+(l.length>lim?`<div style="grid-column:1/-1;text-align:center"><button class="chip" data-act="more">Ver mÃ¡s (${l.length-lim})</button></div>`:''):''')
rep("if(e.target.id=='q'){q=e.target.value;", "if(e.target.id=='q'){q=e.target.value;lim=60;")
rep("else if(a=='cat'){cat=d.c;", "else if(a=='cat'){cat=d.c;lim=60;")
rep('''<button class="x" data-act="delp" data-k="${k}">${ic('trash')}</button></div>`).join('')}}''',
    '''<button class="x" data-act="delp" data-id="${p.id}">${ic('trash')}</button></div>`).join('')+(S.prods.length>100?`<p class="mut">Mostrando 100 de ${S.prods.length}. EditÃ¡ o exportÃ¡ el resto con Excel.</p>`:'')}}''')
rep('S.prods.map((p,k)=>`<div class="li"><div class="t">${pic(p,24)}', 'S.prods.slice(0,100).map((p,k)=>`<div class="li"><div class="t">${pic(p,24)}')
rep("h+=`<h2>${ed?'Editar producto':'Nuevo producto'}</h2>", "h+=locBanner()+`<h2>${ed?'Editar producto':'Nuevo producto'}</h2>")
rep('h=`<div class="c"><div class="hero">', 'h=`<div class="c">${loadErr?\'<p class="mut">No se pudo cargar el catÃ¡logo. ReintentÃ¡ en unos minutos.</p>\':\'\'}<div class="hero">')

# ---------- 6. login real (Supabase Auth) + recuperacion ----------
LOGIN = r'''else if(v=='recuperar'){h=`<div style="max-width:380px;margin:30px auto"><h1 style="font-size:24px;text-align:center">Nueva contraseÃ±a</h1><div class="sec"><label class="fl">Nueva contraseÃ±a (mÃ­n. 10 caracteres)<input id="np1" type="password" autocomplete="new-password"></label><label class="fl">Repetir contraseÃ±a<input id="np2" type="password" autocomplete="new-password"></label><p id="le" style="color:var(--or);min-height:22px;margin:0 0 8px"></p><button class="btn w" data-act="setpw">Guardar contraseÃ±a</button></div></div>`}
 else if((v=='admin'||v=='panel')&&!authed){h=`<div style="max-width:380px;margin:30px auto"><h1 style="font-size:24px;text-align:center">Acceso al panel</h1><div class="sec"><label class="fl">Correo<input id="lu2" type="email" autocomplete="username" autocapitalize="none" inputmode="email"></label><label class="fl">ContraseÃ±a<input id="lp2" type="password" autocomplete="current-password"></label><p id="le" style="color:var(--or);min-height:22px;margin:0 0 8px"></p><button class="btn w" data-act="login">Entrar</button><br><br><button class="chip" style="width:100%" data-act="forgot">OlvidÃ© mi contraseÃ±a</button></div></div>`}'''
rx(r"else if\(\(v=='admin'\|\|v=='panel'\)&&!authed\)\{h=`.*?Entrar</button></div></div>`\}", LOGIN)

# ---------- 7. handlers de clic ----------
rep("else if(a=='open'){sel=+d.id;", "else if(a=='open'){sel=d.id;")
rep("S.cart.push({id:+d.id,col,sz,q:1});save();refreshBadge();", "S.cart.push({id:d.id,col,sz,q:1});ordKey=null;save();refreshBadge();")
rep("el.dataset.gone=1;S.cart.splice(+d.k,1);save();refreshBadge();", "el.dataset.gone=1;S.cart.splice(+d.k,1);ordKey=null;save();refreshBadge();")
rep("else if(a=='edp'){ed=+d.id;", "else if(a=='edp'){ed=d.id;")
rep("else if(a=='tab'){tab=d.t;ed=null;render()}", "else if(a=='tab'){run(async()=>{tab=d.t;ed=null;if(tab=='ords')await loadAdmin();render()})}\n else if(a=='more'){lim+=60;grid()}\n else if(a=='xcancel'){XP=null;const r=$('#xr');if(r)r.innerHTML='';const f=$('#xf');if(f)f.value=''}")

SEND = r'''else if(a=='send'){if(sending)return;if(!g('#nm')||!g('#tel')||!g('#dir')){alert('CompletÃ¡ nombre, telÃ©fono y direcciÃ³n.');return}
  if(!S.cart.length)return;
  sending=true;t.disabled=true;const w=window.open('about:blank','_blank');
  const nm=g('#nm'),tel=g('#tel'),dir=g('#dir'),cart=S.cart.slice();ordKey=ordKey||crypto.randomUUID();
  run(async()=>{try{
   const {data,error}=await sb.rpc('create_order',{p_key:ordKey,p_name:nm,p_phone:tel,p_address:dir,p_items:cart.map(c=>({product_id:c.id,qty:c.q,variant:[c.col,c.sz].filter(Boolean).join(', ')}))});
   if(error)throw error;const o=Array.isArray(data)?data[0]:data;if(!o||!o.order_number)throw new Error('respuesta invÃ¡lida del servidor');
   const L=cart.map(c=>{const p=S.prods.find(p=>p.id==c.id);return p?`â¢ [${p.code||''}] ${p.n}${[c.col,c.sz].filter(Boolean).length?' ('+[c.col,c.sz].filter(Boolean).join(', ')+')':''} x${c.q} â ${gs(p.p*c.q)}`:''}).filter(Boolean);
   S.cart=[];ordKey=null;save();refreshBadge();
   wa(`Hola WIVE, quiero confirmar mi pedido N.Âº ${o.order_number}:\n${L.join('\n')}\nTotal: ${gs(o.total)}\n\nNombre: ${nm}\nTel: ${tel}\nDirecciÃ³n: ${dir}`,w);
   render();
  }catch(e){if(w)try{w.close()}catch(_){}alert('No se pudo registrar el pedido, por eso no se abriÃ³ WhatsApp.\n'+((e&&e.message)||e))}finally{sending=false;if(t&&t.isConnected)t.disabled=false}})}'''
rx(r"else if\(a=='send'\)\{.*?(?=\s*else if\(a=='ordx'\))", SEND)


def line(name, new):
    rx(r"else if\(a=='%s'\)\{[^\n]*(?=\n)" % name, new)


line('ordx', r'''else if(a=='ordx'){run(async()=>{const o=S.orders.find(x=>x.id==d.k);if(!o||!confirm('Â¿Eliminar este pedido del historial?'))return;const {error}=await sb.from('orders').delete().eq('id',o.uid);if(error)throw error;await loadAdmin();render()})}''')
line('saveweb', r'''else if(a=='saveweb'){run(async()=>{const wn=($('#wn').value||'').replace(/\D/g,'');if(!wn){alert('IngresÃ¡ un nÃºmero de WhatsApp vÃ¡lido.');return}const {error}=await sb.from('settings').update({about:$('#ab').value.trim(),whatsapp:wn,email:($('#em').value||'').trim()}).eq('id',1);if(error)throw error;await loadPublic();alert('Guardado')})}''')
line('mkl', r'''else if(a=='mkl'){const u=g('#lu');if(!u)return;run(async()=>{await setSet({links:S.links.concat([{k:$('#ln').value,u}])});render()})}''')
line('dell', r'''else if(a=='dell'){run(async()=>{await setSet({links:S.links.filter((_,i)=>i!=+d.k)});render()})}''')
line('rset', r'''else if(a=='rset'){const r=S.revs[+d.k];if(r)run(async()=>{const {error}=await sb.from('reviews').update({stars:+d.n}).eq('id',r.id);if(error)throw error;r.s=+d.n;t.parentNode.querySelectorAll('.stb').forEach((b,i)=>b.classList.toggle('on',i<r.s))})}''')
line('rmc', r'''else if(a=='rmc'){run(async()=>{await setSet({carousel:S.car.filter((_,i)=>i!=+d.k)});const v=$('#cpv');if(v)v.innerHTML=carThumbs()})}''')
line('mkr', r'''else if(a=='mkr'){const n=g('#rn'),tx=g('#rt');if(!n||!tx)return;run(async()=>{const {error}=await sb.from('reviews').insert({name:n,body:tx,stars:rs});if(error)throw error;rs=5;await loadPublic();render()})}''')
line('delr', r'''else if(a=='delr'){run(async()=>{const r=S.revs[+d.k];if(!r)return;const {error}=await sb.from('reviews').delete().eq('id',r.id);if(error)throw error;await loadPublic();render()})}''')
line('mkc', r'''else if(a=='mkc'){const n=g('#nc');if(!n||S.cats.some(c=>c.n.toLowerCase()==n.toLowerCase()))return;run(async()=>{const {error}=await sb.from('categories').insert({name:n,icon:iconFor(n),sort:S.cats.length});if(error)throw error;await loadPublic();render()})}''')
line('delc', r'''else if(a=='delc'){const c=S.cats[+d.k];if(!c||!confirm('Â¿Eliminar la categorÃ­a "'+c.n+'"? Sus productos quedarÃ¡n sin categorÃ­a.'))return;run(async()=>{const {error}=await sb.from('categories').delete().eq('id',c.id);if(error)throw error;await loadPublic();render()})}''')
line('delp', r'''else if(a=='delp'){const p=S.prods.find(x=>x.id==d.id);if(!p||!confirm('Â¿Eliminar "'+p.n+'"? Los pedidos anteriores conservan su detalle.'))return;run(async()=>{const {error}=await sb.from('products').delete().eq('id',p.id);if(error)throw error;await loadPublic();render()})}''')
line('login', r'''else if(a=='login'){const em=(g('#lu2')||'').toLowerCase(),pw=$('#lp2').value,msg=$('#le');if(!em||!pw){msg.textContent='IngresÃ¡ correo y contraseÃ±a.';return}t.disabled=true;run(async()=>{try{const {error}=await sb.auth.signInWithPassword({email:em,password:pw});if(!error)await checkAdmin();if(error||!authed){if(!error)await sb.auth.signOut();msg.textContent=error?'Correo o contraseÃ±a incorrectos.':'Esta cuenta no tiene permisos de administrador.';const s2=msg.closest('.sec');s2.classList.remove('shake');s2.offsetWidth;s2.classList.add('shake');return}await loadPublic();render()}finally{t.disabled=false}})}''')
line('logout', r'''else if(a=='logout'){run(async()=>{await sb.auth.signOut();authed=false;S.orders=[];await loadPublic();homeDirty=true;go('')})}
 else if(a=='forgot'){const em=(g('#lu2')||'').toLowerCase(),msg=$('#le');if(!em){msg.textContent='EscribÃ­ tu correo arriba y tocÃ¡ de nuevo.';return}run(async()=>{await sb.auth.resetPasswordForEmail(em,{redirectTo:location.origin+'/'});msg.textContent='Si el correo es de un administrador, recibirÃ¡s un enlace para restablecer la contraseÃ±a.'})}
 else if(a=='setpw'){const p1=$('#np1').value,p2=$('#np2').value,msg=$('#le');if(p1.length<10){msg.textContent='UsÃ¡ al menos 10 caracteres.';return}if(p1!=p2){msg.textContent='Las contraseÃ±as no coinciden.';return}run(async()=>{const {error}=await sb.auth.updateUser({password:p1});if(error){msg.textContent='No se pudo cambiar: '+error.message;return}await checkAdmin();await loadPublic();alert('ContraseÃ±a actualizada');go('admin')})}
 else if(a=='xgo'){if(!XP)return;t.disabled=true;run(async()=>{const rows=XP.filter(i=>i.row).map(i=>i.row),r=$('#xr'),CH=500;let c=0,u=0;
  for(let k=0;k<rows.length;k+=CH){r.innerHTML='Importandoâ¦ '+Math.min(k+CH,rows.length)+' / '+rows.length;const {data,error}=await sb.rpc('admin_import_products',{p_rows:rows.slice(k,k+CH)});if(error){r.innerHTML='<b style="color:#ff8a8a">Error en el lote '+(k/CH+1)+': '+esc(error.message)+'</b><br>Se guardaron '+(c+u)+' productos antes del error. PodÃ©s volver a subir el archivo: los cÃ³digos existentes se actualizan sin duplicar.';return}c+=data.created;u+=data.updated}
  const bad=XP.filter(i=>!i.row);XP=null;await loadPublic();homeDirty=true;
  r.innerHTML='<b style="color:#6fd08c">Listo:</b> '+c+' nuevos, '+u+' actualizados, '+bad.length+' omitidos por error.'+(bad.length?'<br>'+bad.slice(0,15).map(i=>'Fila '+i.ix+': '+esc(i.msg)).join('<br>'):'')})}
 else if(a=='migloc'){run(async()=>{const L=locP();if(!L.length)return;t.disabled=true;
  const rows=L.map((p,k)=>({sku:String(p.code||'').toUpperCase()||'LOC'+String(k+1).padStart(3,'0'),name:p.n,description:p.d||'',price:p.p,old_price:p.o&&p.o>p.p?p.o:null,category:p.c||'General',icon:p.i||iconFor(p.n),cat_icon:iconFor(p.c||''),colors:p.col||[],sizes:p.sz||[],featured:!!p.f}));
  const {error}=await sb.rpc('admin_import_products',{p_rows:rows});if(error)throw error;await loadPublic();
  for(let k=0;k<L.length;k++){const p=L[k],im=(p.imgs&&p.imgs.length?p.imgs:(p.img?[p.img]:[])).filter(u=>/^data:image\//.test(u)),pr=S.prods.find(x=>x.code==rows[k].sku);if(!im.length||!pr)continue;const urls=[];for(const u of im.slice(0,6))urls.push(await upImg(await (await fetch(u)).blob(),'products'));await sb.from('products').update({images:urls}).eq('id',pr.id)}
  try{localStorage.setItem('wive_v2_migrated','1')}catch(e){}await loadPublic();render();alert('MigraciÃ³n completada')})}''')

rx(r"else if\(a=='mkp'\)\{.*?ed=null;img=null;save\(\);render\(\)\}", r'''else if(a=='mkp'){const n=g('#pn'),p=NUMP(g('#pp')||''),code=(g('#pcod')||'').toUpperCase();if(!n||!(p>0)){alert('CompletÃ¡ nombre y precio.');return}if(!code){alert('CompletÃ¡ el cÃ³digo.');return}
  const c=$('#pc').value,dp=parseInt((g('#pdesc')||'').replace(/\D/g,''))||0,o=dp>0&&dp<100?Math.round(p/(1-dp/100)):0,L=s=>(g(s)||'').split(',').map(x=>x.trim()).filter(Boolean);
  if(S.prods.some(x=>x.code==code&&x.id!=ed)){alert('Ese cÃ³digo ya existe.');return}
  const row={sku:code,name:n,description:g('#pds')||'',price:p,old_price:o>p?o:null,category_id:(S.cats.find(x=>x.n==c)||{}).id||null,colors:L('#pcl'),sizes:L('#psz'),featured:$('#pd').checked,icon:iconFor(n+' '+c),images:IM.slice()};
  t.disabled=true;run(async()=>{try{const q=ed?sb.from('products').update(row).eq('id',ed):sb.from('products').insert(row);const {error}=await q;if(error)throw error;ed=null;img=null;await loadPublic();render()}finally{t.disabled=false}})}''')

# ---------- 8. subida de imagenes a Storage ----------
UPL = r'''const shrinkNote=b=>{if(b)b.insertAdjacentHTML('beforeend','<span class="mut" id="upl">Subiendoâ¦</span>')};
document.addEventListener('change',async e=>{const id=e.target.id;if(id!='pf'&&id!='cf')return;const fs=[...e.target.files].slice(0,id=='pf'?6:12);e.target.value='';const box=$(id=='pf'?'#pv':'#cpv');
 try{
  if(id=='pf'){for(const f of fs){if(IM.length>=6)break;shrinkNote(box);const b=await shrink(f,900,.82);if(b)IM.push(await upImg(b,'products'));box.innerHTML=thumbsHTML()}}
  else{const L=S.car.slice();for(const f of fs){if(L.length>=12)break;shrinkNote(box);const b=await shrink(f,800,.8);if(b)L.push(await upImg(b,'carousel'))}await setSet({carousel:L});box.innerHTML=carThumbs()}
 }catch(err){const u=$('#upl');if(u)u.remove();alert('No se pudo subir la imagen: '+((err&&err.message)||err))}});
'''
rx(r"document\.addEventListener\('change',async e=>\{if\(e\.target\.id!='pf'\).*?(?=function swipeBack0\(\)\{)", UPL)

# ---------- 9. arranque ----------
rep("\nrender();\n</script></body></html>", r'''
sb.auth.onAuthStateChange(ev=>{if(ev=='PASSWORD_RECOVERY')setTimeout(()=>go('recuperar'),0)});
(async()=>{
 m.innerHTML='<p class="mut" style="text-align:center;margin:80px 0">Cargandoâ¦</p>';
 await checkAdmin();
 try{await loadPublic()}catch(e){loadErr=true}
 render();
})();
</script></body></html>''')

# ---------- 10. textos legales: reflejar el almacenamiento real ----------
rep("Los mensajes por WhatsApp son procesados por WhatsApp segÃºn su propia polÃ­tica de privacidad.",
    "Los datos de tus pedidos se almacenan en servidores de Supabase (regiÃ³n SÃ£o Paulo, Brasil) y el sitio se aloja en Vercel. Los mensajes por WhatsApp son procesados por WhatsApp segÃºn su propia polÃ­tica de privacidad.")
rep("El sitio guarda tu carrito en el almacenamiento local de tu navegador.", "El sitio guarda tu carrito en el almacenamiento local de tu navegador. Al hacer un pedido, tu nombre, telÃ©fono, direcciÃ³n y productos se registran en nuestra base de datos.")

# ---------- salida ----------
out = ROOT / 'public'
out.mkdir(exist_ok=True)
(out / 'index.html').write_text(s, encoding='utf-8')
print('OK public/index.html', len(s), 'bytes')
