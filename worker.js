// Run Python in a worker so the page stays responsive.
importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js');
let runtime;
self.onmessage=async({data})=>{
 try{
  if(!runtime){
   self.postMessage({type:'status',message:'Loading Python, NumPy, and SciPy. The first download may take some time.'});
   runtime=await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/'});
   await runtime.loadPackage(['numpy','scipy']);
   const response=await fetch('./simulation.py');
   if(!response.ok)throw Error('Could not load the simulation code.');
   runtime.FS.writeFile('/home/pyodide/simulation.py',await response.text());
   await runtime.runPythonAsync('from simulation import browser_run');
  }
  self.postMessage({type:'status',message:'Calculating the cases with and without flow…'});
  runtime.globals.set('parameter_json',JSON.stringify(data));
  const result=await runtime.runPythonAsync('browser_run(parameter_json)');
  self.postMessage({type:'result',result:JSON.parse(result)});
 }catch(error){self.postMessage({type:'error',message:String(error)});}
};
