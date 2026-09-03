import fs from 'fs';

const fixUnused = (file, regex, repl) => {
    let text = fs.readFileSync(file, 'utf8');
    text = text.replace(regex, repl);
    fs.writeFileSync(file, text);
};

// 1. AnomaliesCenter.tsx
fixUnused('src/pages/anomalies/AnomaliesCenter.tsx', /,\s*Target/, '');

// 2. CommunityReports.tsx
fixUnused('src/pages/community-reports/CommunityReports.tsx', /ShieldAlert,\s*/, '');
fixUnused('src/pages/community-reports/CommunityReports.tsx', /,\s*CheckCircle2/, '');

// 3. Copilot.tsx
fixUnused('src/pages/copilot/Copilot.tsx', /,\s*Map,\s*Search/, '');
fixUnused('src/pages/copilot/Copilot.tsx', /const { mutate: sendMessage, isLoading, error } = useMutation\(/, 'const { mutate: sendMessage, isLoading } = useMutation(');

// 4. Dashboard.tsx
fixUnused('src/pages/dashboard/Dashboard.tsx', /,\s*FileText,\s*CheckCircle2/, '');

// 5. MapView.tsx
fixUnused('src/pages/map/MapView.tsx', /,\s*GeoJSON/, '');
fixUnused('src/pages/map/MapView.tsx', /const \[selectedRegion, setSelectedRegion\] = useState<number \| null>\(null\)/, 'const [selectedRegion] = useState<number | null>(null)');
fixUnused('src/pages/map/MapView.tsx', /const { data: regions } = useQuery\({[^}]*}\)/s, 'useQuery({queryKey: ["regions"], queryFn: getRegions})');
fixUnused('src/pages/map/MapView.tsx', /const { data: riskData } = useQuery\({[^}]*}\)/s, 'useQuery({queryKey: ["currentRisk"], queryFn: getCurrentRisk})');
fixUnused('src/pages/map/MapView.tsx', /const getRiskColor = [^}]+}/s, '');

// 6. ModelIntelligence.tsx
fixUnused('src/pages/model-intelligence/ModelIntelligence.tsx', /,\s*BarChart2/, '');
let miText = fs.readFileSync('src/pages/model-intelligence/ModelIntelligence.tsx', 'utf8');
miText = miText.replace(/new Date\(log\.created_at\)/g, 'new Date(log.created_at as string)');
fs.writeFileSync('src/pages/model-intelligence/ModelIntelligence.tsx', miText);

// 7. RiskAnalytics.tsx
let raText = fs.readFileSync('src/pages/risk/RiskAnalytics.tsx', 'utf8');
raText = raText.replace(/\{`\$\{\(percent \* 100\)\.toFixed\(0\)\}%`\}/g, '{percent ? `${(percent * 100).toFixed(0)}%` : ""}');
fs.writeFileSync('src/pages/risk/RiskAnalytics.tsx', raText);

console.log("Fixes applied.");
