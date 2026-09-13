import React, { useState } from 'react';
import { userAPI, teamAPI } from '@/services/fieldmind-api';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    notifications: true,
    darkMode: false,
    autoSave: true,
  });

  return (
    <div className="p-8 space-y-8">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Manage your account preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar */}
        <div className="card p-4 h-fit">
          <nav className="space-y-1">
            {['Profile', 'Account', 'Preferences', 'Notifications', 'Security'].map((item) => (
              <button
                key={item}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  item === 'Preferences' ? 'bg-[#27768A] text-white' : 'hover:bg-gray-100'
                }`}
              >
                {item}
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-6">Preferences</h3>

            <div className="space-y-6">
              <div className="flex items-center justify-between pb-6 border-b">
                <div>
                  <div className="font-medium">Email Notifications</div>
                  <div className="text-sm text-gray-600">Receive email updates</div>
                </div>
                <button
                  onClick={() => setSettings({...settings, notifications: !settings.notifications})}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.notifications ? 'bg-[#27768A]' : 'bg-gray-200'
                  }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.notifications ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              <div className="flex items-center justify-between pb-6 border-b">
                <div>
                  <div className="font-medium">Dark Mode</div>
                  <div className="text-sm text-gray-600">Use dark theme</div>
                </div>
                <button
                  onClick={() => setSettings({...settings, darkMode: !settings.darkMode})}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.darkMode ? 'bg-[#27768A]' : 'bg-gray-200'
                  }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.darkMode ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Auto Save</div>
                  <div className="text-sm text-gray-600">Automatically save changes</div>
                </div>
                <button
                  onClick={() => setSettings({...settings, autoSave: !settings.autoSave})}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.autoSave ? 'bg-[#27768A]' : 'bg-gray-200'
                  }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.autoSave ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </div>
            </div>

            <div className="mt-8 flex justify-end gap-3">
              <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button className="px-4 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E] transition-colors">
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
