'use strict';
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={POSITIVO:'Positivo',NEGATIVO:'Negativo',MISTO:'Misto',NEUTRO:'Neutro',INDETERMINADO:'Indeterminado',
 CANCELAMENTO_RELATADO:'Cancelamento relatado',TROCA_RELATADA:'Troca relatada',DECISAO_SAIDA:'Decisão de sair',
 CONSIDERA_SAIDA:'Considera sair',INTENCAO_PERMANENCIA:'Intenção de permanecer',SEM_DECLARACAO:'Sem declaração de saída ou permanência',AMBIGUO:'Relato ambíguo',
 PRECO:'Preço',CONEXAO:'Conexão',SUPORTE:'Suporte',COBRANCA:'Cobrança',CONCORRENCIA:'Concorrência',PRODUTOS:'Produtos',OUTROS:'Outros',
 PRECO_CONCORRENCIA:'Preço e concorrência',PAGAMENTO:'Pagamento',TECNICO:'Técnico',PESSOAL:'Pessoal',PRODUTO_COBERTURA:'Produto e cobertura',ATENDIMENTO:'Atendimento',
 'Month-to-month':'Mensal','One year':'Um ano','Two year':'Dois anos','Fiber optic':'Fibra óptica',DSL:'DSL',No:'Sem internet',
 'Electronic check':'Cheque eletrônico','Mailed check':'Cheque pelo correio','Bank transfer (automatic)':'Débito automático','Credit card (automatic)':'Cartão de crédito automático'};
const routes={CONFERIR_STATUS_CADASTRAL:'Conferir o status cadastral antes de definir a abordagem.',AVALIAR_RETENCAO_IMEDIATA:'Avaliar a retenção imediata e confirmar a situação com o cliente.',INVESTIGAR_MOTIVO_DE_SAIDA:'Investigar o motivo de saída com o cliente.',ESCLARECER_RELATO:'Esclarecer o relato com o cliente.',CONFIRMAR_CONTEXTO_NO_ATENDIMENTO:'Confirmar se o contexto relatado ainda se aplica.'};
let mode='central',base='inference',portfolio='all',selected=null,offset=0,total=0,viewVersion=0,queueVersion=0,detailVersion=0,searchTimer=null;
const pageSize=8;
const scoreText=score=>score.probability===null||score.probability===undefined?'Indisponivel':`${(score.probability*100).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}%`;
const predicted=value=>value==='1'?'Sim (1)':value==='0'?'Não (0)':'Não disponível';
const sentimentClass=s=>s==='NEGATIVO'?'status-negative':s==='POSITIVO'?'status-positive':s==='MISTO'?'status-mixed':'';
const translate=v=>labels[v]||v||'Não informado';
async function api(path){const response=await fetch(path,{headers:{Accept:'application/json'}});if(!response.ok)throw Error(response.status===404?'Cliente não encontrado para este atendimento.':`Não foi possível concluir a consulta (${response.status}). Tente novamente.`);return response.json()}
function emptyProfile(title='O próximo atendimento começa aqui.',description='Digite o ID do cliente para conhecer seu contexto antes da conversa.'){return `<div class="empty-profile"><div class="empty-symbol" aria-hidden="true">◎</div><h3>${esc(title)}</h3><p>${esc(description)}</p></div>`}
function clearProfile(){selected=null;++detailVersion;$('customer-id').value='';$('customer-error').textContent='';$('profile').innerHTML=emptyProfile('Escolha o próximo cliente.','Abra um contato no ranking ou busque pelo ID para preparar a conversa.');highlight()}
function highlight(){document.querySelectorAll('#queue tr[data-customer]').forEach(row=>row.classList.toggle('selected',row.dataset.customer===selected?.id))}
function tag(label,value){return `<span class="tag ${value===true?'owned':''}">${esc(label)} ${value===true?'✓':value===false?'—':'?'}</span>`}
function renderProfile(c){const n=c.nlp,probability=c.score.probability;const sentiments=n.status==='ERRO_API'||n.status==='RESPOSTA_NULA'?null:n.sentiment;
 const review=n.imported&&n.status!=='DISPONIVEL';const owned=c.products;
 const goodEvidence=n.evidence&&c.feedback.includes(n.evidence);
 const nextStep=n.status==='DISPONIVEL'?routes[n.routing]:null;
 $('profile').innerHTML=`<div class="customer-header"><div class="customer-avatar" aria-hidden="true">◎</div><div><div class="customer-name">Cliente ${esc(c.id)}</div><div class="customer-caption">${c.tenure===null?'Tempo de relacionamento não informado':`${esc(c.tenure)} meses de relacionamento`}</div></div><span class="contact-pill">Perfil do cliente</span></div>
 <div class="profile-stats"><div class="profile-stat"><div class="stat-label">Probabilidade_Churn</div><div class="stat-number raw-score ${probability===null?'word':''}">${esc(scoreText(c.score))}</div><span class="stat-caption">${probability===null?'Análise ainda não disponível para este cliente':'Valor recebido do modelo'}</span></div><div class="profile-stat"><div class="stat-label">Churn_Previsto</div><div class="stat-number word">${esc(predicted(c.score.predicted_churn))}</div><span class="stat-caption">Classificação recebida do modelo</span></div><div class="profile-stat"><div class="stat-label">Decil_Risco</div><div class="stat-number">${esc(c.score.risk_decile||'—')}</div><span class="stat-caption">Agrupamento recebido do modelo</span></div><div class="profile-stat"><div class="stat-label">Sentimento do comentário</div><div class="stat-number word ${sentimentClass(sentiments)}">${esc(labels[sentiments]||'Não disponível')}</div><span class="stat-caption">${review?'Leitura para conferir durante o atendimento':sentiments?'Interpretação do comentário':'Sem interpretação disponível'}</span></div></div>
 <h3 class="profile-title">Produtos e relacionamento</h3><div class="products-card"><div class="product-top"><strong>Internet: ${esc(translate(c.internet))}</strong></div><div class="tags">${tag('Telefone',owned.PhoneService)}${tag('TV',owned.StreamingTV)}${tag('Filmes',owned.StreamingMovies)}${tag('Segurança',owned.OnlineSecurity)}${tag('Backup',owned.OnlineBackup)}${tag('Proteção',owned.DeviceProtection)}${tag('Suporte técnico',owned.TechSupport)}</div><div class="product-detail"><span>Contrato<strong>${esc(translate(c.contract))}</strong></span><span>Forma de pagamento<strong>${esc(translate(c.payment))}</strong></span></div></div>
 <h3 class="profile-title">O que o cliente contou</h3><blockquote class="quote">${esc(c.feedback||'Nenhum comentário disponível.')}</blockquote><p class="feedback-caption">Confirme com o cliente se esse relato ainda representa sua necessidade.</p>
 <details id="feedback-details" class="feedback-details"><summary>Ver interpretação e evidências</summary> ${n.summary||n.situation||n.motives.length?`<div class="insight-card"><h3>✦ Leitura do comentário</h3>${labels[n.situation]?`<span class="situation">${esc(labels[n.situation])}</span>`:''}${n.motives.length?`<div class="tags">${n.motives.map(m=>`<span class="tag">${esc(translate(m))}</span>`).join('')}</div>`:''}${n.summary?`<p>${esc(n.summary)}</p>`:''}${review?'<div class="review-note">Esta interpretação precisa ser conferida antes de orientar a abordagem.</div>':''}</div>`:''}
 ${goodEvidence?`<p class="evidence">Trecho em destaque: “${esc(n.evidence)}”</p>`:''}
 </details> ${nextStep?`<div class="insight-card"><h3>Próximo passo</h3><p>${esc(nextStep)}</p></div>`:''}
 <h3 class="actions-heading">Apoio ao atendimento</h3><div class="actions"><button class="action" data-action="technical"><span aria-hidden="true">⌂</span>Visita técnica</button><button class="action" data-action="offers"><span aria-hidden="true">◇</span>Ofertas disponíveis</button><button class="action" data-action="products"><span aria-hidden="true">↗</span>Plano e produtos</button></div><p class="actions-note">Confirme a necessidade e a elegibilidade antes de propor qualquer alteração.</p>`}
async function choose(id){const current=++detailVersion,currentView=viewVersion,currentBase=base;$('customer-error').textContent='';selected=null;highlight();$('profile').innerHTML=emptyProfile('Consultando o cliente…','Aguarde um instante.');
 try{const c=await api(`/api/customers/${encodeURIComponent(id)}?base=${currentBase}`);if(current!==detailVersion||currentView!==viewVersion)return;
 if(c.base!=='inference')throw Error('Cliente fora da carteira de atendimento.');
 selected=c;$('customer-id').value=c.id;renderProfile(c);highlight();window.Learning.mark('profile');
 }catch(error){if(current!==detailVersion||currentView!==viewVersion)return;selected=null;$('customer-error').textContent=error.message;$('profile').innerHTML=emptyProfile('Vamos conferir o ID?','Confira a identificação e tente novamente.');highlight()}}
async function loadQueue(){const current=++queueVersion,currentView=viewVersion;$('queue-error').textContent='';$('prev').disabled=true;$('next').disabled=true;
 $('queue').innerHTML='<tr><td colspan="4" class="empty-queue">Carregando contatos…</td></tr>';
 let params;try{params=buildFilters()}catch(error){$('queue').innerHTML='<tr><td colspan="4" class="empty-queue">Revise a faixa de probabilidade.</td></tr>';$('queue-error').textContent=error.message;$('queue-note').textContent='';$('queue-count').textContent='—';return} 
 try{const result=await api('/api/customers?'+params);if(current!==queueVersion||currentView!==viewVersion)return;
 if(result.items.some(c=>c.base!=='inference'))throw Error('A consulta retornou clientes fora da carteira.');total=result.total;$('queue-count').textContent=total.toLocaleString('pt-BR');
 $('queue').innerHTML=result.items.length?result.items.map(c=>`<tr data-customer="${esc(c.id)}"><td><strong>${esc(c.id)}</strong><div class="queue-product">${esc(translate(c.internet))} · ${esc(translate(c.contract))}</div></td><td class="score-cell">${c.score.probability===null?'—':esc(scoreText(c.score))}<div class="queue-product">Previsto: ${esc(predicted(c.score.predicted_churn))}</div><div class="queue-product">Decil: ${esc(c.score.risk_decile||'—')}</div></td><td><span class="sentiment-chip ${sentimentClass(c.sentiment)}">${esc(labels[c.sentiment]||'Não disponível')}</span>${c.nlp_status==='REVISAR'?'<div class="queue-product">Conferir leitura</div>':''}</td><td><button class="open-customer" data-id="${esc(c.id)}" aria-label="Abrir cliente ${esc(c.id)}">↗</button></td></tr>`).join(''):'<tr><td colspan="4" class="empty-queue">Nenhum cliente encontrado neste filtro.</td></tr>';
 $('queue-note').textContent=total?`${offset+1}–${Math.min(offset+pageSize,total)} de ${total.toLocaleString('pt-BR')} contatos`:'Nenhum contato';$('prev').disabled=offset===0;$('next').disabled=offset+pageSize>=total;highlight();if(params.get('decile'))window.Learning.mark('decile');if(params.get('predicted_churn'))window.Learning.mark('prediction');
 }catch(error){if(current!==queueVersion||currentView!==viewVersion)return;$('queue').innerHTML='<tr><td colspan="4" class="empty-queue">Não foi possível abrir a carteira.</td></tr>';$('queue-error').textContent=error.message}}
async function loadSummary(){const current=viewVersion;try{const result=await api('/api/summary?base=inference');if(current!==viewVersion)return;
 $('total').textContent=result.customers.toLocaleString('pt-BR');$('classified').textContent=result.classified.toLocaleString('pt-BR');$('scored').textContent=result.scored.toLocaleString('pt-BR');
 }catch(error){if(current===viewVersion)$('page-error').textContent=error.message}}

function buildFilters(){
 const params=new URLSearchParams({base:'inference',q:$('queue-search').value.trim(),sentiment:$('sentiment-filter').value,decile:$('risk-filter').value,predicted_churn:$('prediction-filter').value,offset:String(offset),limit:String(pageSize)});
 const readPercent=id=>{const raw=$(id).value.trim();if(!raw)return null;const value=Number(raw);if(!Number.isFinite(value)||value<0||value>100)throw Error('Informe probabilidades entre 0 e 100%.');return value/100};
 const min=readPercent('probability-min'),max=readPercent('probability-max');
 if(min!==null&&max!==null&&min>max)throw Error('A probabilidade mínima não pode superar a máxima.');
 if(min!==null)params.set('min_probability',String(min));if(max!==null)params.set('max_probability',String(max));
 return params;
}
function applyFilters(){offset=0;clearProfile();loadQueue()}
$('lookup').addEventListener('submit',event=>{event.preventDefault();const id=$('customer-id').value.trim().toUpperCase();if(id)choose(id)});
$('queue').addEventListener('click',event=>{const button=event.target.closest('[data-id]');if(button)choose(button.dataset.id)});
$('queue-search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(applyFilters,250)});
['sentiment-filter','risk-filter','prediction-filter'].forEach(id=>$(id).addEventListener('change',applyFilters));
$('filters-form').addEventListener('submit',event=>{event.preventDefault();applyFilters()});
$('clear-filters').addEventListener('click',()=>{clearTimeout(searchTimer);['queue-search','risk-filter','prediction-filter','sentiment-filter','probability-min','probability-max'].forEach(id=>$(id).value='');applyFilters()});
$('prev').addEventListener('click',()=>{offset=Math.max(0,offset-pageSize);loadQueue()});$('next').addEventListener('click',()=>{offset+=pageSize;loadQueue()});
$('profile').addEventListener('toggle',event=>{if(event.target.id==='feedback-details'&&event.target.open&&selected)window.Learning.mark('feedback')},true);
$('profile').addEventListener('click',event=>{const button=event.target.closest('[data-action]');if(!button||!selected)return;
 const messages={technical:['Visita técnica','O agendamento ainda não está conectado ao sistema de visitas. Nenhuma visita foi agendada.'],offers:['Ofertas disponíveis','A consulta de ofertas ainda não está conectada ao catálogo comercial. Nenhuma condição foi oferecida ou contratada.'],products:['Plano e produtos','A alteração de plano ainda não está conectada ao sistema de contratação. Os produtos atuais estão disponíveis no perfil. Nenhuma alteração foi realizada.']};
 const [title,message]=messages[button.dataset.action];$('dialog-title').textContent=title;$('dialog-copy').textContent=`Cliente ${selected.id}. ${message}`;$('action-dialog').showModal()});
window.Learning.init();clearProfile();loadSummary();loadQueue();
