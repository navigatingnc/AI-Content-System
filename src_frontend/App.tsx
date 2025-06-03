import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import LoginPage from './components/auth/LoginPage';
import TaskDashboard from './components/tasks/TaskDashboard';
import TaskSubmissionForm from './components/tasks/TaskSubmissionForm';
import TaskDetailView from './components/tasks/TaskDetailView';

// Protected route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            
            <Route path="/" element={
              <ProtectedRoute>
                <Navigate to="/dashboard" replace />
              </ProtectedRoute>
            } />
            
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <TaskDashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/tasks/new" element={
              <ProtectedRoute>
                <TaskSubmissionForm />
              </ProtectedRoute>
            } />
            
            <Route path="/tasks/:taskId" element={
              <ProtectedRoute>
                <TaskDetailView />
              </ProtectedRoute>
            } />
            
            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
