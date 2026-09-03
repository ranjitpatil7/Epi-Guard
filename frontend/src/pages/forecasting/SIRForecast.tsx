import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Activity, ShieldAlert, HeartPulse, RefreshCw } from "lucide-react";
import { client as api } from "@/lib/api/client";
import { getRegions, type Region } from "@/lib/api/regionsApi";

export default function SIRForecast() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  const [regions, setRegions] = useState<Region[]>([]);
  const [regionsLoading, setRegionsLoading] = useState(true);
  const [regionsError, setRegionsError] = useState(false);
  
  const [regionId, setRegionId] = useState("");
  const [beta, setBeta] = useState(0.3); // Infection rate
  const [gamma, setGamma] = useState(0.1); // Recovery rate
  
  useEffect(() => {
    const fetchInitialRegions = async () => {
      try {
        const fetchedRegions = await getRegions();
        setRegions(fetchedRegions);
        if (fetchedRegions.length > 0) {
          setRegionId(String(fetchedRegions[0].id));
        }
      } catch (err) {
        console.error("Failed to load regions:", err);
        setRegionsError(true);
      } finally {
        setRegionsLoading(false);
      }
    };
    fetchInitialRegions();
  }, []);
  
  const fetchForecast = async () => {
    if (!regionId) return;
    setLoading(true);
    try {
      const res = await api.get(`/forecasting/sir/${regionId}?beta=${beta}&gamma=${gamma}`);
      setData(res.data);
    } catch (err) {
      console.error("Failed to fetch forecast:", err);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (regionId) {
      fetchForecast();
    }
  }, [regionId, beta, gamma]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">Predictive Epidemiology</h1>
          <p className="text-slate-400 mt-2">
            Mathematical SIR Forecasting to predict outbreak trajectories based on current anomalies.
          </p>
        </div>
        <button 
          onClick={fetchForecast}
          disabled={loading || !regionId}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Recalculate
        </button>
      </div>

      {/* Controls */}
      <div className="glass-panel p-6 rounded-xl border border-slate-700/50">
        <h2 className="text-xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <Activity className="h-5 w-5 text-indigo-400" /> Simulation Parameters
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Target Region</label>
            <select 
              value={regionId}
              onChange={(e) => setRegionId(e.target.value)}
              disabled={regionsLoading || regionsError || regions.length === 0}
              className="w-full bg-slate-800 border border-slate-700 rounded-md p-2 text-slate-200 focus:ring-2 focus:ring-blue-500 outline-none disabled:opacity-50"
            >
              {regionsLoading ? (
                <option value="">Loading regions...</option>
              ) : regionsError ? (
                <option value="">Failed to load regions</option>
              ) : regions.length === 0 ? (
                <option value="">No regions available</option>
              ) : (
                regions.map(region => (
                  <option key={region.id} value={region.id}>{region.name}</option>
                ))
              )}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300 flex justify-between">
              <span>Transmission Rate (β)</span>
              <span className="text-blue-400">{beta}</span>
            </label>
            <input 
              type="range" min="0.1" max="1.0" step="0.05"
              value={beta} onChange={(e) => setBeta(parseFloat(e.target.value))}
              className="w-full accent-blue-500"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300 flex justify-between">
              <span>Recovery Rate (γ)</span>
              <span className="text-green-400">{gamma}</span>
            </label>
            <input 
              type="range" min="0.05" max="0.5" step="0.05"
              value={gamma} onChange={(e) => setGamma(parseFloat(e.target.value))}
              className="w-full accent-green-500"
            />
          </div>
        </div>
      </div>

      {/* Stats */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-panel p-6 rounded-xl border border-slate-700/50 border-l-4 border-l-orange-500">
            <p className="text-sm font-medium text-slate-400">Basic Reproduction Number (R0)</p>
            <h3 className="text-3xl font-bold text-slate-100 mt-2">{data.parameters.R0}</h3>
            <p className="text-xs text-slate-500 mt-1">If R0 &gt; 1, the disease will spread.</p>
          </div>
          <div className="glass-panel p-6 rounded-xl border border-slate-700/50 border-l-4 border-l-red-500">
            <p className="text-sm font-medium text-slate-400">Peak Infection Day</p>
            <h3 className="text-3xl font-bold text-slate-100 mt-2 flex items-center gap-2">
              Day {data.insights.peak_infection_day}
              <ShieldAlert className="h-5 w-5 text-red-400" />
            </h3>
            <p className="text-xs text-slate-500 mt-1">Estimated {data.insights.peak_infected_count.toLocaleString()} cases.</p>
          </div>
          <div className="glass-panel p-6 rounded-xl border border-slate-700/50 border-l-4 border-l-green-500">
            <p className="text-sm font-medium text-slate-400">Herd Immunity Threshold</p>
            <h3 className="text-3xl font-bold text-slate-100 mt-2 flex items-center gap-2">
              {data.insights.herd_immunity_threshold}
              <HeartPulse className="h-5 w-5 text-green-400" />
            </h3>
            <p className="text-xs text-slate-500 mt-1">Required resistance to stop spread.</p>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="glass-panel p-6 rounded-xl border border-slate-700/50 h-[450px]">
        {loading ? (
          <div className="flex h-full items-center justify-center">
            <RefreshCw className="h-8 w-8 text-slate-500 animate-spin" />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data?.forecast || []} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="day" stroke="#94a3b8" tick={{ fill: '#94a3b8' }} label={{ value: 'Days', position: 'insideBottomRight', offset: -10, fill: '#94a3b8' }} />
              <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8' }} tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                itemStyle={{ color: '#f8fafc' }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Line type="monotone" dataKey="susceptible" name="Susceptible" stroke="#3b82f6" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
              <Line type="monotone" dataKey="infected" name="Infected" stroke="#ef4444" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
              <Line type="monotone" dataKey="recovered" name="Recovered" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
