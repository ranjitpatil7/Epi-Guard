import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Save, Bell, Shield, Cpu, Key, Database, Mail, Smartphone, Loader2 } from "lucide-react"
import { motion } from "framer-motion"
import { containerVariants, itemVariants } from "@/lib/animations"
import { useAuth } from "@/lib/auth/AuthContext"
import { usersApi, type UserPreferences } from "@/lib/api/usersApi"

export default function Settings() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    email: '',
    region_id: '1'
  });

  const { data: preferences, isLoading: isLoadingPrefs, isError: isErrorPrefs } = useQuery({
    queryKey: ['preferences'],
    queryFn: usersApi.getPreferences
  });

  // Local state for preferences to allow optimistic UI updates before saving
  const [localPrefs, setLocalPrefs] = useState<UserPreferences | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileForm({
        full_name: user.full_name || '',
        email: user.email || '',
        region_id: user.region_id?.toString() || '1'
      });
    }
  }, [user]);

  useEffect(() => {
    if (preferences) {
      setLocalPrefs(preferences);
    }
  }, [preferences]);

  const updateProfileMutation = useMutation({
    mutationFn: usersApi.updateProfile,
    onSuccess: () => {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
    onError: () => {
      setSaveError(true);
      setTimeout(() => setSaveError(false), 3000);
    }
  });

  const updatePrefsMutation = useMutation({
    mutationFn: usersApi.updatePreferences,
    onSuccess: (data) => {
      queryClient.setQueryData(['preferences'], data);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
    onError: () => {
      setSaveError(true);
      setTimeout(() => setSaveError(false), 3000);
    }
  });

  const handleSaveProfile = () => {
    updateProfileMutation.mutate({
      full_name: profileForm.full_name,
      email: profileForm.email,
      region_id: parseInt(profileForm.region_id)
    });
  };

  const handleSavePrefs = () => {
    if (localPrefs) {
      updatePrefsMutation.mutate(localPrefs);
    }
  };

  const updateLocalPref = (key: keyof UserPreferences, value: any) => {
    if (localPrefs) {
      setLocalPrefs({ ...localPrefs, [key]: value });
    }
  };

  if (isLoadingPrefs || !localPrefs) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (isErrorPrefs) {
    return (
      <div className="flex h-[50vh] items-center justify-center text-red-500">
        Failed to load preferences. Please try again.
      </div>
    );
  }

  const isSaving = updateProfileMutation.isPending || updatePrefsMutation.isPending;

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6 max-w-5xl mx-auto pb-10"
    >
      <motion.div variants={itemVariants} className="flex justify-between items-center border-b border-white/10 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground text-sm mt-1">Application configuration and user preferences.</p>
        </div>
        <div className="flex gap-2">
          {saveError && <span className="text-red-500 text-sm self-center">Save failed</span>}
          <Button 
            onClick={() => { handleSaveProfile(); handleSavePrefs(); }} 
            className="gap-2 shadow-[0_4px_14px_rgba(59,130,246,0.3)]"
            disabled={isSaving}
          >
            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {isSaving ? "Saving..." : saveSuccess ? "Saved Successfully" : "Save Changes"}
          </Button>
        </div>
      </motion.div>
      
      <Tabs defaultValue="general" className="w-full">
        <motion.div variants={itemVariants}>
          <TabsList className="grid w-full grid-cols-4 mb-6 bg-black/5 p-1 rounded-xl">
            <TabsTrigger value="general" className="rounded-lg data-[state=active]:bg-white/5 data-[state=active]:shadow-sm">General & Profile</TabsTrigger>
            <TabsTrigger value="alerts" className="rounded-lg data-[state=active]:bg-white/5 data-[state=active]:shadow-sm">Notifications & Alerts</TabsTrigger>
            <TabsTrigger value="ai" className="rounded-lg data-[state=active]:bg-white/5 data-[state=active]:shadow-sm">AI & Model Config</TabsTrigger>
            <TabsTrigger value="integrations" className="rounded-lg data-[state=active]:bg-white/5 data-[state=active]:shadow-sm">Integrations & API</TabsTrigger>
          </TabsList>
        </motion.div>

        {/* GENERAL TAB */}
        <TabsContent value="general" className="space-y-4">
          <motion.div variants={itemVariants}>
            <Card className="border-white/10 glass-panel shadow-lg">
              <CardHeader className="border-b border-white/10">
                <CardTitle className="text-xl flex items-center gap-2">
                  <Shield className="w-5 h-5 text-primary" />
                  Profile Settings
                </CardTitle>
                <p className="text-sm text-muted-foreground">Manage your account identity and regional focus.</p>
              </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="space-y-2">
                <Label htmlFor="name">Display Name</Label>
                <Input 
                  id="name" 
                  value={profileForm.full_name} 
                  onChange={(e) => setProfileForm({...profileForm, full_name: e.target.value})} 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input 
                  id="email" 
                  type="email" 
                  value={profileForm.email} 
                  onChange={(e) => setProfileForm({...profileForm, email: e.target.value})} 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="region">Default Region Context</Label>
                <select 
                  id="region" 
                  value={profileForm.region_id}
                  onChange={(e) => setProfileForm({...profileForm, region_id: e.target.value})}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="1">Assam State (Aggregated)</option>
                  <option value="2">Kamrup Metro</option>
                  <option value="3">East Khasi Hills</option>
                </select>
              </div>
            </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={itemVariants}>
            <Card className="border-white/10 glass-panel shadow-lg">
              <CardHeader className="border-b border-white/10">
                <CardTitle className="text-xl">Appearance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="space-y-0.5">
                  <Label>Dark Mode</Label>
                  <p className="text-sm text-muted-foreground">Enable dark theme for the entire platform.</p>
                </div>
                <Switch 
                  checked={localPrefs.dark_mode}
                  onCheckedChange={(c) => updateLocalPref('dark_mode', c)} 
                />
              </div>
              <div className="flex items-center justify-between border-b pb-4">
                <div className="space-y-0.5">
                  <Label>Animations & Glassmorphism</Label>
                  <p className="text-sm text-muted-foreground">Enable modern UI effects (requires capable GPU).</p>
                </div>
                <Switch 
                  checked={localPrefs.animations_enabled}
                  onCheckedChange={(c) => updateLocalPref('animations_enabled', c)} 
                />
              </div>
            </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        {/* ALERTS TAB */}
        <TabsContent value="alerts" className="space-y-4">
          <motion.div variants={itemVariants}>
            <Card className="border-white/10 glass-panel shadow-lg">
              <CardHeader className="border-b border-white/10">
                <CardTitle className="text-xl flex items-center gap-2">
                  <Bell className="w-5 h-5 text-primary" />
                  Notification Channels
                </CardTitle>
                <p className="text-sm text-muted-foreground">How you receive automated public health alerts.</p>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-muted rounded-full"><Mail className="w-4 h-4" /></div>
                  <div className="space-y-0.5">
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive daily digests and critical alerts via email.</p>
                  </div>
                </div>
                <Switch 
                  checked={localPrefs.email_notifications}
                  onCheckedChange={(c) => updateLocalPref('email_notifications', c)}
                />
              </div>
              <div className="flex items-center justify-between border-b pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-muted rounded-full"><Smartphone className="w-4 h-4" /></div>
                  <div className="space-y-0.5">
                    <Label>SMS / Push Notifications</Label>
                    <p className="text-sm text-muted-foreground">Immediate alerts sent to your registered mobile device.</p>
                  </div>
                </div>
                <Switch 
                  checked={localPrefs.sms_notifications}
                  onCheckedChange={(c) => updateLocalPref('sms_notifications', c)}
                />
              </div>
            </CardContent>
            </Card>
          </motion.div>
          
          <motion.div variants={itemVariants}>
            <Card className="border-white/10 glass-panel shadow-lg">
              <CardHeader className="border-b border-white/10">
                <CardTitle className="text-xl">Alert Thresholds</CardTitle>
                <p className="text-sm text-muted-foreground">Configure when the system should interrupt you.</p>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                 <div className="space-y-2">
                  <Label htmlFor="risk-threshold">Minimum Risk Score for Alerting</Label>
                  <div className="flex items-center gap-4">
                    <Input 
                      id="risk-threshold" 
                      type="number" 
                      value={localPrefs.risk_threshold}
                      onChange={(e) => updateLocalPref('risk_threshold', parseInt(e.target.value))}
                      className="w-24" 
                    />
                    <span className="text-sm text-muted-foreground">Alerts will trigger for Risk &gt; {localPrefs.risk_threshold} (HIGH)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        {/* AI CONFIG TAB */}
        <TabsContent value="ai" className="space-y-4">
          <motion.div variants={itemVariants}>
            <Card className="border-white/10 glass-panel shadow-lg">
              <CardHeader className="border-b border-white/10">
                <CardTitle className="text-xl flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-primary" />
                  Copilot & Engine Parameters
                </CardTitle>
                <p className="text-sm text-muted-foreground">Tune the behavior of the Agentic AI and ML models.</p>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="space-y-0.5">
                  <Label>Strict Guardrails (Medical Safety)</Label>
                  <p className="text-sm text-muted-foreground">Prevent the Copilot from making definitive medical diagnoses.</p>
                </div>
                <Switch 
                  checked={localPrefs.strict_guardrails}
                  onCheckedChange={(c) => updateLocalPref('strict_guardrails', c)}
                />
              </div>
              <div className="space-y-2 border-b pb-4">
                <Label>Primary Forecasting Model</Label>
                <select 
                  value={localPrefs.primary_model}
                  onChange={(e) => updateLocalPref('primary_model', e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option>Ensemble (RandomForest + XGBoost)</option>
                  <option>XGBoost Only</option>
                  <option>RandomForest Only</option>
                  <option>ARIMA (Legacy)</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label>Anomaly Detection Sensitivity (Z-Score Threshold)</Label>
                <div className="flex items-center gap-4">
                  <input 
                    type="range" 
                    min="1" 
                    max="5" 
                    step="0.5" 
                    value={localPrefs.anomaly_sensitivity}
                    onChange={(e) => updateLocalPref('anomaly_sensitivity', parseFloat(e.target.value))}
                    className="w-full accent-primary" 
                  />
                  <span className="text-sm font-bold w-12">{localPrefs.anomaly_sensitivity} σ</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
        </TabsContent>

        {/* INTEGRATIONS & API TAB */}
        <TabsContent value="integrations" className="space-y-4">
          <motion.div variants={itemVariants}>
            <Card className="border-primary/50 glass-panel shadow-[0_8px_32px_rgba(59,130,246,0.1)] relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4">
                 <Badge variant="default" className="bg-primary/10 text-primary border-primary/20 hover:bg-primary/20 shadow-sm border">Required</Badge>
              </div>
              <CardHeader className="border-b border-white/10">
                <CardTitle className="text-xl flex items-center gap-2">
                  <Key className="w-5 h-5 text-primary" />
                  Gemini API Configuration
                </CardTitle>
                <p className="text-sm text-muted-foreground">Powers the AI Copilot and investigative reasoning engines.</p>
              </CardHeader>
              <CardContent className="space-y-4 pt-6">
                <div className="space-y-2">
                  <Label htmlFor="gemini-key">Gemini Developer API Key</Label>
                  <Input 
                    id="gemini-key" 
                    type="password" 
                    value={localPrefs.gemini_api_key || ''} 
                    onChange={(e) => updateLocalPref('gemini_api_key', e.target.value)} 
                    className="font-mono bg-white/5 shadow-inner"
                  />
                  <p className="text-xs text-muted-foreground mt-1">This key is securely stored and never transmitted to third parties.</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={itemVariants}>
            <Card className="border-white/10 glass-panel shadow-lg">
              <CardHeader className="border-b border-white/10">
                <CardTitle className="text-xl flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary" />
                  Telemetry Sources
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="space-y-0.5">
                  <Label>IMD Weather Service Sync</Label>
                  <p className="text-sm text-muted-foreground">Automatically fetch rainfall and temperature data.</p>
                </div>
                <Switch 
                  checked={localPrefs.imd_weather_sync}
                  onCheckedChange={(c) => updateLocalPref('imd_weather_sync', c)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Local Hospital Records Sync</Label>
                  <p className="text-sm text-muted-foreground">Ingest anonymized patient admission rates daily.</p>
                </div>
                <Switch 
                  checked={localPrefs.hospital_sync}
                  onCheckedChange={(c) => updateLocalPref('hospital_sync', c)}
                />
              </div>
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

      </Tabs>
    </motion.div>
  )
}
