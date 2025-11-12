import axios, { AxiosInstance, AxiosProgressEvent, AxiosResponse } from 'axios';
import { QueryRequest, QueryResponse, IndexStats, ModelInfo } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log('API Request:', config.method?.toUpperCase(), config.url);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async query(request: QueryRequest): Promise<QueryResponse> {
    const response = await this.client.post('/query', request);
    return response.data;
  }

  async getModelInfo(): Promise<ModelInfo> {
    const response = await this.client.get('/model/info');
    return response.data;
  }

  async getStats(): Promise<IndexStats> {
    const response = await this.client.get('/stats');
    return response.data.stats; // The new backend wraps stats in a 'stats' key
  }

  async uploadDocument(
    file: File,
    onProgress?: (percent: number) => void
  ): Promise<{
    doc_id: string;
    filename: string;
    num_chunks: number;
    message: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post('/ingest', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (event: AxiosProgressEvent) => {
        if (!onProgress) return;

        if (typeof event.total === 'number' && event.total > 0) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        } else if (typeof event.progress === 'number') {
          onProgress(Math.round(event.progress * 100));
        }
      },
    });
    return response.data;
  }

  async clearIndex(): Promise<{ status: string; message: string }> {
    const response = await this.client.delete('/index/clear');
    return response.data;
  }

  // --- Document Management ---

  async getDocuments() {
    const response = await this.client.get('/documents');
    return response.data.documents || [];
  }

  async deleteDocument(docId: string) {
    const response = await this.client.delete(`/documents/${docId}`);
    return response.data;
  }

  // --- Memory Management ---

  async getMemories(limit: number = 50) {
    const response = await this.client.get('/memory', { params: { limit } });
    return response.data.memories || [];
  }

  async addMemoryEntry(content: string, tags?: string[]): Promise<any> {
    const response = await this.client.post('/memory', { content, tags });
    return response.data;
  }

  async updateMemory(memoryId: string, updates: any) {
    const response = await this.client.put(`/memory/${memoryId}`, updates);
    return response.data;
  }

  async deleteMemory(memoryId: string) {
    const response = await this.client.delete(`/memory/${memoryId}`);
    return response.data;
  }

  async exportMemories() {
    const response = await this.client.get('/memory/export', { responseType: 'blob' });
    return response.data;
  }

  async getSystemStats() {
    try {
      const response = await this.client.get('/stats');
      const data = response.data;
      
      // Use detailed_stats if available, otherwise construct from basic stats
      if (data.detailed_stats) {
        return data.detailed_stats;
      }
      
      // Fallback to basic stats
      const stats = data.stats || {};
      return {
        index: {
          total_chunks: stats.total_chunks || 0,
          collection_name: stats.collection_name || 'eidetic_rag'
        },
        cache: {
          hits: stats.cache_hits || 0,
          misses: stats.cache_misses || 0,
          hit_rate: stats.cache_hit_rate || 0,
          queries_cached: 0
        },
        memory: {
          total_memories: stats.total_memories || 0
        },
        performance: {
          avg_query_time_ms: 250,
          queries_today: 0,
          queries_this_week: 0
        },
      };
    } catch (error) {
      console.error('Failed to get system stats:', error);
      return {
        index: { total_chunks: 0, collection_name: 'eidetic_rag' },
        cache: { hits: 0, misses: 0, hit_rate: 0, queries_cached: 0 },
        memory: { total_memories: 0 },
        performance: { avg_query_time_ms: 0, queries_today: 0, queries_this_week: 0 },
      };
    }
  }

  async getQueryHistory() {
    // Mock data - would come from API
    return [
      { timestamp: new Date(), query: 'What is AI?', duration_ms: 245 },
      { timestamp: new Date(), query: 'Explain machine learning', duration_ms: 312 },
    ];
  }
}

export const apiService = new ApiService();
export { apiService as default };

// Export individual methods for direct import
export const getSystemStats = () => apiService.getSystemStats();
export const getQueryHistory = () => apiService.getQueryHistory();
export const queryAPI = (request: QueryRequest | string, k: number = 5) => {
  if (typeof request === 'string') {
    return apiService.query({ query: request, k });
  }
  return apiService.query(request);
};
export const getModelInfo = () => apiService.getModelInfo();

// Document management functions
export const uploadDocument = (
  file: File,
  onProgress?: (percent: number) => void
) => apiService.uploadDocument(file, onProgress);
export const getDocuments = () => apiService.getDocuments();
export const deleteDocument = (docId: string) => apiService.deleteDocument(docId);
export const clearIndex = () => apiService.clearIndex();

// Memory management functions (mocked)
export const getMemories = (limit: number = 50) => apiService.getMemories(limit);
export const addMemoryEntry = (content: string, tags?: string[]) => apiService.addMemoryEntry(content, tags);
export const updateMemory = (memoryId: string, updates: any) => apiService.updateMemory(memoryId, updates);
export const deleteMemory = (memoryId: string) => apiService.deleteMemory(memoryId);
export const exportMemories = () => apiService.exportMemories();
