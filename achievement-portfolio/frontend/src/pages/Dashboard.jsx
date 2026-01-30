import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Trophy, Search, Filter, Calendar, Award } from 'lucide-react';
import api from '../utils/api';

export default function Dashboard() {
  const [achievements, setAchievements] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterCategory, setFilterCategory] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [achRes, catRes] = await Promise.all([
        api.get('/achievements'),
        api.get('/categories')
      ]);
      setAchievements(achRes.data.achievements);
      setCategories(catRes.data.categories);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredAchievements = achievements.filter((ach) => {
    const matchesSearch =
      ach.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ach.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = !filterStatus || ach.status === filterStatus;
    const matchesCategory = !filterCategory || ach.category_id === parseInt(filterCategory);
    return matchesSearch && matchesStatus && matchesCategory;
  });

  const getStatusBadge = (status) => {
    const styles = {
      completed: 'bg-green-100 text-green-800',
      in_progress: 'bg-yellow-100 text-yellow-800',
      pending: 'bg-gray-100 text-gray-800'
    };
    const labels = {
      completed: 'Completed',
      in_progress: 'In Progress',
      pending: 'Pending'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getDifficultyBadge = (difficulty) => {
    if (!difficulty) return null;
    const styles = {
      easy: 'bg-green-100 text-green-800',
      medium: 'bg-blue-100 text-blue-800',
      hard: 'bg-orange-100 text-orange-800',
      expert: 'bg-red-100 text-red-800'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[difficulty] || ''}`}>
        {difficulty}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">My Achievements</h1>
          <p className="text-gray-600 mt-1">Track and celebrate your accomplishments</p>
        </div>
        <button className="btn btn-primary mt-4 md:mt-0 flex items-center justify-center space-x-2">
          <Plus className="h-5 w-5" />
          <span>New Achievement</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total</p>
              <p className="text-2xl font-bold text-gray-800">{achievements.length}</p>
            </div>
            <Trophy className="h-8 w-8 text-primary-600" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Completed</p>
              <p className="text-2xl font-bold text-green-600">
                {achievements.filter((a) => a.status === 'completed').length}
              </p>
            </div>
            <Award className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">In Progress</p>
              <p className="text-2xl font-bold text-yellow-600">
                {achievements.filter((a) => a.status === 'in_progress').length}
              </p>
            </div>
            <Calendar className="h-8 w-8 text-yellow-600" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Categories</p>
              <p className="text-2xl font-bold text-blue-600">{categories.length}</p>
            </div>
            <Filter className="h-8 w-8 text-blue-600" />
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search achievements..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="input"
          >
            <option value="">All Status</option>
            <option value="completed">Completed</option>
            <option value="in_progress">In Progress</option>
            <option value="pending">Pending</option>
          </select>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="input"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {filteredAchievements.length === 0 ? (
        <div className="text-center py-12">
          <Trophy className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">No achievements found</p>
          <p className="text-gray-500">Create your first achievement to get started!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAchievements.map((achievement) => (
            <Link
              key={achievement.id}
              to={`/achievements/${achievement.id}`}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <span
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white"
                  style={{ backgroundColor: achievement.category_color }}
                >
                  <span className="text-lg">{achievement.category_icon?.[0] || '★'}</span>
                </span>
                <div className="flex space-x-2">
                  {getStatusBadge(achievement.status)}
                  {getDifficultyBadge(achievement.difficulty)}
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                {achievement.title}
              </h3>
              {achievement.description && (
                <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                  {achievement.description}
                </p>
              )}
              {achievement.date_achieved && (
                <p className="text-sm text-gray-500">
                  Achieved: {new Date(achievement.date_achieved).toLocaleDateString()}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
