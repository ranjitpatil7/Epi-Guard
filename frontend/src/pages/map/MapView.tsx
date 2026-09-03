import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { getRegions, type Region } from "@/lib/api/regionsApi"
import { getCurrentRisk } from "@/lib/api/riskApi"
import { MapContainer, TileLayer, useMap, CircleMarker, Tooltip } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import { Spinner } from "@/components/ui/spinner"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

function MapUpdater({ center, zoom }: { center: [number, number], zoom: number }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, zoom)
  }, [center, zoom, map])
  return null
}

export const getRiskColor = (riskData: any[] | undefined, regionId: number) => {
  if (!riskData) return "#3b82f6" // blue default
  
  // Guard against regression: riskData is an array, not an object with a .data property
  if (!Array.isArray(riskData)) {
    console.error("Expected riskData to be an array directly");
    return "#3b82f6";
  }
  
  const risk = riskData.find(r => r.region_id === regionId)
  if (!risk) return "#3b82f6" // blue fallback
  
  const score = risk.estimated_risk_score ?? risk.risk_score ?? 0
  if (score >= 80) return "#ef4444" // red
  if (score >= 60) return "#f97316" // orange
  if (score >= 40) return "#eab308" // yellow
  return "#10b981" // green
}

export default function MapView() {
  const { data: regionsData, isLoading: isLoadingRegions } = useQuery({
    queryKey: ['regions'],
    queryFn: getRegions
  })

  const { data: riskData, isLoading: isLoadingRisk } = useQuery({
    queryKey: ['currentRisk'],
    queryFn: getCurrentRisk
  })

  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null)

  if (isLoadingRegions || isLoadingRisk) {
    return <div className="flex h-full items-center justify-center"><Spinner size="lg" /></div>
  }

  // Find center (default Assam)
  const defaultCenter: [number, number] = [26.2, 92.9]

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h1 className="text-3xl font-bold tracking-tight">Intelligence Map</h1>
        <p className="text-muted-foreground text-sm">Geospatial risk monitoring and early warning system.</p>
      </div>
      
      <div className="flex flex-1 gap-4 overflow-hidden">
        {/* Map Container */}
        <div className="flex-1 rounded-xl overflow-hidden border border-border shadow-sm relative z-0">
          <MapContainer center={defaultCenter} zoom={7} className="h-full w-full" zoomControl={true}>
            {/* Dark mode friendly map tiles */}
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            />
            <MapUpdater center={defaultCenter} zoom={7} />
            
            {/* Render Region Markers */}
            {regionsData?.map(region => (
              region.lat && region.lng && (
                <CircleMarker
                  key={region.id}
                  center={[region.lat, region.lng]}
                  radius={12}
                  pathOptions={{ 
                    fillColor: getRiskColor(riskData, region.id), 
                    color: getRiskColor(riskData, region.id), 
                    weight: 2, 
                    fillOpacity: selectedRegion?.id === region.id ? 0.9 : 0.6 
                  }}
                  eventHandlers={{
                    click: () => setSelectedRegion(region)
                  }}
                >
                  <Tooltip>
                    <div className="text-sm font-semibold">{region.name}</div>
                    <div className="text-xs text-muted-foreground">Click for intelligence</div>
                  </Tooltip>
                </CircleMarker>
              )
            ))}
          </MapContainer>
        </div>

        {/* Intelligence Panel */}
        <div className="w-80 flex flex-col gap-4 overflow-y-auto">
          <Card className="p-4 flex-shrink-0">
            <h3 className="font-semibold mb-2">Map Layers</h3>
            <div className="space-y-2 text-sm text-muted-foreground">
              <label className="flex items-center gap-2">
                <input type="checkbox" defaultChecked className="rounded border-input text-primary" />
                Risk Choropleth
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded border-input text-primary" />
                Community Reports
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded border-input text-primary" />
                Water Quality Sensors
              </label>
            </div>
          </Card>
          
          <Card className="p-4 flex-1 overflow-y-auto">
            {selectedRegion ? (
              <div>
                <h3 className="font-bold text-lg">{selectedRegion.name}</h3>
                <p className="text-xs text-muted-foreground mb-4">{selectedRegion.district}, {selectedRegion.state}</p>
                
                <div className="space-y-4 mt-4">
                  <div>
                    <h4 className="text-sm font-semibold mb-1">Population</h4>
                    <p className="text-sm">{selectedRegion.population.toLocaleString()}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Active Intelligence Alerts</h4>
                    <div className="space-y-2">
                       <Badge variant="destructive" className="w-full justify-center">Risk Score Elevated</Badge>
                       <Badge variant="outline" className="w-full justify-center text-amber-500 border-amber-500/50">Anomaly Detected</Badge>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground opacity-70">
                <p className="text-sm">Select a region on the map to view detailed intelligence.</p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
