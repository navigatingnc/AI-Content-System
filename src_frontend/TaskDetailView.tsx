import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { taskAPI } from '../../lib/api'; // Assuming api.ts is in ../../lib
import { useAuth } from '../../hooks/useAuth'; // Assuming useAuth is in ../../hooks

interface Content {
  id: string;
  title: string;
  content_type: string;
  file_path: string;
  content_data?: string; // For direct preview of text/code
  status: string;
  created_at: string;
}

interface Assignment {
  id: string;
  provider_id: string;
  provider_name: string; // Added this based on backend update
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
      const response = await taskAPI.getTask(id); // This should fetch TaskDetail structure
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
      fetchTaskDetail(taskId);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to cancel task');
    }
  };

  const getStatusBadge = (status: string) => {
    // ... (same as before)
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
    return new Date(dateString).toLocaleString();
  };

  // Moved renderContentPreview out to be a component or memoized function if it causes re-renders
  // For now, keeping it as a function within TaskDetailView, but it will re-declare on each render.
  // To use hooks like useState/useEffect, it must be a component or a custom hook.
  // So, we create a sub-component for rendering each content item's preview.

  const ContentItemPreview = ({ item }: { item: Content }) => {
    const [fetchedCode, setFetchedCode] = useState<string | null>(null);
    const [isFetchingCode, setIsFetchingCode] = useState(false);
    const [fetchError, setFetchError] = useState<string | null>(null);

    useEffect(() => {
      setFetchedCode(null);
      setIsFetchingCode(false);
      setFetchError(null);

      if (item.content_type === 'code' && item.content_data) {
        setFetchedCode(item.content_data);
      } else if (item.content_type === 'code' && item.file_path) {
        setIsFetchingCode(true);
        fetch(`/api/content/file?path=${encodeURIComponent(item.file_path)}`)
          .then(async response => {
            if (!response.ok) {
              const errorText = await response.text();
              try {
                const errorJson = JSON.parse(errorText);
                throw new Error(errorJson.error || errorJson.detail || `Failed to fetch code: ${response.statusText}`);
              } catch (e) {
                throw new Error(errorText && errorText.length < 200 ? errorText : `Failed to fetch code: ${response.statusText}`);
              }
            }
            return response.text();
          })
          .then(textData => {
            setFetchedCode(textData);
          })
          .catch(err => {
            console.error("Error fetching code content for item:", item.id, err);
            setFetchError(err.message || 'Unknown error fetching code.');
          })
          .finally(() => {
            setIsFetchingCode(false);
          });
      }
    }, [item.id, item.content_type, item.content_data, item.file_path]);

    switch (item.content_type) {
      case 'image':
        return (
          <div className="mt-4">
            {item.file_path && (
              <img
                src={`/api/content/file?path=${encodeURIComponent(item.file_path)}`}
                alt={item.title}
                className="max-w-full h-auto rounded-md shadow-md"
              />
            )}
          </div>
        );
      case 'code':
        let codeToDisplay: string;
        if (item.content_data && !isFetchingCode && !fetchError && fetchedCode === null) {
          // Primarily use content_data if available and no fetch operation has superseded it.
          codeToDisplay = item.content_data;
        } else if (isFetchingCode) {
          codeToDisplay = "Fetching code from file...";
        } else if (fetchError) {
          codeToDisplay = `Error: ${fetchError}`;
        } else if (fetchedCode !== null) {
          codeToDisplay = fetchedCode;
        } else if (!item.content_data && !item.file_path) {
          codeToDisplay = "No code content or file path available.";
        } else {
          codeToDisplay = "Loading code content...";
        }

        return (
          <div className="mt-4">
            <div className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-auto max-h-96">
              <pre><code>{codeToDisplay}</code></pre>
            </div>
            {item.file_path && (
              <Button variant="outline" className="mt-2">
                <a
                  href={`/api/content/file?path=${encodeURIComponent(item.file_path)}`}
                  download
                  className="no-underline"
                >
                  Download Code File
                </a>
              </Button>
            )}
          </div>
        );
      case 'code_project':
        return (
          <div className="mt-4">
            <div className="bg-gray-100 p-4 rounded-md">
              <p>Project files are packaged as a ZIP archive.</p>
            </div>
            {item.file_path && (
              <Button variant="outline" className="mt-2">
                <a
                  href={`/api/content/file?path=${encodeURIComponent(item.file_path)}`}
                  download
                  className="no-underline"
                >
                  Download Project ZIP
                </a>
              </Button>
            )}
          </div>
        );
      default:
        return (
          <div className="mt-4">
            <div className="bg-gray-100 p-4 rounded-md">
              <p>Content preview not available for this type.</p>
            </div>
            {item.file_path && (
              <Button variant="outline" className="mt-2">
                <a
                  href={`/api/content/file?path=${encodeURIComponent(item.file_path)}`}
                  download
                  className="no-underline"
                >
                  Download Content
                </a>
              </Button>
            )}
          </div>
        );
    }
  };


  if (loading) {
    return <div className="container mx-auto py-6 text-center">Loading task details...</div>;
  }

  if (error) {
    return (
      <div className="container mx-auto py-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>
        <Button onClick={handleBackToDashboard}>Back to Dashboard</Button>
      </div>
    );
  }

  if (!taskDetail) {
    return (
      <div className="container mx-auto py-6 text-center">
        Task not found
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
          {/* ... (task details grid - same as before) ... */}
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
            <Button variant="destructive" onClick={handleCancelTask}>Cancel Task</Button>
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
            <Card><CardContent className="pt-6 text-center py-4">No content generated yet.</CardContent></Card>
          ) : (
            content.map((item) => (
              <Card key={item.id} className="mb-4">
                <CardHeader>
                  <CardTitle>{item.title}</CardTitle>
                  <CardDescription>Type: {item.content_type} | Status: {item.status}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ContentItemPreview item={item} />
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
        
        <TabsContent value="assignments">
          {assignments.length === 0 ? (
            <Card><CardContent className="pt-6 text-center py-4">No assignments yet.</CardContent></Card>
          ) : (
            assignments.map((assignment) => (
              <Card key={assignment.id} className="mb-4">
                <CardHeader>
                  <CardTitle>Assignment to {assignment.provider_name}</CardTitle>
                  <CardDescription>Status: {assignment.status}</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* ... (assignment details grid - same as before) ... */}
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
