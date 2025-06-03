import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Textarea } from '../ui/textarea';
import { taskAPI } from '../../lib/api';
import { useAuth } from '../../hooks/useAuth';

const taskTypes = [
  { value: 'image', label: 'Image Generation (GPT)' },
  { value: 'code_project', label: 'Project Code (MANUS)' },
  { value: 'code', label: 'Alternative Code (Claude)' },
  { value: 'prompt', label: 'Prompt Generation (Grok/Gemini/Perplexity)' },
  { value: 'meeting', label: 'Meeting Tracking (Lindy.ai)' },
  { value: 'people_image', label: 'People Images (Lumenor)' },
];

export default function TaskSubmissionForm() {
  const [formData, setFormData] = useState({
    title: '',
    task_type: '',
    priority: '3',
    description_data: {
      prompt: '',
      language: 'python',
      size: '1024x1024',
    },
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleDescriptionChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      description_data: {
        ...prev.description_data,
        [name]: value,
      },
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await taskAPI.createTask(formData);
      setSuccess(true);
      setFormData({
        title: '',
        task_type: '',
        priority: '3',
        description_data: {
          prompt: '',
          language: 'python',
          size: '1024x1024',
        },
      });
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create task');
    } finally {
      setLoading(false);
    }
  };

  // Determine which additional fields to show based on task type
  const renderAdditionalFields = () => {
    switch (formData.task_type) {
      case 'image':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="prompt">Image Prompt</Label>
              <Textarea
                id="prompt"
                name="prompt"
                placeholder="Describe the image you want to generate"
                value={formData.description_data.prompt}
                onChange={handleDescriptionChange}
                rows={4}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="size">Image Size</Label>
              <Select
                value={formData.description_data.size}
                onValueChange={(value) => 
                  setFormData((prev) => ({
                    ...prev,
                    description_data: {
                      ...prev.description_data,
                      size: value,
                    },
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select size" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1024x1024">1024x1024</SelectItem>
                  <SelectItem value="512x512">512x512</SelectItem>
                  <SelectItem value="256x256">256x256</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        );
      case 'code':
      case 'code_project':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="prompt">Code Description</Label>
              <Textarea
                id="prompt"
                name="prompt"
                placeholder="Describe the code you want to generate"
                value={formData.description_data.prompt}
                onChange={handleDescriptionChange}
                rows={4}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="language">Programming Language</Label>
              <Select
                value={formData.description_data.language}
                onValueChange={(value) => 
                  setFormData((prev) => ({
                    ...prev,
                    description_data: {
                      ...prev.description_data,
                      language: value,
                    },
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="python">Python</SelectItem>
                  <SelectItem value="javascript">JavaScript</SelectItem>
                  <SelectItem value="typescript">TypeScript</SelectItem>
                  <SelectItem value="java">Java</SelectItem>
                  <SelectItem value="csharp">C#</SelectItem>
                  <SelectItem value="cpp">C++</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        );
      case 'prompt':
      case 'meeting':
      case 'people_image':
      default:
        return (
          <div className="space-y-2">
            <Label htmlFor="prompt">Description</Label>
            <Textarea
              id="prompt"
              name="prompt"
              placeholder="Provide details for your request"
              value={formData.description_data.prompt}
              onChange={handleDescriptionChange}
              rows={4}
              required
            />
          </div>
        );
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Create New Task</CardTitle>
        <CardDescription>
          Submit a new task to be processed by the AI content generation system.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Task Title</Label>
            <Input
              id="title"
              name="title"
              placeholder="Enter a title for your task"
              value={formData.title}
              onChange={handleChange}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="task_type">Task Type</Label>
            <Select
              value={formData.task_type}
              onValueChange={(value) => handleSelectChange('task_type', value)}
              required
            >
              <SelectTrigger>
                <SelectValue placeholder="Select task type" />
              </SelectTrigger>
              <SelectContent>
                {taskTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="priority">Priority</Label>
            <Select
              value={formData.priority}
              onValueChange={(value) => handleSelectChange('priority', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Low</SelectItem>
                <SelectItem value="2">Medium-Low</SelectItem>
                <SelectItem value="3">Medium</SelectItem>
                <SelectItem value="4">Medium-High</SelectItem>
                <SelectItem value="5">High</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {formData.task_type && renderAdditionalFields()}

          {error && (
            <div className="text-sm font-medium text-red-500">
              {error}
            </div>
          )}

          {success && (
            <div className="text-sm font-medium text-green-500">
              Task created successfully! Redirecting to dashboard...
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Creating Task...' : 'Create Task'}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="flex justify-center">
        <Button variant="outline" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
      </CardFooter>
    </Card>
  );
}
