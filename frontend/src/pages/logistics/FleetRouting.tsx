import { useState, useEffect } from "react";
import { MapPin, Navigation, Truck, Package, Clock, CheckCircle, Rocket, AlertTriangle, Loader2 } from "lucide-react";
import { client as api } from "@/lib/api/client";
import { getRegions, type Region } from "@/lib/api/regionsApi";

const STANDARD_KIT = [
  { item: "ORS Packets", quantity: 500, unit: "packets" },
  { item: "Water Purification Tablets", quantity: 1000, unit: "tablets" },
  { item: "Vaccines (Cholera)", quantity: 200, unit: "vials" },
];

export default function FleetRouting() {
  const [routeData, setRouteData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [dispatching, setDispatching] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<any>(null);
  
  const [regions, setRegions] = useState<Region[]>([]);
  const [regionsLoading, setRegionsLoading] = useState(true);
  const [regionsError, setRegionsError] = useState(false);
  const [selectedRegionIds, setSelectedRegionIds] = useState<number[]>([]);

  // Editable kit quantities (per-dispatch overrides)
  const [kitQuantities, setKitQuantities] = useState(
    STANDARD_KIT.map(k => ({ ...k }))
  );
  
  useEffect(() => {
    const fetchInitialRegions = async () => {
      try {
        const fetchedRegions = await getRegions();
        setRegions(fetchedRegions);
      } catch (err) {
        console.error("Failed to load regions:", err);
        setRegionsError(true);
      } finally {
        setRegionsLoading(false);
      }
    };
    fetchInitialRegions();
  }, []);

  const calculateRoute = async () => {
    if (selectedRegionIds.length === 0) return;
    setLoading(true);
    setDispatchResult(null);
    try {
      const regionsStr = selectedRegionIds.join(",");
      const res = await api.get(`/logistics/dispatch-route?regions=${regionsStr}`);
      setRouteData(res.data.data);
    } catch (err) {
      console.error("Failed to calculate route:", err);
    } finally {
      setLoading(false);
    }
  };

  const dispatchFleet = async () => {
    if (selectedRegionIds.length === 0) return;
    setDispatching(true);
    try {
      const res = await api.post("/logistics/dispatch", { region_ids: selectedRegionIds });
      setDispatchResult(res.data.data);
    } catch (err: any) {
      console.error("Failed to dispatch fleet:", err);
      setDispatchResult({ error: err.response?.data?.detail || err.message });
    } finally {
      setDispatching(false);
    }
  };

  const toggleRegion = (id: number) => {
    setSelectedRegionIds(prev => 
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">Automated Fleet Routing</h1>
          <p className="text-slate-400 mt-2">
            Greedy TSP Heuristic routing for medical and drone response units.
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={calculateRoute}
            disabled={loading || selectedRegionIds.length === 0}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Navigation className="h-4 w-4" />} 
            {loading ? "Calculating..." : "Optimize Route"}
          </button>
          {routeData && (
            <button 
              onClick={dispatchFleet}
              disabled={dispatching || selectedRegionIds.length === 0}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)]"
            >
              {dispatching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
              {dispatching ? "Dispatching..." : "Dispatch Fleet"}
            </button>
          )}
        </div>
      </div>

      {/* Dispatch Success / Error Toast */}
      {dispatchResult && !dispatchResult.error && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 backdrop-blur-md p-4 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold">
            <CheckCircle className="h-5 w-5" />
            Fleet Successfully Dispatched
          </div>
          <p className="text-sm text-emerald-300/80">
            {dispatchResult.dispatched_regions?.length || 0} regions supplied. Total route: {dispatchResult.total_distance_km} km ({dispatchResult.estimated_time_hrs} hrs).
          </p>
          {dispatchResult.inventory_warnings?.length > 0 && (
            <div className="flex items-start gap-2 rounded-lg bg-amber-500/10 border border-amber-500/20 p-3 text-amber-400 text-xs">
              <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
              <div>
                <p className="font-semibold mb-1">Inventory Warnings</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {dispatchResult.inventory_warnings.map((w: string, i: number) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {dispatchResult?.error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400 text-sm">
          Dispatch failed: {dispatchResult.error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Controls and Metrics */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel p-6 rounded-xl border border-slate-700/50">
            <h2 className="text-xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
              <Package className="h-5 w-5 text-indigo-400" /> Dispatch Request
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Select Target Regions</label>
                <div className="max-h-60 overflow-y-auto space-y-2 p-3 bg-slate-800 rounded-md border border-slate-700">
                  {regionsLoading ? (
                    <span className="text-slate-400 text-sm">Loading regions...</span>
                  ) : regionsError ? (
                    <span className="text-red-400 text-sm">Failed to load regions.</span>
                  ) : regions.length === 0 ? (
                    <span className="text-slate-400 text-sm">No regions found.</span>
                  ) : (
                    regions.map(region => (
                      <label key={region.id} className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedRegionIds.includes(region.id)}
                          onChange={() => toggleRegion(region.id)}
                          className="rounded border-slate-600 bg-slate-700 text-indigo-500 focus:ring-indigo-500/50"
                        />
                        {region.name}
                      </label>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Standard Emergency Kit (editable defaults) */}
          <div className="glass-panel p-6 rounded-xl border border-slate-700/50">
            <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
              <Package className="h-5 w-5 text-emerald-400" /> Standard Emergency Kit
            </h2>
            <p className="text-xs text-slate-400 mb-4">Per-region supply allocation (editable)</p>
            <div className="space-y-3">
              {kitQuantities.map((kit, idx) => (
                <div key={kit.item} className="flex items-center gap-3">
                  <span className="text-sm text-slate-300 flex-1 truncate">{kit.item}</span>
                  <input
                    type="number"
                    value={kit.quantity}
                    onChange={(e) => {
                      const updated = [...kitQuantities];
                      updated[idx] = { ...updated[idx], quantity: parseInt(e.target.value) || 0 };
                      setKitQuantities(updated);
                    }}
                    className="w-24 bg-slate-800 border border-slate-700 rounded-md p-1.5 text-slate-200 text-sm text-right focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                  <span className="text-xs text-slate-500 w-14">{kit.unit}</span>
                </div>
              ))}
            </div>
          </div>

          {routeData && (
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-panel p-4 rounded-xl border border-slate-700/50">
                <div className="flex items-center gap-2 text-slate-400 mb-1">
                  <Truck className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">Total Distance</span>
                </div>
                <div className="text-2xl font-bold text-slate-100">{routeData.total_distance_km} <span className="text-sm font-normal text-slate-500">km</span></div>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-slate-700/50">
                <div className="flex items-center gap-2 text-slate-400 mb-1">
                  <Clock className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">Estimated ETA</span>
                </div>
                <div className="text-2xl font-bold text-slate-100">{routeData.estimated_time_hrs} <span className="text-sm font-normal text-slate-500">hrs</span></div>
              </div>
            </div>
          )}
        </div>

        {/* Route Visualization */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-xl border border-slate-700/50">
          <h2 className="text-xl font-semibold text-slate-100 mb-6 flex items-center gap-2">
            <MapPin className="h-5 w-5 text-indigo-400" /> Dispatch Sequence
          </h2>
          
          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <span className="text-slate-500 animate-pulse">Running Optimization Algorithm...</span>
            </div>
          ) : routeData?.route ? (
            <div className="space-y-0">
              {routeData.route.map((stop: any, index: number) => (
                <div key={index} className="flex relative">
                  {/* Timeline connecting line */}
                  {index !== routeData.route.length - 1 && (
                    <div className="absolute left-6 top-10 bottom-[-10px] w-0.5 bg-indigo-500/30"></div>
                  )}
                  
                  {/* Stop Node */}
                  <div className="mr-6 z-10 flex flex-col items-center">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center border-4 border-slate-900 ${
                      stop.id === 'HUB' ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300'
                    }`}>
                      {stop.id === 'HUB' ? <Truck className="h-5 w-5" /> : index}
                    </div>
                  </div>
                  
                  {/* Stop Details */}
                  <div className="pb-10 pt-2 flex-1">
                    <h3 className="text-lg font-bold text-slate-200">{stop.name}</h3>
                    <div className="flex gap-4 mt-1 text-sm text-slate-400">
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3"/> Lat: {stop.lat?.toFixed(2) || "N/A"}, Lng: {stop.lng?.toFixed(2) || "N/A"}</span>
                      {stop.distance_from_last_km > 0 && (
                        <span className="flex items-center gap-1 text-indigo-400">
                          <Navigation className="h-3 w-3"/> {stop.distance_from_last_km} km from last stop
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Status */}
                  <div className="pt-3">
                    <CheckCircle className={`h-6 w-6 ${dispatchResult && !dispatchResult.error ? 'text-emerald-500' : 'text-slate-600'}`} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-500">
              No route calculated yet. Select regions and calculate the route.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
