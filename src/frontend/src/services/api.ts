import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { QueryRequest, QueryResponse, IndexStats, ModelInfo } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
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
    return response.data;
  }

  async uploadDocument(file: File): Promise<{
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
    });
    return response.data;
  }

  async clearIndex(): Promise<{ status: string; message: string }> {
    const response = await this.client.delete('/index/clear');
    return response.data;
  }

  async getMemoryEntries(): Promise<Array<{
    id: string;
    content: string;
    metadata: Record<string, any>;
    tags: string[];
    created_at: string;
  }>> {
    const response = await this.client.get('/memory/');
    // Backend returns { memories: [...], count: number }
    // We need to extract the memories array and transform it
    const memories = response.data.memories || [];
    return memories.map((memory: any) => ({
      id: memory.id,
      content: memory.content,
      metadata: memory.metadata || {},
      tags: memory.metadata?.tags || [],
      created_at: memory.created_at
    }));
  }

  async addMemoryEntry(content: string, tags?: string[]): Promise<{
    id: string;
    content: string;
    metadata: Record<string, any>;
    tags: string[];
    created_at: string;
  }> {
    const response = await this.client.post('/memory/', {
      content,
      tags,
      metadata: { tags: tags || [] }
    });
    return response.data;
  }

  // Legacy methods for backward compatibility
  async queryLegacy(query: string, k: number = 5) {
    return this.query({ query, k });
  }

  async uploadDocumentLegacy(file: File, onProgress?: (progress: number) => void) {
    return this.uploadDocument(file);
  }

  async getDocuments() {
    // Return mock data for now - would come from API
    return [
      {
        doc_id: 'doc_001',
        filename: 'sample1.txt',
        num_chunks: 12,
        size: 4096,
        upload_date: new Date().toISOString(),
        format: 'txt',
      },
      {
        doc_id: 'doc_002',
        filename: 'sample2.txt',
        num_chunks: 8,
        size: 3072,
        upload_date: new Date().toISOString(),
        format: 'txt',
      },
    ];
  }

  async deleteDocument(docId: string) {
    // Mock implementation - would call DELETE endpoint
    return { success: true, message: `Document ${docId} deleted` };
  }

  async getMemories(limit: number = 50) {
    return this.getMemoryEntries();
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
    const response = await this.client.get('/memory/export/json');
    return new Blob([JSON.stringify(response.data)], { type: 'application/json' });
  }

  async getSystemStats() {
    try {
      const stats = await this.getStats();
      return {
        index: {
          total_chunks: stats.total_chunks,
          collection_name: 'eidetic_rag'
        },
        cache: { hits: 0, misses: 0, hit_rate: 0, queries_cached: 0 },
        memory: { total_memories: 0 },
        performance: {
          avg_query_time_ms: 0,
          queries_today: 0,
          queries_this_week: 0
        },
      };
    } catch (error) {
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
export const uploadDocument = (file: File, onProgress?: (progress: number) => void) =>
  apiService.uploadDocument(file);

export const getDocuments = () => apiService.getDocuments();
export const deleteDocument = (docId: string) => apiService.deleteDocument(docId);
export const clearIndex = () => apiService.clearIndex();

// Memory management functions
export const getMemories = (limit: number = 50) => apiService.getMemories(limit);
export const updateMemory = (memoryId: string, updates: any) => apiService.updateMemory(memoryId, updates);
export const deleteMemory = (memoryId: string) => apiService.deleteMemory(memoryId);
export const exportMemories = () => apiService.exportMemories();
