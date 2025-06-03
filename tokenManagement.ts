import { providerAPI } from '../../lib/api';

// Token management service
export const TokenManagementService = {
  // Check if a provider account has sufficient tokens for a task
  checkTokenAvailability: async (providerId, estimatedTokens) => {
    try {
      const response = await providerAPI.getProviderStatus(providerId);
      const accounts = response.data.accounts.filter(account => account.status === 'active');
      
      // Find accounts with sufficient tokens
      const availableAccounts = accounts.filter(
        account => (account.token_limit - account.token_used) >= estimatedTokens
      );
      
      if (availableAccounts.length === 0) {
        return { available: false, message: 'No accounts with sufficient tokens' };
      }
      
      // Sort by available tokens (descending)
      availableAccounts.sort((a, b) => 
        (b.token_limit - b.token_used) - (a.token_limit - a.token_used)
      );
      
      return { 
        available: true, 
        accountId: availableAccounts[0].id,
        availableTokens: availableAccounts[0].token_limit - availableAccounts[0].token_used
      };
    } catch (error) {
      console.error('Error checking token availability:', error);
      return { available: false, message: 'Error checking token availability' };
    }
  },
  
  // Record token usage for a task
  recordTokenUsage: async (accountId, tokensUsed) => {
    try {
      await providerAPI.updateTokenUsage(accountId, { tokens_used: tokensUsed });
      return { success: true };
    } catch (error) {
      console.error('Error recording token usage:', error);
      return { success: false, message: 'Error recording token usage' };
    }
  },
  
  // Reset token usage for accounts that have reached their reset date
  checkAndResetTokens: async () => {
    try {
      const response = await providerAPI.resetExpiredTokens();
      return { 
        success: true, 
        resetCount: response.data.reset_count,
        accounts: response.data.accounts 
      };
    } catch (error) {
      console.error('Error resetting tokens:', error);
      return { success: false, message: 'Error resetting tokens' };
    }
  },
  
  // Find fallback provider for a task when primary provider is unavailable
  findFallbackProvider: async (taskType, primaryProviderId) => {
    try {
      const response = await providerAPI.getFallbackProviders(taskType, primaryProviderId);
      
      if (!response.data.providers || response.data.providers.length === 0) {
        return { found: false, message: 'No fallback providers available' };
      }
      
      // Return the first fallback provider with available tokens
      const fallbackProvider = response.data.providers.find(
        provider => provider.has_available_tokens
      );
      
      if (!fallbackProvider) {
        return { found: false, message: 'No fallback providers with available tokens' };
      }
      
      return { 
        found: true, 
        providerId: fallbackProvider.id,
        accountId: fallbackProvider.available_account_id,
        competencyScore: fallbackProvider.competency_score
      };
    } catch (error) {
      console.error('Error finding fallback provider:', error);
      return { found: false, message: 'Error finding fallback provider' };
    }
  },
  
  // Estimate token usage for a task
  estimateTokenUsage: (taskType, contentLength) => {
    // Simple estimation based on task type and content length
    const baseTokens = {
      'image': 1000,
      'code': 500,
      'code_project': 2000,
      'prompt': 300,
      'meeting': 1500,
      'people_image': 800
    };
    
    const base = baseTokens[taskType] || 500;
    const estimated = base + (contentLength * 0.1);
    
    return Math.ceil(estimated);
  }
};

export default TokenManagementService;
