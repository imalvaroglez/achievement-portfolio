import { Link } from 'react-router-dom';
import { LogOut, Trophy, Folder, User, Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useState } from 'react';

export default function Navbar({ user }) {
  const { logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Trophy className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-800">Achievement Portfolio</span>
          </Link>

          <div className="hidden md:flex items-center space-x-6">
            <Link to="/" className="text-gray-700 hover:text-primary-600 transition-colors">
              Dashboard
            </Link>
            <Link to="/categories" className="text-gray-700 hover:text-primary-600 transition-colors">
              Categories
            </Link>
            <Link to="/profile" className="text-gray-700 hover:text-primary-600 transition-colors">
              Profile
            </Link>
            <div className="flex items-center space-x-2 border-l pl-6">
              <User className="h-5 w-5 text-gray-500" />
              <span className="text-gray-700">{user?.username}</span>
            </div>
            <button
              onClick={logout}
              className="flex items-center space-x-1 text-red-600 hover:text-red-700 transition-colors"
            >
              <LogOut className="h-5 w-5" />
              <span>Logout</span>
            </button>
          </div>

          <button
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t">
            <div className="flex flex-col space-y-4">
              <Link to="/" className="text-gray-700 hover:text-primary-600">
                Dashboard
              </Link>
              <Link to="/categories" className="text-gray-700 hover:text-primary-600">
                Categories
              </Link>
              <Link to="/profile" className="text-gray-700 hover:text-primary-600">
                Profile
              </Link>
              <div className="border-t pt-4">
                <div className="flex items-center space-x-2 mb-4">
                  <User className="h-5 w-5 text-gray-500" />
                  <span className="text-gray-700">{user?.username}</span>
                </div>
                <button
                  onClick={logout}
                  className="flex items-center space-x-1 text-red-600 hover:text-red-700"
                >
                  <LogOut className="h-5 w-5" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
