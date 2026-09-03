export interface RiskLineage {
    origin_event_id: string;
    caused_by: string;
    processing_depth: number;
}

export interface RiskEventPayload {
    region_id: number;
    snapshot_id: string;
    current_risk: number;
    previous_risk: number;
    risk_delta: number;
    change_type: string;
    confidence: number;
    prediction_interval: {
        lower: number;
        upper: number;
    };
    lineage: RiskLineage;
}

export interface AlertEventPayload {
    alert_id: number;
    region_id: number;
    severity: string;
    message: string;
    confidence: number;
    prediction_interval?: any;
    risk_snapshot_id?: string;
    timestamp: string;
}

export interface IntelligenceEvent {
    event_id: string;
    event_type: 'RISK_RECALCULATED' | 'RISK_ESCALATED' | 'RISK_DEESCALATED' | 'ALERT_CREATED' | 'ALERT_ESCALATED' | 'ALERT_DEESCALATED' | 'ALERT_RESOLVED' | string;
    region_id: number;
    source: string;
    timestamp: string;
    payload: RiskEventPayload | AlertEventPayload | any;
    schema_version: string;
    confidence: number;
    correlation_id?: string;
}
