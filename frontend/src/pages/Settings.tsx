/**
 * Settings Page - Dashboard Version
 * User account settings and preferences
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings as SettingsIcon,
  User,
  Lock,
  Bell,
  Shield,
  Globe,
  Moon,
  Sun,
  Eye,
  EyeOff,
  Save,
  Loader2,
  ChevronRight,
  LogOut,
  Trash2,
  Mail,
  Smartphone
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/apiClient';
import { cn } from '@/lib/utils';
import DashboardCard from '@/components/dashboard/DashboardCard';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

const Settings = () => {
  const { user, signOut } = useAuth();
  const queryClient = useQueryClient();
  
  const [activeTab, setActiveTab] = useState('profile');
  const [showPassword, setShowPassword] = useState(false);
  
  // Profile form state
  const [profileForm, setProfileForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });

  // Password form state
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  // Preferences state
  const [preferences, setPreferences] = useState({
    theme: 'dark',
    language: 'en',
    currency: 'USD',
    emailNotifications: true,
    pushNotifications: true,
    marketingEmails: false,
    twoFactorEnabled: false,
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: (data: { name: string }) => api.auth.updateProfile(data),
    onSuccess: () => {
      toast.success('Profile updated successfully');
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update profile');
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      api.auth.changePassword(data),
    onSuccess: () => {
      toast.success('Password changed successfully');
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to change password');
    },
  });

  const handleSaveProfile = () => {
    updateProfileMutation.mutate({ name: profileForm.name });
  };

  const handleChangePassword = () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    if (passwordForm.newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    changePasswordMutation.mutate({
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword,
    });
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Lock },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'preferences', label: 'Preferences', icon: Globe },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-display font-bold text-white flex items-center gap-3">
          <SettingsIcon className="h-7 w-7 text-gold-400" />
          Settings
        </h1>
        <p className="text-gray-400 mt-1">Manage your account settings and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar Navigation */}
        <div className="lg:col-span-1">
          <DashboardCard noPadding>
            <nav className="p-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left',
                    activeTab === tab.id
                      ? 'bg-gold-500/10 text-gold-400'
                      : 'text-gray-400 hover:bg-white/5 hover:text-white'
                  )}
                >
                  <tab.icon className="h-5 w-5" />
                  <span className="font-medium">{tab.label}</span>
                  <ChevronRight className={cn(
                    'h-4 w-4 ml-auto transition-transform',
                    activeTab === tab.id && 'rotate-90'
                  )} />
                </button>
              ))}
            </nav>
          </DashboardCard>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <DashboardCard title="Profile Information" icon={<User className="h-5 w-5" />}>
              <div className="space-y-6">
                {/* Avatar */}
                <div className="flex items-center gap-4">
                  <div className="h-20 w-20 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-black text-2xl font-bold">
                    {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{user?.name}</h3>
                    <p className="text-gray-400">{user?.email}</p>
                    <p className="text-xs text-gray-500 mt-1">Member since {new Date(user?.createdAt || Date.now()).toLocaleDateString()}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-gray-300">Full Name</Label>
                    <Input
                      value={profileForm.name}
                      onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                      className="bg-white/5 border-white/10 focus:border-gold-500/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-gray-300">Email</Label>
                    <Input
                      value={profileForm.email}
                      disabled
                      className="bg-white/5 border-white/10 opacity-50"
                    />
                  </div>
                </div>

                <Button
                  onClick={handleSaveProfile}
                  disabled={updateProfileMutation.isPending}
                  className="bg-gold-500 hover:bg-gold-400 text-black"
                >
                  {updateProfileMutation.isPending ? (
                    <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...</>
                  ) : (
                    <><Save className="h-4 w-4 mr-2" /> Save Changes</>
                  )}
                </Button>
              </div>
            </DashboardCard>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <>
              <DashboardCard title="Change Password" icon={<Lock className="h-5 w-5" />}>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-gray-300">Current Password</Label>
                    <div className="relative">
                      <Input
                        type={showPassword ? 'text' : 'password'}
                        value={passwordForm.currentPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                        className="bg-white/5 border-white/10 focus:border-gold-500/50 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-gray-300">New Password</Label>
                      <Input
                        type="password"
                        value={passwordForm.newPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                        className="bg-white/5 border-white/10 focus:border-gold-500/50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-gray-300">Confirm Password</Label>
                      <Input
                        type="password"
                        value={passwordForm.confirmPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                        className="bg-white/5 border-white/10 focus:border-gold-500/50"
                      />
                    </div>
                  </div>

                  <Button
                    onClick={handleChangePassword}
                    disabled={changePasswordMutation.isPending || !passwordForm.currentPassword || !passwordForm.newPassword}
                    className="bg-gold-500 hover:bg-gold-400 text-black"
                  >
                    {changePasswordMutation.isPending ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Updating...</>
                    ) : (
                      'Update Password'
                    )}
                  </Button>
                </div>
              </DashboardCard>

              <DashboardCard title="Two-Factor Authentication" icon={<Shield className="h-5 w-5" />} glowColor="emerald">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-white">2FA Status</h3>
                    <p className="text-sm text-gray-400 mt-1">
                      Add an extra layer of security to your account
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={cn(
                      'px-2 py-1 text-xs font-medium rounded-full',
                      preferences.twoFactorEnabled
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : 'bg-red-500/10 text-red-400'
                    )}>
                      {preferences.twoFactorEnabled ? 'Enabled' : 'Disabled'}
                    </span>
                    <Button variant="outline" size="sm" className="border-white/10 hover:bg-white/5">
                      {preferences.twoFactorEnabled ? 'Manage' : 'Enable'}
                    </Button>
                  </div>
                </div>
              </DashboardCard>

              <DashboardCard title="Danger Zone" glowColor="red">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-red-400">Delete Account</h3>
                    <p className="text-sm text-gray-400 mt-1">
                      Permanently delete your account and all data
                    </p>
                  </div>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" size="sm" className="border-red-500/30 text-red-400 hover:bg-red-500/10">
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete Account
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent className="bg-[#1a1a2e] border-white/10">
                      <AlertDialogHeader>
                        <AlertDialogTitle className="text-white">Are you sure?</AlertDialogTitle>
                        <AlertDialogDescription className="text-gray-400">
                          This action cannot be undone. This will permanently delete your account and remove all your data from our servers.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel className="bg-white/5 border-white/10 hover:bg-white/10">Cancel</AlertDialogCancel>
                        <AlertDialogAction className="bg-red-500 hover:bg-red-600">Delete Account</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </DashboardCard>
            </>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <DashboardCard title="Notification Preferences" icon={<Bell className="h-5 w-5" />}>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="font-medium text-white">Email Notifications</p>
                      <p className="text-sm text-gray-400">Receive alerts via email</p>
                    </div>
                  </div>
                  <Switch
                    checked={preferences.emailNotifications}
                    onCheckedChange={(v) => setPreferences({ ...preferences, emailNotifications: v })}
                  />
                </div>

                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                  <div className="flex items-center gap-3">
                    <Smartphone className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="font-medium text-white">Push Notifications</p>
                      <p className="text-sm text-gray-400">Receive alerts on your device</p>
                    </div>
                  </div>
                  <Switch
                    checked={preferences.pushNotifications}
                    onCheckedChange={(v) => setPreferences({ ...preferences, pushNotifications: v })}
                  />
                </div>

                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="font-medium text-white">Marketing Emails</p>
                      <p className="text-sm text-gray-400">Receive news and promotions</p>
                    </div>
                  </div>
                  <Switch
                    checked={preferences.marketingEmails}
                    onCheckedChange={(v) => setPreferences({ ...preferences, marketingEmails: v })}
                  />
                </div>
              </div>
            </DashboardCard>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <DashboardCard title="Display Preferences" icon={<Globe className="h-5 w-5" />}>
              <div className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-gray-300">Theme</Label>
                    <Select value={preferences.theme} onValueChange={(v) => setPreferences({ ...preferences, theme: v })}>
                      <SelectTrigger className="bg-white/5 border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#1a1a2e] border-white/10">
                        <SelectItem value="dark">
                          <div className="flex items-center gap-2">
                            <Moon className="h-4 w-4" />
                            <span>Dark</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="light">
                          <div className="flex items-center gap-2">
                            <Sun className="h-4 w-4" />
                            <span>Light</span>
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-300">Currency</Label>
                    <Select value={preferences.currency} onValueChange={(v) => setPreferences({ ...preferences, currency: v })}>
                      <SelectTrigger className="bg-white/5 border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#1a1a2e] border-white/10">
                        <SelectItem value="USD">USD ($)</SelectItem>
                        <SelectItem value="EUR">EUR (€)</SelectItem>
                        <SelectItem value="GBP">GBP (£)</SelectItem>
                        <SelectItem value="BTC">BTC (₿)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-300">Language</Label>
                    <Select value={preferences.language} onValueChange={(v) => setPreferences({ ...preferences, language: v })}>
                      <SelectTrigger className="bg-white/5 border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#1a1a2e] border-white/10">
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="es">Español</SelectItem>
                        <SelectItem value="fr">Français</SelectItem>
                        <SelectItem value="de">Deutsch</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button className="bg-gold-500 hover:bg-gold-400 text-black">
                  <Save className="h-4 w-4 mr-2" />
                  Save Preferences
                </Button>
              </div>
            </DashboardCard>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
