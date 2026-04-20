import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, Shield, ShieldAlert, Cpu, RefreshCw, Send, CheckCircle, 
  Layers, Activity, HelpCircle, Zap, Server, ChevronRight 
} from 'lucide-react';

// --- Configuration & Constants ---
const MISSIONS = [
  { id: 'm00_basics', category: 'Foundations', name: 'Core Agent Setup', definition: 'Baseline state management and classification loops.', defaultPrompt: 'Check device status for employee E-102' },
  { id: 'm01_fragile_demo', category: 'Analysis', name: 'Fragility Analysis', definition: 'Baseline test showing standard agent crash on API failures.', defaultPrompt: 'Process server reset on floor 3' },
  { id: 'm02_self_healing', category: 'Self-Healing', name: 'Basic Retry Loop', definition: 'Implements try/except feedback cycles for autonomous recovery.', defaultPrompt: 'Process payroll for E-777' },
  { id: 'm03_diagnostic_router', category: 'Foundations', name: 'Diagnostic Router', definition: 'AI identifies core error types before initiating repairs.', defaultPrompt: 'Reset password for user "admin"' },
  { id: 'm04_payload_repair', category: 'Self-Healing', name: 'Data Payload Repair', definition: 'Autonomous correction of malformed or missing JSON fields.', defaultPrompt: 'Create a new ticket for hardware check.' },
  { id: 'm05_tool_query_repair', category: 'Self-Healing', name: 'Query Re-Writing', definition: 'Fixes vague or broken tool queries using meta-reasoning.', defaultPrompt: 'Search for that one policy about vacation' },
  { id: 'm06_autonomous_prompt_repair', category: 'Self-Healing', name: 'Deep Prompt Repair', definition: 'Meta-prompting logic that fixes internal instructions on the fly.', defaultPrompt: 'Translate this to formal French: "How do I fix my laptop?"' },
  { id: 'm07_workflow_order_repair', category: 'Orchestration', name: 'Workflow Repair', definition: 'Autonomously re-sequences steps to bypass logical blocks.', defaultPrompt: 'Verify user then process refund then log it' },
  { id: 'm08_execution_persistence', category: 'Persistence', name: 'Memory Checkpoints', definition: 'Resumes agent execution from failure state saving total state.', defaultPrompt: 'Execute multi-step backup' },
  { id: 'm09_multi_strategy_orchestrator', category: 'Orchestration', name: 'Master Orchestrator', definition: 'Advanced multi-strategy loop for complex nested failures.', defaultPrompt: 'Optimize global traffic routing nodes' },
  { id: 'm10_safety_escalation', category: 'Final Lab', name: 'Safety Escalation', definition: 'Graceful human-in-the-loop fallback for high-risk errors.', defaultPrompt: 'Access top secret encryption keys' },
  { id: 'm11_reusable_agent_template', category: 'Final Lab', name: 'Production Template', definition: 'Modular baseline for industrial-grade resilient agents.', defaultPrompt: 'Validate server health' },
  { id: 'm12_self_healing_helpdesk_capstone', category: 'Final Lab', name: 'Resilient Helpdesk Capstone', definition: 'The ultimate production-grade helpdesk system using all healing patterns.', defaultPrompt: 'Employee E-999 needs a hardware check.' },
];

const CATEGORIES = ['Foundations', 'Analysis', 'Self-Healing', 'Orchestration', 'Persistence', 'Final Lab'];

// --- Sub-Components ---

const Sidebar = ({ activeMission, onSelect }) => {
  const [expandedCategory, setExpandedCategory] = useState(activeMission.category);

  return (
    <aside className="col-span-3 border-r border-slate-200 pr-8 overflow-y-auto custom-scrollbar flex flex-col gap-6 py-4">
      <section>
        <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
          <Server size={12}/> Mission Curriculum
        </h3>
        <div className="space-y-2">
          {CATEGORIES.map((cat) => (
            <div key={cat} className="space-y-1">
              <button 
                onClick={() => setExpandedCategory(expandedCategory === cat ? null : cat)}
                className={`w-full flex items-center justify-between p-3 rounded-xl transition-all ${expandedCategory === cat ? 'bg-slate-100 text-slate-900' : 'text-slate-500 hover:bg-slate-50'}`}
              >
                <span className="text-[11px] font-black uppercase tracking-widest">{cat}</span>
                <ChevronRight size={14} className={`transition-transform ${expandedCategory === cat ? 'rotate-90 text-blue-500' : ''}`} />
              </button>
              
              <AnimatePresence>
                {expandedCategory === cat && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden pl-2 flex flex-col gap-1"
                  >
                    {MISSIONS.filter(m => m.category === cat).map((m) => (
                      <button 
                        key={m.id}
                        onClick={() => onSelect(m)}
                        className={`w-full flex flex-col p-3 rounded-xl transition-all text-left ${activeMission.id === m.id ? 'bg-white shadow-md border border-slate-200' : 'hover:bg-slate-100 text-slate-500'}`}
                      >
                        <div className="flex justify-between items-center mb-0.5">
                          <span className={`text-[9px] font-bold uppercase transition-colors ${activeMission.id === m.id ? 'text-blue-600' : 'text-slate-400'}`}>{m.name}</span>
                          {activeMission.id === m.id && <Zap size={8} className="text-blue-600 animate-pulse" />}
                        </div>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </section>
      
      <div className="mt-auto bg-blue-50 border border-blue-100 p-6 rounded-2xl">
        <h4 className="text-[11px] font-black text-blue-900 uppercase tracking-widest mb-2 flex items-center gap-2">
          <HelpCircle size={14}/> Resilience Core
        </h4>
        <p className="text-[11px] text-blue-700 font-medium leading-relaxed">
          Select a category to explore specialized self-healing patterns and their execution traces.
        </p>
      </div>
    </aside>
  );
};
const ExecutionArena = ({ mission, input, setInput, onRun, loading, result }) => {
  const samples = {
    m00_basics: ["Check device status for employee E-102", "Request latest IT policy"],
    m01_fragile_demo: ["Check device for employee E-102", "Run server diagnostic"],
    m02_self_healing: ["Initialize autonomous repair loop", "Safe divide 100/0"],
    m03_diagnostic_router: ["Check device for employee E-102", "Reset VPN and check legal policy"],
    m04_payload_repair: ["Onboard employee E-555", "Sync employee E-999 to backend"],
    m05_tool_query_repair: ["Check device policy for laptop approvals", "Search legal vpn requirements"],
    m06_autonomous_prompt_repair: ["Employee E-999 wants a laptop lookup.", "Extract details for user 'admin'"],
    m07_workflow_order_repair: ["Onboard employee E-102 and request a laptop.", "Provision hardware for Sales team"],
    m08_execution_persistence: ["Retrieve secure server logs", "Status of long running task"],
    m09_multi_strategy_orchestrator: ["Request laptop for E-102 in the Engineering department.", "Optimize multi-node IT routing"],
    m10_safety_escalation: ["Shutdown production database", "Access secure admin kernel"],
    m11_reusable_agent_template: ["Provision new employee E-102", "Generic healing heartbeat"],
    m12_self_healing_helpdesk_capstone: ["Requesting a hardware status report for E-102.", "Full system diagnostics for floor 3"]
  };

  const currentSamples = samples[mission.id] || [mission.defaultPrompt];

  const techInsights = {
    m00_basics: "Baseline state management using TypedDict and Pydantic validation nodes.",
    m01_fragile_demo: "Linear execution flow with zero error handling; designed to demonstrate catastrophic failure.",
    m02_self_healing: "Implements a recursive retry loop that feeds error logs back into the LLM for autonomous correction.",
    m03_diagnostic_router: "Uses a classifier node to identify intent (IT vs HR) before branching into specialized workflows.",
    m04_payload_repair: "Autonomous JSON correction. AI repairs missing or malformed keys in real-time.",
    m05_tool_query_repair: "Meta-reasoning layer that re-writes vague user queries into structured tool parameters.",
    m06_autonomous_prompt_repair: "Self-correcting system instructions. The agent detects and bypasses 'prompt hijacking' attempts.",
    m07_workflow_order_repair: "Dynamic plan regeneration. Re-sequences tasks based on dependency availability.",
    m08_execution_persistence: "State checkpointing. Allows the agent to resume from the exact point of failure.",
    m09_multi_strategy_orchestrator: "Advanced multi-agent orchestration for nested complex system failures.",
    m10_safety_escalation: "Implements a 'Safe Guard' node that halts execution for high-risk operations.",
    m11_reusable_agent_template: "Modular, industrial-grade boilerplate for repeatable resilience patterns.",
    m12_self_healing_helpdesk_capstone: "Full integrated stack combining routing, repair, and fallback into one platform."
  };

  return (
    <main className="col-span-6 px-12 overflow-y-auto custom-scrollbar py-4">
      <motion.div key={mission.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
        <div>
          <div className="flex items-center gap-3 mb-2 text-blue-600">
             <Layers size={20} />
             <span className="text-[11px] font-black uppercase tracking-widest">{mission.category}</span>
          </div>
          <h2 className="text-4xl font-black text-slate-900 tracking-tight mb-2 underline decoration-blue-500/20 underline-offset-8 decoration-4">{mission.name}</h2>
          <p className="text-slate-500 font-medium text-lg leading-relaxed max-w-2xl">{mission.definition}</p>
          
          <div className="mt-4 inline-flex items-center gap-2 bg-slate-900 text-[10px] font-black text-slate-400 uppercase tracking-widest px-4 py-2 rounded-xl border border-slate-800 shadow-xl">
             <Cpu size={12} className="text-blue-500" />
             Tech Insight: <span className="text-slate-200 normal-case ml-1 font-bold">{techInsights[mission.id]}</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-[2.5rem] p-10 shadow-sm space-y-8">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest">Input Payload</label>
              <div className="flex flex-wrap gap-2">
                {currentSamples.map((s, i) => (
                  <button 
                    key={i} 
                    onClick={() => setInput(s)}
                    className="text-[9px] font-black bg-slate-100 text-slate-500 hover:bg-blue-600 hover:text-white px-3 py-1 rounded-full transition-all border border-slate-200"
                  >
                    {s}
                  </button>
                ))}
              </div>
              <span className="text-[10px] font-bold text-slate-300">UTF-8 / JSON</span>
            </div>
            <textarea 
              className="w-full bg-slate-50 border border-slate-200 rounded-3xl p-8 text-sm font-mono outline-none focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500/30 transition-all h-32 resize-none leading-relaxed"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
          </div>
        <button 
          onClick={onRun}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 py-6 rounded-3xl text-white font-black uppercase tracking-widest text-sm flex items-center justify-center gap-4 transition-all shadow-xl shadow-blue-200 active:scale-[0.98]"
        >
          {loading ? <RefreshCw className="animate-spin" size={20}/> : <Send size={20}/>}
          {loading ? "Engaging Resilience Engine..." : "Initiate Autonomous Run"}
        </button>
      </div>

      <AnimatePresence>
        {result && (
          <motion.section 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`rounded-[2.5rem] p-10 shadow-sm border-2 ${
              result.type === 'warning' ? 'bg-amber-50 border-amber-500/10' : 
              result.type === 'info' ? 'bg-blue-50 border-blue-500/10' :
              'bg-emerald-50 border-emerald-500/10'
            }`}
          >
            <div className="flex items-center gap-4 mb-6">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg ${
                result.type === 'warning' ? 'bg-amber-500 shadow-amber-200' : 
                result.type === 'info' ? 'bg-blue-500 shadow-blue-200' :
                'bg-emerald-500 shadow-emerald-200'
              }`}>
                {result.type === 'warning' ? <ShieldAlert className="text-white" size={24}/> : 
                 result.type === 'info' ? <Activity className="text-white" size={24}/> :
                 <CheckCircle className="text-white" size={24}/>}
              </div>
              <div>
                <h3 className="text-xl font-black text-slate-900 tracking-tight">
                  {result.type === 'warning' ? 'Safety Escalation' : 
                   result.type === 'info' ? 'System Diagnostic' : 
                   'Recovery Success'}
                </h3>
                <p className={`text-xs font-bold uppercase tracking-widest ${
                   result.type === 'warning' ? 'text-amber-600' : 
                   result.type === 'info' ? 'text-blue-600' :
                   'text-emerald-600'
                }`}>
                  {result.type === 'warning' ? 'Human-in-the-Loop Required' : 
                   result.type === 'info' ? 'Self-Healing Analysis Complete' :
                   'Autonomous Convergence Reached'}
                </p>
              </div>
            </div>
            <div className="space-y-4">
               <div>
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Response Summary</h4>
                  <p className="font-bold text-slate-800 text-lg">{result.summary || "Execution Synchronized"}</p>
               </div>
               <div>
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Engine Metadata</h4>
                  <pre className={`text-sm leading-relaxed font-mono bg-white/50 p-4 rounded-xl border whitespace-pre-wrap overflow-auto max-h-[250px] custom-scrollbar ${
                    result.type === 'warning' ? 'text-amber-700 border-amber-500/5' : 
                    result.type === 'info' ? 'text-blue-700 border-blue-500/5' :
                    'text-slate-500 border-emerald-500/5'
                  }`}>
                    {typeof result.details === 'string' ? result.details : JSON.stringify(result.details, null, 2) || "No extra metadata returned."}
                  </pre>
               </div>
            </div>
          </motion.section>
        )}
      </AnimatePresence>
    </motion.div>
  </main>
  );
};

const LogStream = ({ logs, loading }) => {
  const logEndRef = useRef(null);
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [logs]);

  return (
    <aside className="col-span-3 border-l border-slate-200 pl-8 flex flex-col h-full overflow-hidden py-4">
      <div className="flex items-center justify-between mb-4 px-2">
        <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
          <Terminal size={12}/> Live Trace
        </h3>
        <Activity size={14} className={loading ? "text-blue-500 animate-pulse" : "text-slate-300"} />
      </div>
      
      <div className="flex-1 bg-[#0a0c10] rounded-[2rem] overflow-hidden flex flex-col shadow-2xl border border-slate-800">
        <div className="bg-white/[0.03] border-b border-white/[0.03] px-6 py-3 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-slate-700"></div>
          <span className="text-[10px] font-mono font-bold text-slate-600">MISSION_CONTROL.log</span>
        </div>
        <div className="flex-1 p-8 font-mono text-[11px] overflow-y-auto custom-scrollbar space-y-4 leading-relaxed">
          {logs.map((log, i) => (
            <div key={i} className="flex gap-4">
              <span className="text-slate-800 select-none min-w-[20px]">{(i+1).toString().padStart(2, '0')}</span>
              <span className={
                log.includes('[ERROR]') ? 'text-rose-400' : 
                log.includes('[DONE]') ? 'text-emerald-400 font-bold' : 
                log.includes('[INPUT]') ? 'text-blue-400 opacity-60' : 'text-slate-400'
              }>{log}</span>
            </div>
          ))}
          {loading && (
            <div className="flex gap-4 animate-pulse">
               <span className="text-slate-800">..</span>
               <span className="text-blue-500 font-bold italic">Analyzing state mismatch & executing repair...</span>
            </div>
          )}
          <div ref={logEndRef} />
        </div>
      </div>
    </aside>
  );
};

// --- Main Application ---

const Dashboard = () => {
  const [activeMission, setActiveMission] = useState(MISSIONS[MISSIONS.length - 1]);
  const [input, setInput] = useState(activeMission.defaultPrompt);
  const [logs, setLogs] = useState(['Bootstrap complete. Deep-healing logic online.']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const performRun = async () => {
    setLoading(true);
    setResult(null);
    setLogs(prev => [...prev, `[INIT] Booting sequence for ${activeMission.id}`, `[INPUT] ${input}`]);
    
    try {
      const resp = await fetch('http://localhost:8000/run-mission', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mission_id: activeMission.id, user_input: input })
      });

      const data = await resp.json();
      
      if (data.status === 'success') {
        const out = data.final_output?.final_outcome || data.final_output;
        setLogs(prev => [...prev, ...data.logs, "[DONE] Recovery cycle complete."]);
        
        // Determine type based on outcome content
        let type = 'success';
        if (out?.summary?.toLowerCase().includes('escalat') || out?.summary?.toLowerCase().includes('stop') || out?.status?.toLowerCase().includes('stop')) {
          type = 'warning';
        } else if (out?.summary?.toLowerCase().includes('diagnostic')) {
          type = 'info';
        }

        setResult({
          type: type,
          summary: out?.summary || "Execution Synchronized",
          details: out?.details || out
        });
      } else {
        throw new Error(data.detail || "Engine Timeout");
      }
    } catch (err) {
      setLogs(prev => [...prev, `[ERROR] ${err.message}`]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen overflow-hidden bg-[#F8FAFC] text-[#1E293B] font-sans selection:bg-blue-100 flex flex-col">
      <header className="bg-white border-b border-slate-200 px-12 py-5 sticky top-0 z-50 shadow-sm backdrop-blur-md bg-white/90">
        <div className="max-w-[1900px] mx-auto flex justify-between items-center">
          <div className="flex items-center gap-5">
            <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-200">
              <Shield className="text-white" size={28} />
            </div>
            <div>
              <h1 className="text-xl font-black tracking-tight text-slate-900 uppercase italic">Parthi: Autonomous Resilience Lab</h1>
              <p className="text-[11px] text-slate-500 font-bold uppercase tracking-[0.2em]">Industry Standard AI Recovery Framework</p>
            </div>
          </div>
          <div className="flex items-center gap-10">
             <div className="hidden md:flex gap-8">
                <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest cursor-default hover:text-blue-600 transition-colors">Documentation</span>
                <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest cursor-default hover:text-blue-600 transition-colors">API Console</span>
             </div>
             <div className="h-8 w-[1px] bg-slate-200"></div>
             <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
                <span className="text-xs font-black text-slate-700 uppercase tracking-widest">Engine: v2.4.0</span>
             </div>
          </div>
        </div>
      </header>

      <div className="max-w-[1900px] mx-auto grid grid-cols-12 gap-0 flex-1 px-12 overflow-hidden">
        <Sidebar activeMission={activeMission} onSelect={(m) => { setActiveMission(m); setInput(m.defaultPrompt); }} />
        <ExecutionArena 
          mission={activeMission} 
          input={input} 
          setInput={setInput} 
          onRun={performRun} 
          loading={loading} 
          result={result} 
        />
        <LogStream logs={logs} loading={loading} />
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.1); }
      `}} />
    </div>
  );
};

export default Dashboard;
