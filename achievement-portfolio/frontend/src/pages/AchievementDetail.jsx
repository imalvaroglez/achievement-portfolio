import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Edit, Trash2, Plus, CheckCircle2 } from 'lucide-react';
import api from '../utils/api';

export default function AchievementDetail() {
  const { id } = useParams();
  const [achievement, setAchievement] = useState(null);
  const [milestones, setMilestones] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAchievement();
  }, [id]);

  const loadAchievement = async () => {
    try {
      const response = await api.get(`/achievements/${id}`);
      setAchievement(response.data.achievement);
      setMilestones(response.data.milestones);
    } catch (error) {
      console.error('Error loading achievement:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteAchievement = async () => {
    if (!confirm('Are you sure you want to delete this achievement?')) return;
    
    try {
      await api.delete(`/achievements/${id}`);
      window.location.href = '/';
    } catch (error) {
      console.error('Error deleting achievement:', error);
    }
  };

  const addMilestone = async () => {
    const title = prompt('Enter milestone title:');
    if (!title) return;

    try {
      const response = await api.post(`/achievements/${id}/milestones`, { title });
      setMilestones([...milestones, response.data.milestone]);
    } catch (error) {
      console.error('Error adding milestone:', error);
    }
  };

  const toggleMilestone = async (milestone) => {
    const completed = milestone.completed_at ? null : new Date().toISOString();
    
    try {
      const response = await api.put(`/achievements/${id}/milestones/${milestone.id}`, {
        ...milestone,
        completed_at: completed
      });
      setMilestones(milestones.map(m => 
        m.id === milestone.id ? response.data.milestone : m
      ));
    } catch (error) {
      console.error('Error updating milestone:', error);
    }
  };

  const deleteMilestone = async (milestoneId) => {
    try {
      await api.delete(`/achievements/${id}/milestones/${milestoneId}`);
      setMilestones(milestones.filter(m => m.id !== milestoneId));
    } catch (error) {
      console.error('Error deleting milestone:', error);
    }
  };

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
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${styles[status] || styles.pending}`}>
        {labels[status] || status}
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

  if (!achievement) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Achievement not found</p>
        <Link to="/" className="btn btn-secondary mt-4 inline-block">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <Link to="/" className="inline-flex items-center text-gray-600 hover:text-primary-600 mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Link>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-800">{achievement.title}</h1>
            <div className="flex items-center space-x-3 mt-2">
              {getStatusBadge(achievement.status)}
            </div>
          </div>
          <div className="flex space-x-2">
            <button className="btn btn-secondary flex items-center space-x-1">
              <Edit className="h-4 w-4" />
              <span>Edit</span>
            </button>
            <button
              onClick={deleteAchievement}
              className="btn btn-danger flex items-center space-x-1"
            >
              <Trash2 className="h-4 w-4" />
              <span>Delete</span>
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {achievement.description && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-800 mb-3">Description</h2>
              <p className="text-gray-700 whitespace-pre-wrap">{achievement.description}</p>
            </div>
          )}

          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-800">Milestones</h2>
              <button
                onClick={addMilestone}
                className="btn btn-primary flex items-center space-x-1"
              >
                <Plus className="h-4 w-4" />
                <span>Add</span>
              </button>
            </div>
            {milestones.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No milestones yet</p>
            ) : (
              <div className="space-y-3">
                {milestones.map((milestone) => (
                  <div
                    key={milestone.id}
                    className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <button
                      onClick={() => toggleMilestone(milestone)}
                      className={`mt-1 ${
                        milestone.completed_at ? 'text-green-600' : 'text-gray-400 hover:text-gray-600'
                      }`}
                    >
                      {milestone.completed_at ? (
                        <CheckCircle2 className="h-5 w-5" />
                      ) : (
                        <div className="w-5 h-5 border-2 border-current rounded" />
                      )}
                    </button>
                    <div className="flex-1">
                      <p className={`font-medium ${milestone.completed_at ? 'line-through text-gray-500' : 'text-gray-800'}`}>
                        {milestone.title}
                      </p>
                      {milestone.description && (
                        <p className="text-sm text-gray-600 mt-1">{milestone.description}</p>
                      )}
                      {milestone.completed_at && (
                        <p className="text-xs text-green-600 mt-1">
                          Completed: {new Date(milestone.completed_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => deleteMilestone(milestone.id)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Details</h2>
            <div className="space-y-3">
              {achievement.date_achieved && (
                <div>
                  <p className="text-sm text-gray-500">Date Achieved</p>
                  <p className="text-gray-800 font-medium">
                    {new Date(achievement.date_achieved).toLocaleDateString()}
                  </p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-500">Created</p>
                <p className="text-gray-800 font-medium">
                  {new Date(achievement.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>

          {milestones.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-800 mb-3">Progress</h2>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">
                  {milestones.filter(m => m.completed_at).length} of {milestones.length} completed
                </span>
                <span className="text-sm font-semibold text-primary-600">
                  {Math.round((milestones.filter(m => m.completed_at).length / milestones.length) * 100)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${(milestones.filter(m => m.completed_at).length / milestones.length) * 100}%`
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
