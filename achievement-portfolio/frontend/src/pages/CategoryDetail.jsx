import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Plus, Edit, Trash2 } from 'lucide-react';
import api from '../utils/api';

export default function CategoryDetail() {
  const { id } = useParams();
  const [category, setCategory] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCategory();
  }, [id]);

  const loadCategory = async () => {
    try {
      const response = await api.get(`/categories/${id}`);
      setCategory(response.data.category);
      setAchievements(response.data.achievements);
    } catch (error) {
      console.error('Error loading category:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteAchievement = async (achievementId) => {
    if (!confirm('Are you sure you want to delete this achievement?')) return;
    
    try {
      await api.delete(`/achievements/${achievementId}`);
      setAchievements(achievements.filter(a => a.id !== achievementId));
    } catch (error) {
      console.error('Error deleting achievement:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!category) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Category not found</p>
        <Link to="/categories" className="btn btn-secondary mt-4 inline-block">
          Back to Categories
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/categories" className="text-gray-600 hover:text-primary-600">
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <div
            className="w-14 h-14 rounded-lg flex items-center justify-center text-white text-2xl"
            style={{ backgroundColor: category.color }}
          >
            <span>{category.icon?.[0] || '★'}</span>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-800">{category.name}</h1>
            <p className="text-gray-600">{category.description}</p>
          </div>
        </div>
        <button className="btn btn-primary flex items-center space-x-2">
          <Plus className="h-5 w-5" />
          <span>New Achievement</span>
        </button>
      </div>

      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">Total Achievements</p>
            <p className="text-2xl font-bold text-gray-800">{achievements.length}</p>
          </div>
          <div className="text-right">
            <p className="text-gray-600 text-sm">Completed</p>
            <p className="text-2xl font-bold text-green-600">
              {achievements.filter(a => a.status === 'completed').length}
            </p>
          </div>
        </div>
      </div>

      {achievements.length === 0 ? (
        <div className="text-center py-12 card">
          <Plus className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">No achievements yet</p>
          <p className="text-gray-500">Create your first achievement in this category!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {achievements.map((achievement) => (
            <div
              key={achievement.id}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      achievement.status === 'completed' ? 'bg-green-100 text-green-800' :
                      achievement.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {achievement.status === 'completed' ? 'Completed' :
                       achievement.status === 'in_progress' ? 'In Progress' : 'Pending'}
                    </span>
                  </div>
                  <Link
                    to={`/achievements/${achievement.id}`}
                    className="text-lg font-semibold text-gray-800 hover:text-primary-600"
                  >
                    {achievement.title}
                  </Link>
                  {achievement.description && (
                    <p className="text-gray-600 text-sm mt-1 line-clamp-2">
                      {achievement.description}
                    </p>
                  )}
                  {achievement.date_achieved && (
                    <p className="text-sm text-gray-500 mt-2">
                      Achieved: {new Date(achievement.date_achieved).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="flex space-x-1 ml-4">
                  <Link
                    to={`/achievements/${achievement.id}`}
                    className="p-2 text-gray-400 hover:text-primary-600 transition-colors"
                  >
                    <Edit className="h-4 w-4" />
                  </Link>
                  <button
                    onClick={() => deleteAchievement(achievement.id)}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
