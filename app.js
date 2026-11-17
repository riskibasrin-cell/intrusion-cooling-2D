const $=id=>document.getElementById(id);let worker,result,timer;
const status=t=>$('status').textContent=t;
function busy(b){$('run').disabled=b;$('stop').disabled=!b;$('example').disabled=b;}
function stopAnimation(){clearInterval(timer);timer=null;$('play').textContent='Play animation';}
function color(t){t=Math.max(0,Math.min(1,t));return `rgb(${Math.round(255*Math.min(1,3*t))},${Math.round(255*Math.max(0,Math.min(1,3*t-1)))},${Math.round(255*Math.max(0,3*t-2))})`;}
function field(id,arr,min,max,flow=false){
 const c=$(id),ctx=c.getContext('2d'),p=result.parameters;
 ctx.clearRect(0,0,c.width,c.height);const left=75,top=35,w=540,h=540;
 let nz=arr.length,nx=arr[0].length;
 arr.forEach((row,j)=>row.forEach((v,i)=>{ctx.fillStyle=v===null?'#b8c7cf':color((v-min)/(max-min||1));ctx.fillRect(left+i*w/nx,top+j*h/nz,w/nx+.4,h/nz+.4);}));
 ctx.strokeStyle='#02dcfa';ctx.lineWidth=2;ctx.strokeRect(left+(p.xc-p.width/2)/p.Lx*w,top+(p.zc-p.height/2)/p.Lz*h,p.width/p.Lx*w,p.height/p.Lz*h);
 ctx.fillStyle='#183044';ctx.font='15px system-ui';ctx.fillText('x (m)',left+w/2,top+h+40);ctx.fillText('Local z (m)',left+w+12,top+h/2);
 for(let a=0;a<=4;a++){ctx.fillText(String(p.Lx*a/4),left+w*a/4-10,top+h+20);ctx.fillText(String(p.Lz*a/4),8,top+h*a/4+5);}
 if(flow){let maxq=0;for(let j=0;j<nz;j++)for(let i=0;i<nx;i++)maxq=Math.max(maxq,Math.hypot((result.qx[j][i]+result.qx[j][i+1])/2,(result.qz[j][i]+result.qz[j+1][i])/2));
 ctx.strokeStyle='white';ctx.lineWidth=1.4;
 for(let j=2;j<nz;j+=Math.max(3,Math.round(nz/14)))for(let i=2;i<nx;i+=Math.max(3,Math.round(nx/14))){if(result.intrusion[j][i]||!maxq)continue;
 const u=(result.qx[j][i]+result.qx[j][i+1])/2/maxq*22,v=(result.qz[j][i]+result.qz[j+1][i])/2/maxq*22;
 const x=left+(i+.5)*w/nx,y=top+(j+.5)*h/nz,a=Math.atan2(v,u);ctx.beginPath();ctx.moveTo(x-u/2,y-v/2);ctx.lineTo(x+u/2,y+v/2);ctx.lineTo(x+u/2-5*Math.cos(a-.5),y+v/2-5*Math.sin(a-.5));ctx.moveTo(x+u/2,y+v/2);ctx.lineTo(x+u/2-5*Math.cos(a+.5),y+v/2-5*Math.sin(a+.5));ctx.stroke();}
 ctx.fillStyle='#183044';ctx.fillText(`Head: ${min} to ${max} m`,left,20);}
}
function heat(){if(!result)return;let k=+$('frame').value,p=result.parameters;field('heat',result[$('case').value][k],p.Tb,p.Tm);$('year').textContent=`${result.snapshot_times[k].toFixed(1)} years`;}
function curve(){let c=$('curve'),ctx=c.getContext('2d'),p=result.parameters;ctx.clearRect(0,0,c.width,c.height);let l=80,t=25,w=760,h=340;
 ctx.strokeStyle='#bbc9d2';ctx.fillStyle='#183044';ctx.font='14px system-ui';
 for(let a=0;a<=4;a++){let yy=t+h-a*h/4;ctx.beginPath();ctx.moveTo(l,yy);ctx.lineTo(l+w,yy);ctx.stroke();ctx.fillText((p.Tb+(p.Tm-p.Tb)*a/4).toFixed(0),20,yy+5);ctx.fillText((p.years*a/4).toFixed(0),l+w*a/4-8,t+h+25);}
 for(let [key,col,dash]of[['center_no_flow','#111',[7,5]],['center_flow','#195a99',[]]]){ctx.strokeStyle=col;ctx.lineWidth=2;ctx.setLineDash(dash);ctx.beginPath();result.times.forEach((v,i)=>{let x=l+v/p.years*w,y=t+h-(result[key][i]-p.Tb)/(p.Tm-p.Tb||1)*h;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();}ctx.setLineDash([]);ctx.fillStyle='#183044';ctx.fillText('Time (years)',380,420);ctx.fillText('Temperature (°C)',10,16);}
function show(r,label){stopAnimation();result=r;$('results').hidden=false;$('which').textContent=label+` Intrusion ${r.parameters.width} × ${r.parameters.height} m; grid ${r.parameters.spacing} m; permeability ${r.parameters.k_host} m²; left head ${r.parameters.head_left} m.`;$('frame').max=r.snapshots.length-1;$('frame').value=0;let p=r.parameters,a=r.center_no_flow.at(-1),b=r.center_flow.at(-1);
 $('metrics').textContent=`At ${p.years} years: center without flow ${a.toFixed(3)}°C; with flow ${b.toFixed(3)}°C. Difference (no flow − with flow): ${(a-b).toFixed(3)}°C. Intrusion area: ${r.effective_area.toLocaleString('en-US')} m². Time step: ${r.dt_years.toFixed(3)} years. Largest difference between the final maps: ${r.max_final_map_difference.toFixed(3)}°C.`;
 $('cold').textContent=p.Tb+'°C';$('hot').textContent=p.Tm+'°C';field('flow',r.head,Math.min(p.head_left,p.head_right),Math.max(p.head_left,p.head_right),true);heat();curve();}
$('form').onsubmit=e=>{e.preventDefault();stopAnimation();const p=Object.fromEntries([...new FormData(e.target)].map(([k,v])=>[k,Number(v)]));
 if(p.spacing===40 && (p.width%80!==0||p.height%80!==0)){p.spacing=20;e.target.elements.spacing.value='20';status('Grid adjusted to 20 m to align the intrusion boundaries.');}
 if(!worker){worker=new Worker('./worker.js');worker.onmessage=({data})=>{if(data.type==='status')status(data.message);else if(data.type==='result'){busy(false);show(data.result,'Results of the simulation just completed.');status('Simulation completed.');}else{busy(false);status(data.message);worker.terminate();worker=null;}};worker.onerror=e=>{busy(false);status('Failed to load the worker: '+e.message);worker.terminate();worker=null;};}busy(true);status('Preparing the calculations…');worker.postMessage(p);};
$('stop').onclick=()=>{worker?.terminate();worker=null;busy(false);status('Simulation stopped. Previous results remain visible.');};
$('example').onclick=async()=>{try{const r=await fetch('./results/example.json');if(!r.ok)throw Error('Could not load the example.');show(await r.json(),'Saved example: default parameters, 20 m grid. These results do not use newly edited controls.');status('Saved example displayed.');}catch(e){status(String(e));}};
$('frame').oninput=heat;$('case').onchange=heat;$('play').onclick=()=>{if(timer){stopAnimation();return;}$('play').textContent='Pause';timer=setInterval(()=>{$('frame').value=(+$('frame').value+1)%result.snapshots.length;heat();},160);};
$('download').onclick=()=>{let rows=['years,center_with_flow_C,center_without_flow_C'];result.times.forEach((t,i)=>rows.push([t,result.center_flow[i],result.center_no_flow[i]].join(',')));let u=URL.createObjectURL(new Blob([rows.join('\n')],{type:'text/csv'})),a=document.createElement('a');a.href=u;a.download='intrusion_cooling.csv';a.click();URL.revokeObjectURL(u);};
// The default 200 × 400 m intrusion uses a 20 m grid.
document.querySelector('[name=spacing]').value='20';
