import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { User, Calendar, Shield, Edit } from 'lucide-react';
import api from '../utils/api';

export default function Profile() {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [achRes, catRes] = await Promise.all([
        api.get('/achievements?limit=1000'),
        api.get('/categories')
      ]);
      const achievements = achRes.data.achievements;
      setStats({
        total: achievements.length,
        completed: achievements.filter(a => a.status === 'completed').length,
        inProgress: achievements.filter(a => a.status === 'in_progress').length,
        categories: catRes.data.categories.length,
        memberSince: user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A',
        lastLogin: user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Profile</h1>
        <p className="text-gray-600 mt-1">Manage your account settings</p>
      </div>

      <div className="card">
        <div className="flex items-center space-x-4">
          <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center">
            <User className="h-10 w-10 text-primary-600" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-800">{user?.username}</h2>
            <div className="flex items-center space-x-1 text-gray-600 mt-1">
              <User className="h-4 w-4" />
              <span>Personal account</span>
            </div>
          </div>
          <button className="btn btn-secondary flex items-center space-x-2">
            <Edit className="h-4 w-4" />
            <span>Edit Profile</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
              <Shield className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-gray-600 text-sm">Total</p>
              <p className="text-2xl font-bold text-gray-800">{stats?.total || 0}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
              <Shield className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-gray-600 text-sm">Completed</p>
              <p className="text-2xl font-bold text-green-600">{stats?.completed || 0}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-yellow-100 flex items-center justify-center">
              <Shield className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-gray-600 text-sm">In Progress</p>
              <p className="text-2xl font-bold text-yellow-600">{stats?.inProgress || 0}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <User className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-gray-600 text-sm">Categories</p>
              <p className="text-2xl font-bold text-purple-600">{stats?.categories || 0}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Account Details</h2>
        <div className="space-y-4">
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <User className="h-5 w-5 text-gray-500" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Username</p>
              <p className="font-medium text-gray-800">{user?.username}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <Calendar className="h-5 w-5 text-gray-500" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Member Since</p>
              <p className="font-medium text-gray-800">{stats?.memberSince}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <Shield className="h-5 w-5 text-gray-500" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Last Login</p>
              <p className="font-medium text-gray-800">{stats?.lastLogin}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card border-l-4 border-red-500">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Danger Zone</h2>
        <p className="text-gray-600 mb-4">
          These actions are irreversible. Please be certain.
        </p>
        <button
          onClick={logout}
          className="btn btn-secondary"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
}
