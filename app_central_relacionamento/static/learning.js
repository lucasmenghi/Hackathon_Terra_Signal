'use strict';
window.Learning=(()=>{
 const key='terra-signal-learning-inference-v1';
 const missions=[
  {id:'profile',title:'Conheça um cliente',description:'Abra um perfil pelo ranking ou pela busca para encontrar os dados e o score.',target:'queue-panel'},
  {id:'decile',title:'Encontre uma faixa de risco',description:'Aplique um decil. D1 concentra os maiores scores; D10, os menores.',target:'risk-filter'},
  {id:'prediction',title:'Explore a previsão de churn',description:'Filtre Sim (1) ou Não (0). Essa é a previsão do modelo, não um cancelamento confirmado.',target:'prediction-filter'},
  {id:'feedback',title:'Abra a leitura do comentário',description:'No perfil, abra a interpretação e confira o relato antes de orientar a abordagem.',target:'feedback-details'},
  {id:'quiz',title:'Conclua seu primeiro percurso',description:'Responda uma pergunta rápida sobre a interpretação do risco.',target:'knowledge-check'}
 ];
 let completed=new Set(),dismissed=false,persistent=true,toastTimer=null;
 const $=id=>document.getElementById(id);
 try{const saved=JSON.parse(localStorage.getItem(key)||'{}');if(Array.isArray(saved.completed))completed=new Set(saved.completed.filter(id=>missions.some(m=>m.id===id)));dismissed=saved.dismissed===true}catch(e){persistent=false}
 function save(){try{localStorage.setItem(key,JSON.stringify({completed:[...completed],dismissed}))}catch(e){persistent=false}if(!persistent)$('storage-note').textContent='Seu navegador não está salvando o progresso. A jornada funciona nesta sessão.'}
 function toast(message){$('learning-toast').textContent=message;$('learning-toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('learning-toast').hidden=true,3800)}
 function render(){const count=completed.size,next=missions.find(m=>!completed.has(m.id));$('journey-badge').textContent=`${count}/5`;$('journey-progress').value=count;$('learning-strip').hidden=dismissed;
  $('journey-title').textContent=count===5?'Primeiro percurso concluído.':count?'Você já conhece melhor sua central.':'Seu primeiro passo faz diferença.';
  $('journey-description').textContent=count===5?'Continue explorando a carteira com contexto.':`${count} de 5 missões concluídas. Próxima: ${next.title.toLowerCase()}.`;
  $('learning-continue').textContent=count===5?'Ver conquistas ✓':count?'Continuar jornada →':'Começar jornada →';
  $('mission-list').innerHTML=missions.map((m,i)=>`<div class="mission ${completed.has(m.id)?'completed':''}"><span class="mission-number" aria-hidden="true">${completed.has(m.id)?'✓':i+1}</span><div><h3>${m.title}</h3><p>${m.description}</p></div><button class="text-button" data-guide="${m.id}">${completed.has(m.id)?'Revisitar':'Explorar'} ↗</button></div>`).join('');
 }
 function mark(id){if(completed.has(id)||!missions.some(m=>m.id===id))return;completed.add(id);save();render();toast(completed.size===5?'Jornada concluída! Você explorou os recursos principais.':`Missão concluída: ${missions.find(m=>m.id===id).title} (${completed.size}/5)`)}
 function show(){render();$('learning-dialog').showModal()}
 function guide(id){const mission=missions.find(m=>m.id===id);if(!mission)return;
  if(id==='quiz'){$('knowledge-check').hidden=false;$('knowledge-check').scrollIntoView({block:'nearest',behavior:'smooth'});return}
  $('learning-dialog').close();const target=$(mission.target);
  if(id==='feedback'&&!target){toast('Abra primeiro um perfil no ranking. Depois, expanda a leitura do comentário.');$('queue-panel').scrollIntoView({behavior:'smooth',block:'start'});return}
  if(target){document.querySelectorAll('.tutorial-target').forEach(el=>el.classList.remove('tutorial-target'));target.classList.add('tutorial-target');target.scrollIntoView({behavior:'smooth',block:'center'});if(target.tagName==='SELECT')target.focus();if(id==='feedback')target.open=true;setTimeout(()=>target.classList.remove('tutorial-target'),6000)}
  toast(id==='profile'?'Clique na seta ao lado de um cliente para abrir o perfil.':id==='decile'?'Escolha um decil para completar a missão.':id==='prediction'?'Selecione Sim (1) ou Não (0) no filtro de previsão.':'Abra e confira a interpretação do comentário.');
 }
 function init(){render();save();$('learning-open').addEventListener('click',show);$('learning-continue').addEventListener('click',show);$('learning-close').addEventListener('click',()=>$('learning-dialog').close());$('learning-dismiss').addEventListener('click',()=>{dismissed=true;save();render()});
  $('mission-list').addEventListener('click',e=>{const b=e.target.closest('[data-guide]');if(b)guide(b.dataset.guide)});
  document.querySelectorAll('[data-answer]').forEach(b=>b.addEventListener('click',()=>{if(b.dataset.answer==='correct'){$('quiz-feedback').textContent='Isso! D1 indica os maiores scores da base. A previsão não confirma cancelamento.';mark('quiz')}else $('quiz-feedback').textContent='Tente novamente: o decil ordena o risco estimado. Ele não confirma o status atual do cliente.'}));
  $('learning-reset').addEventListener('click',()=>{completed.clear();dismissed=false;$('knowledge-check').hidden=true;$('quiz-feedback').textContent='';save();render();toast('Sua jornada foi reiniciada. Nenhum dado de cliente foi alterado.')});
 }
 return {init,mark,show};
})();
