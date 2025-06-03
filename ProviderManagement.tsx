import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Badge } from '../ui/badge';
import { providerAPI } from '../../lib/api';
import { useAuth } from '../../hooks/useAuth';

interface ProviderAccount {
  id: string;
  provider_id: string;
  account_name: string;
  token_limit: number;
  token_used: number;
  reset_date: string | null;
  status: string;
}

interface Provider {
  id: string;
  name: string;
  api_endpoint: string;
  auth_type: string;
  competencies: Record<string, number>;
  status: string;
  accounts: ProviderAccount[];
}

export default function ProviderManagement() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [newAccount, setNewAccount] = useState({
    account_name: '',
    api_key: '',
    token_limit: '1000',
    reset_date: '',
  });
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    if (user.role !== 'admin') {
      navigate('/dashboard');
      return;
    }

    fetchProviders();
  }, [user, navigate]);

  const fetchProviders = async () => {
    setLoading(true);
    try {
      const response = await providerAPI.getProviders();
      setProviders(response.data.providers);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch providers');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedProvider) {
      setError('Please select a provider');
      return;
    }

    try {
      await providerAPI.addAccount(selectedProvider, {
        account_name: newAccount.account_name,
        auth_credentials: JSON.stringify({ api_key: newAccount.api_key }),
        token_limit: parseInt(newAccount.token_limit),
        reset_date: newAccount.reset_date ? new Date(newAccount.reset_date).toISOString() : null,
      });
      
      // Reset form and refresh providers
      setNewAccount({
        account_name: '',
        api_key: '',
        token_limit: '1000',
        reset_date: '',
      });
      setSelectedProvider('');
      setShowAddAccount(false);
      fetchProviders();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to add account');
    }
  };

  const handleToggleAccountStatus = async (accountId: string, currentStatus: string) => {
    try {
      const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
      await providerAPI.updateAccountStatus(accountId, { status: newStatus });
      fetchProviders();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update account status');
    }
  };

  const handleTestConnection = async (providerId: string, accountId: string) => {
    try {
      const response = await providerAPI.testProvider(providerId, { account_id: accountId });
      if (response.data.success) {
        alert('Connection successful!');
      } else {
        alert(`Connection failed: ${response.data.message}`);
      }
    } catch (err: any) {
      alert(`Connection failed: ${err.response?.data?.error || 'Unknown error'}`);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  const getTokenUsagePercentage = (used: number, limit: number) => {
    if (limit === 0) return 0;
    return Math.min(100, Math.round((used / limit) * 100));
  };

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">AI Provider Management</h1>
        <Button onClick={() => setShowAddAccount(!showAddAccount)}>
          {showAddAccount ? 'Cancel' : 'Add Provider Account'}
        </Button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {showAddAccount && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Add Provider Account</CardTitle>
            <CardDescription>
              Add a new account for an AI provider to use in the system.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddAccount} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="provider">Provider</Label>
                <Select
                  value={selectedProvider}
                  onValueChange={setSelectedProvider}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {providers.map((provider) => (
                      <SelectItem key={provider.id} value={provider.id}>
                        {provider.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="account_name">Account Name</Label>
                <Input
                  id="account_name"
                  value={newAccount.account_name}
                  onChange={(e) => setNewAccount({ ...newAccount, account_name: e.target.value })}
                  placeholder="e.g., Primary GPT Account"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="api_key">API Key</Label>
                <Input
                  id="api_key"
                  type="password"
                  value={newAccount.api_key}
                  onChange={(e) => setNewAccount({ ...newAccount, api_key: e.target.value })}
                  placeholder="Enter API key"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="token_limit">Monthly Token Limit</Label>
                <Input
                  id="token_limit"
                  type="number"
                  value={newAccount.token_limit}
                  onChange={(e) => setNewAccount({ ...newAccount, token_limit: e.target.value })}
                  placeholder="e.g., 1000"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="reset_date">Reset Date (Optional)</Label>
                <Input
                  id="reset_date"
                  type="date"
                  value={newAccount.reset_date}
                  onChange={(e) => setNewAccount({ ...newAccount, reset_date: e.target.value })}
                  placeholder="When token count resets"
                />
              </div>

              <Button type="submit" className="w-full">Add Account</Button>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="text-center py-4">Loading providers...</div>
      ) : providers.length === 0 ? (
        <div className="text-center py-4">
          No providers found. Please add providers to the system.
        </div>
      ) : (
        providers.map((provider) => (
          <Card key={provider.id} className="mb-6">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>{provider.name}</CardTitle>
                  <CardDescription>
                    Endpoint: {provider.api_endpoint} | Auth Type: {provider.auth_type}
                  </CardDescription>
                </div>
                <Badge
                  variant={provider.status === 'active' ? 'default' : 'secondary'}
                >
                  {provider.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <h3 className="text-lg font-medium">Competencies</h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  {Object.entries(provider.competencies).map(([type, score]) => (
                    <Badge key={type} variant="outline" className="bg-blue-50">
                      {type}: {score}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-2">Accounts</h3>
                {provider.accounts.length === 0 ? (
                  <div className="text-center py-4 bg-gray-50 rounded-md">
                    No accounts configured for this provider.
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Account Name</TableHead>
                        <TableHead>Token Usage</TableHead>
                        <TableHead>Reset Date</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {provider.accounts.map((account) => (
                        <TableRow key={account.id}>
                          <TableCell className="font-medium">{account.account_name}</TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <div className="w-full bg-gray-200 rounded-full h-2.5">
                                <div
                                  className="bg-blue-600 h-2.5 rounded-full"
                                  style={{ width: `${getTokenUsagePercentage(account.token_used, account.token_limit)}%` }}
                                ></div>
                              </div>
                              <span className="text-xs whitespace-nowrap">
                                {account.token_used} / {account.token_limit}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>{formatDate(account.reset_date)}</TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Switch
                                checked={account.status === 'active'}
                                onCheckedChange={() => handleToggleAccountStatus(account.id, account.status)}
                              />
                              <span>{account.status}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleTestConnection(provider.id, account.id)}
                            >
                              Test Connection
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}
