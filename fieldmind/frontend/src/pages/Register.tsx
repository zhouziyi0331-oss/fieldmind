import React from 'react';
import { authAPI } from '@/services/fieldmind-api';
import { useNavigate } from 'react-router-dom';

export default function RegisterPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#748D44] to-[#85A156] p-12 flex-col justify-between">
        <div>
          <h1 className="text-4xl font-bold text-white mb-4">Join FieldMind</h1>
          <p className="text-white/90 text-lg">Start your knowledge journey</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">Create Account</h2>
            <p className="mt-2 text-gray-600">Get started with FieldMind</p>
          </div>

          <form className="mt-8 space-y-6" onSubmit={(e) => { e.preventDefault(); navigate('/dashboard'); }}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                <input type="text" required className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#748D44] focus:border-transparent" placeholder="John Doe" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input type="email" required className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#748D44] focus:border-transparent" placeholder="you@example.com" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <input type="password" required className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#748D44] focus:border-transparent" placeholder="••••••••" />
              </div>
            </div>

            <button type="submit" className="w-full py-3 px-4 bg-[#748D44] text-white rounded-lg hover:bg-[#5C7136] transition-colors font-medium">
              Create Account
            </button>

            <div className="text-center">
              <span className="text-sm text-gray-600">Already have an account? </span>
              <button type="button" onClick={() => navigate('/login')} className="text-sm text-[#748D44] hover:text-[#5C7136] font-medium">Sign in</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
