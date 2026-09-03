import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

interface Incident {
    incident_id: string;
    incident_type: string;
    title: string;
    description: string;
    region_id: number;
    severity: string;
    confidence: number;
    status: string;
    first_detected_at: string;
    last_updated_at: string;
    event_count: number;
    source_event_ids: string[];
    triggered_rules: string[];
    risk_delta: number | null;
    signal_diversity: number;
}

export const IncidentCommandCenter: React.FC = () => {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchIncidents = async () => {
        try {
            const { data } = await apiClient.get('/incidents/');
            if (Array.isArray(data)) {
                setIncidents(data);
            } else {
                setIncidents([]);
            }
        } catch (error) {
            console.error('Failed to fetch incidents', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchIncidents();
        // Polling every 10 seconds for real-time feel
        const interval = setInterval(fetchIncidents, 10000);
        return () => clearInterval(interval);
    }, []);

    const triggerDemo = async () => {
        try {
            await apiClient.post('/incidents/demo');
            fetchIncidents(); // Refresh immediately
        } catch (error) {
            console.error('Failed to trigger demo', error);
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'CRITICAL': return 'bg-red-900 text-red-100 border-red-700';
            case 'HIGH': return 'bg-orange-900 text-orange-100 border-orange-700';
            case 'MEDIUM': return 'bg-yellow-900 text-yellow-100 border-yellow-700';
            case 'LOW': return 'bg-blue-900 text-blue-100 border-blue-700';
            default: return 'bg-gray-800 text-gray-100 border-gray-600';
        }
    };

    if (loading) {
        return <div className="p-4 text-gray-400 animate-pulse">Loading Command Center...</div>;
    }

    return (
        <div className="flex flex-col gap-4 p-4">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-white tracking-wide">Incident Command Center</h2>
                <button 
                    onClick={triggerDemo}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-sm transition-colors"
                >
                    Trigger Demo Scenario
                </button>
            </div>
            
            <div className="bg-red-950/40 border border-red-800/50 rounded p-3 mb-2 flex items-center justify-center">
                <span className="text-red-400 font-mono text-xs font-bold tracking-widest">
                    ⚠️ SYNTHETIC VALIDATION DATA. NON-DIAGNOSTIC DECISION SUPPORT ONLY. ⚠️
                </span>
            </div>

            {incidents.length === 0 ? (
                <div className="text-center p-8 bg-gray-900/50 rounded border border-gray-800">
                    <p className="text-gray-400">No active incidents detected.</p>
                </div>
            ) : (
                <div className="grid gap-6">
                    {incidents.map((incident) => (
                        <div key={incident.incident_id} className={`rounded-lg border p-5 shadow-lg backdrop-blur-sm ${getSeverityColor(incident.severity)}`}>
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <div className="flex items-center gap-3 mb-1">
                                        <span className="px-2 py-0.5 rounded text-xs font-bold bg-black/40 tracking-wider">
                                            {incident.incident_type}
                                        </span>
                                        <span className="text-xs opacity-75 font-mono">
                                            ID: {incident.incident_id.split('-')[0]}
                                        </span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                            incident.status === 'OPEN' ? 'bg-red-500/20 text-red-300' :
                                            incident.status === 'INVESTIGATING' ? 'bg-blue-500/20 text-blue-300' :
                                            'bg-gray-500/20 text-gray-300'
                                        }`}>
                                            {incident.status}
                                        </span>
                                    </div>
                                    <h3 className="text-xl font-bold mt-2">{incident.title}</h3>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs opacity-80 uppercase tracking-wider mb-1">Severity</div>
                                    <div className="text-lg font-bold">{incident.severity}</div>
                                </div>
                            </div>
                            
                            <p className="opacity-90 text-sm mb-4 leading-relaxed">{incident.description}</p>
                            
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                <div className="bg-black/20 p-3 rounded">
                                    <div className="text-xs opacity-70 mb-1">Events Correlated</div>
                                    <div className="text-lg font-mono">{incident.event_count}</div>
                                </div>
                                <div className="bg-black/20 p-3 rounded">
                                    <div className="text-xs opacity-70 mb-1">Signal Diversity</div>
                                    <div className="text-lg font-mono">{incident.signal_diversity} classes</div>
                                </div>
                                <div className="bg-black/20 p-3 rounded">
                                    <div className="text-xs opacity-70 mb-1">Risk Delta</div>
                                    <div className="text-lg font-mono">{incident.risk_delta ? `+${(incident.risk_delta * 100).toFixed(1)}%` : 'N/A'}</div>
                                </div>
                                <div className="bg-black/20 p-3 rounded">
                                    <div className="text-xs opacity-70 mb-1">Confidence Score</div>
                                    <div className="text-lg font-mono">{(incident.confidence * 100).toFixed(0)}%</div>
                                </div>
                            </div>

                            <div className="mt-4 pt-4 border-t border-white/10 text-xs opacity-75 flex justify-between items-center">
                                <div>
                                    <span className="font-semibold mr-2">Triggered Rules:</span>
                                    {incident.triggered_rules.join(', ')}
                                </div>
                                <div className="font-mono">
                                    Detected: {new Date(incident.first_detected_at).toLocaleString()}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
