import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { taskAPI } from '../../lib/api';
import { useAuth } from '../../hooks/useAuth';

interface Content {
  id: string;
  title: string;
  content_type: string;
  file_path: string;
  status: string;
  created_at: string;
}

interface Assignment {
  id: string;
  provider_id: string;
  provider_name: string;
  status: string;
  tokens_used: number;
  created_at: string;
  updated_at: string;
}

interface TaskDetail {
  task: {
    id: string;
    title: string;
    task_type: string;
    priority: number;
    status: string;
    created_at: string;
    started_at: string | null;
    completed_at: string | null;
  };
  assignments: Assignment[];
  content: Content[];
}

export default function TaskDetailView() {
  const { taskId } = useParams<{ taskId: string }>();
  const [taskDetail, setTaskDetail] = useState<TaskDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    if (taskId) {
      fetchTaskDetail(taskId);
    }
  }, [taskId, user, navigate]);

  const fetchTaskDetail = async (id: string) => {
    setLoading(true);
    try {
      const response = await taskAPI.getTask(id);
      setTaskDetail(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch task details');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  const handleCancelTask = async () => {
    if (!taskId) return;
    
    try {
      await taskAPI.cancelTask(taskId);
      // Refresh task details after cancellation
      fetchTaskDetail(taskId);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to cancel task');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="outline" className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      case 'processing':
        return <Badge variant="outline" className="bg-blue-100 text-blue-800">Processing</Badge>;
      case 'completed':
        return <Badge variant="outline" className="bg-green-100 text-green-800">Completed</Badge>;
      case 'failed':
        return <Badge variant="outline" className="bg-red-100 text-red-800">Failed</Badge>;
      case 'cancelled':
        return <Badge variant="outline" className="bg-gray-100 text-gray-800">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const renderContentPreview = (content: Content) => {
    switch (content.content_type) {
      case 'image':
        return (
          <div className="mt-4">
            <img 
              src={`/api/content/file?path=${encodeURIComponent(content.file_path)}`} 
              alt={content.title}
              className="max-w-full h-auto rounded-md shadow-md"
            />
          </div>
        );
      case 'code':
        return (
          <div className="mt-4">
            <div className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-auto max-h-96">
              <pre>
                <code>
                  {/* Code content would be loaded here */}
                  Loading code content...
                </code>
              </pre>
            </div>
            <Button variant="outline" className="mt-2">
              <a 
                href={`/api/content/file?path=${encodeURIComponent(content.file_path)}`} 
                download
                className="no-underline"
              >
                Download Code File
              </a>
            </Button>
          </div>
        );
      case 'code_project':
        return (
          <div className="mt-4">
            <div className="bg-gray-100 p-4 rounded-md">
              <p>Project files are packaged as a ZIP archive.</p>
            </div>
            <Button variant="outline" className="mt-2">
              <a 
                href={`/api/content/file?path=${encodeURIComponent(content.file_path)}`} 
                download
                className="no-underline"
              >
                Download Project ZIP
              </a>
            </Button>
          </div>
        );
      default:
        return (
          <div className="mt-4">
            <div className="bg-gray-100 p-4 rounded-md">
              <p>Content preview not available for this type.</p>
            </div>
            <Button variant="outline" className="mt-2">
              <a 
                href={`/api/content/file?path=${encodeURIComponent(content.file_path)}`} 
                download
                className="no-underline"
              >
                Download Content
              </a>
            </Button>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center">Loading task details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <Button onClick={handleBackToDashboard}>Back to Dashboard</Button>
      </div>
    );
  }

  if (!taskDetail) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center">Task not found</div>
        <Button onClick={handleBackToDashboard} className="mt-4">Back to Dashboard</Button>
      </div>
    );
  }

  const { task, assignments, content } = taskDetail;

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Task Details</h1>
        <Button onClick={handleBackToDashboard}>Back to Dashboard</Button>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>{task.title}</CardTitle>
              <CardDescription>Type: {task.task_type}</CardDescription>
            </div>
            <div>{getStatusBadge(task.status)}</div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium">Created:</p>
              <p>{formatDate(task.created_at)}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Started:</p>
              <p>{formatDate(task.started_at)}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Completed:</p>
              <p>{formatDate(task.completed_at)}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Priority:</p>
              <p>{task.priority}</p>
            </div>
          </div>
        </CardContent>
        <CardFooter>
          {(task.status === 'pending' || task.status === 'processing') && (
            <Button variant="destructive" onClick={handleCancelTask}>
              Cancel Task
            </Button>
          )}
        </CardFooter>
      </Card>

      <Tabs defaultValue="content" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="assignments">AI Provider Assignments</TabsTrigger>
        </TabsList>
        
        <TabsContent value="content">
          {content.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-4">
                  No content generated yet.
                </div>
              </CardContent>
            </Card>
          ) : (
            content.map((item) => (
              <Card key={item.id} className="mb-4">
                <CardHeader>
                  <CardTitle>{item.title}</CardTitle>
                  <CardDescription>
                    Type: {item.content_type} | Status: {item.status}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {renderContentPreview(item)}
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
        
        <TabsContent value="assignments">
          {assignments.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-4">
                  No assignments yet.
                </div>
              </CardContent>
            </Card>
          ) : (
            assignments.map((assignment) => (
              <Card key={assignment.id} className="mb-4">
                <CardHeader>
                  <CardTitle>Assignment to {assignment.provider_name}</CardTitle>
                  <CardDescription>
                    Status: {assignment.status}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium">Created:</p>
                      <p>{formatDate(assignment.created_at)}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium">Updated:</p>
                      <p>{formatDate(assignment.updated_at)}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium">Tokens Used:</p>
                      <p>{assignment.tokens_used}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
