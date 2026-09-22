import React, { useState } from 'react';
import { userAPI } from '@/services/fieldmind-api';

export default function ProfilePage() {
  const [profile, setProfile] = useState({
    name: 'John Doe',
    email: 'john@example.com',
    role: 'Data Analyst',
    bio: 'Passionate about data science and analytics',
  });

  return (
    <div className="p-8 space-y-8">
      <div className="page-header">
        <h1 className="page-title">Profile</h1>
        <p className="page-subtitle">Manage your personal information</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar */}
        <div className="card p-6 text-center h-fit">
          <div className="w-32 h-32 bg-[#27768A] rounded-full mx-auto mb-4 flex items-center justify-center text-white text-4xl font-bold">
            {profile.name.split(' ').map(n => n[0]).join('')}
          </div>
          <h2 className="text-xl font-bold mb-1">{profile.name}</h2>
          <p className="text-gray-600 mb-4">{profile.role}</p>
          <button className="w-full py-2 border rounded-lg hover:bg-gray-50 mb-2">Change Photo</button>
          <button className="w-full py-2 text-red-600 hover:bg-red-50 rounded-lg">Delete Account</button>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-6">Personal Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Full Name</label>
                <input type="text" value={profile.name} onChange={(e) => setProfile({...profile, name: e.target.value})} className="w-full p-3 border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Email</label>
                <input type="email" value={profile.email} onChange={(e) => setProfile({...profile, email: e.target.value})} className="w-full p-3 border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Role</label>
                <input type="text" value={profile.role} onChange={(e) => setProfile({...profile, role: e.target.value})} className="w-full p-3 border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Bio</label>
                <textarea value={profile.bio} onChange={(e) => setProfile({...profile, bio: e.target.value})} className="w-full p-3 border rounded-lg" rows={3} />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button className="px-6 py-2 border rounded-lg hover:bg-gray-50">Cancel</button>
              <button className="px-6 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E]">Save Changes</button>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-6">Activity Stats</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-[#27768A]">42</div>
                <div className="text-sm text-gray-600 mt-1">Projects</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-[#748D44]">156</div>
                <div className="text-sm text-gray-600 mt-1">Workflows</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-[#F8B042]">89</div>
                <div className="text-sm text-gray-600 mt-1">Assets</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
