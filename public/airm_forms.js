
function airmHandleForm(form, endpoint){
  if(!form) return;
  form.addEventListener('submit', async function(ev){
    ev.preventDefault();
    const fd = new FormData(form);
    const data = {}; fd.forEach((v,k)=>data[k]=v);
    const btn = form.querySelector('button[type="submit"]');
    const msg = form.querySelector('.airm-msg');
    if(btn){ btn.disabled = true; btn.textContent = 'Küldés...'; }
    if(msg){ msg.textContent=''; msg.className='airm-msg muted small'; }
    try{
      const res = await fetch((window.BACKEND_ORIGIN||"")+endpoint, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)});
      const j = await res.json();
      if(j && j.ok){
        if(msg){ msg.textContent = j.message || 'Sikeres küldés.'; msg.className='airm-msg ok'; }
        form.reset();
      }else{ throw new Error((j && j.message) || 'Ismeretlen hiba'); }
    }catch(e){
      if(msg){ msg.textContent = e.message || 'Hiba történt. Próbálja meg később.'; msg.className='airm-msg bad'; }
    }finally{
      if(btn){ btn.disabled = false; btn.textContent = btn.getAttribute('data-label') || 'Küldés'; }
    }
  });
}
document.addEventListener('DOMContentLoaded', function(){
  airmHandleForm(document.getElementById('airmRegisterForm'), '/api/register');
  airmHandleForm(document.getElementById('airmContactForm'), '/api/contact');
});