import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Chip,
  Stack,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  LinearProgress,
  MenuItem,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  ContentCopy as CopyIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Flag as FlagIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { queryAPI } from '../services/api';
import ProvenancePanel from '../components/ProvenancePanel';
import ChunkViewer from '../components/ChunkViewer';
import WebSearchToggle from '../components/WebSearchToggle';
import { GeneratorType, QueryRequest, QueryResponse } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const QueryPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [feedbackGiven, setFeedbackGiven] = useState<string | null>(null);
  const [generatorType, setGeneratorType] = useState<GeneratorType>('ollama');
  const [modelName, setModelName] = useState<string>('llama3.2:1b');
  const [apiKey, setApiKey] = useState<string>('');
  const [apiBase, setApiBase] = useState<string>('');
  const [webSearchEnabled, setWebSearchEnabled] = useState<boolean>(false);
  const [searchStrategy, setSearchStrategy] = useState<'local_only' | 'web_only' | 'hybrid'>('hybrid');
  const [useWikipedia, setUseWikipedia] = useState<boolean>(false);
  const [useCaching, setUseCaching] = useState<boolean>(true);
  const [useMemory, setUseMemory] = useState<boolean>(true);
  const [useReflection, setUseReflection] = useState<boolean>(true);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setFeedbackGiven(null);

    try {
      if (generatorType !== 'ollama' && generatorType !== 'mock' && !apiKey.trim()) {
        setLoading(false);
        setError('Please provide an API key for the selected mode.');
        return;
      }

      if ((generatorType === 'huggingface' || generatorType === 'spikingbrain') && !apiBase.trim()) {
        setLoading(false);
        setError('Please provide the API base URL for the selected mode.');
        return;
      }

      const request: QueryRequest = {
        query,
        use_web_search: webSearchEnabled,
        use_wikipedia: webSearchEnabled ? useWikipedia : false,
        search_strategy: searchStrategy,
        use_cache: useCaching,
        use_memory: useMemory,
        use_reflection: useReflection,
        generator: {
          type: generatorType,
          model: modelName.trim() || undefined,
          api_key: apiKey.trim() || undefined,
          api_base: apiBase.trim() || undefined,
        },
      };

      // Remove undefined generator fields to avoid backend validation issues
      if (request.generator) {
        Object.entries(request.generator).forEach(([key, value]) => {
          if (value === undefined || value === '') {
            delete (request.generator as Record<string, unknown>)[key];
          }
        });

        if (Object.keys(request.generator).length === 0) {
          delete request.generator;
        }
      }

      const response = await queryAPI(request);
      setResult(response);
      setTabValue(0);
    } catch (err: any) {
      const message = err?.response?.data?.detail || err?.message || 'An error occurred';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Reset defaults when changing generator type
    if (generatorType === 'ollama') {
      setModelName('llama3.2:1b');
      setApiKey('');
      setApiBase('');
    } else if (generatorType === 'openai') {
      setModelName('gpt-4o-mini');
      setApiBase('');
    } else if (generatorType === 'huggingface') {
      setModelName('mistralai/Mixtral-8x7B-Instruct');
      setApiBase('');
    } else if (generatorType === 'spikingbrain') {
      setModelName('spikingbrain/starter');
      setApiBase('');
    } else {
      setModelName('mock-model');
      setApiKey('');
      setApiBase('');
    }
  }, [generatorType]);

  const handleCopy = () => {
    if (result?.answer) {
      navigator.clipboard.writeText(result.answer);
    }
  };

  const handleFeedback = (type: 'positive' | 'negative') => {
    setFeedbackGiven(type);
    // TODO: Send feedback to API
  };

  const getVerificationBadge = () => {
    if (!result?.verification) return null;
    
    const score = result.verification.hallucination_score;
    if (score < 0.2) {
      return <Chip label="Highly Reliable" color="success" size="small" />;
    } else if (score < 0.4) {
      return <Chip label="Moderately Reliable" color="warning" size="small" />;
    } else {
      return <Chip label="Low Confidence" color="error" size="small" />;
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Paper sx={{ p: 3, mb: 3 }} className="fade-in">
        <Typography variant="h4" gutterBottom>
          Ask a Question
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Get intelligent answers with transparent provenance and verification
        </Typography>

        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                select
                label="Mode"
                value={generatorType}
                onChange={(e) => setGeneratorType(e.target.value as GeneratorType)}
                disabled={loading}
                sx={{ minWidth: 220 }}
                helperText="Choose between local and hosted generation backends"
              >
                <MenuItem value="ollama">Local (Ollama)</MenuItem>
                <MenuItem value="openai">OpenAI API</MenuItem>
                <MenuItem value="huggingface">Hugging Face Endpoint</MenuItem>
                <MenuItem value="spikingbrain">SpikingBrain</MenuItem>
                <MenuItem value="mock">Mock Responses</MenuItem>
              </TextField>
              <TextField
                label="Model"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                disabled={loading}
                fullWidth
              />
            </Stack>

            {(generatorType === 'openai' || generatorType === 'huggingface' || generatorType === 'spikingbrain') && (
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                <TextField
                  label="API Key"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  disabled={loading}
                  fullWidth
                  autoComplete="off"
                  helperText="Stored only in this session"
                />
                {(generatorType === 'huggingface' || generatorType === 'spikingbrain') && (
                  <TextField
                    label="API Base URL"
                    value={apiBase}
                    onChange={(e) => setApiBase(e.target.value)}
                    disabled={loading}
                    fullWidth
                    placeholder="https://api-inference.huggingface.co/models/..."
                  />
                )}
              </Stack>
            )}

            <Divider sx={{ my: 1 }} />

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>Advanced Features</Typography>
              <Stack direction="row" spacing={2} flexWrap="wrap">
                <Stack direction="row" spacing={1} alignItems="center">
                  <input
                    type="checkbox"
                    id="cache-toggle"
                    checked={useCaching}
                    onChange={(e) => setUseCaching(e.target.checked)}
                    disabled={loading}
                  />
                  <label htmlFor="cache-toggle" style={{ cursor: 'pointer', fontSize: '0.9rem' }}>
                    Enable Caching
                  </label>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <input
                    type="checkbox"
                    id="memory-toggle"
                    checked={useMemory}
                    onChange={(e) => setUseMemory(e.target.checked)}
                    disabled={loading}
                  />
                  <label htmlFor="memory-toggle" style={{ cursor: 'pointer', fontSize: '0.9rem' }}>
                    Enable Memory
                  </label>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <input
                    type="checkbox"
                    id="reflection-toggle"
                    checked={useReflection}
                    onChange={(e) => setUseReflection(e.target.checked)}
                    disabled={loading}
                  />
                  <label htmlFor="reflection-toggle" style={{ cursor: 'pointer', fontSize: '0.9rem' }}>
                    Enable Reflection
                  </label>
                </Stack>
              </Stack>
            </Box>

            <Stack spacing={2}>
              <WebSearchToggle
                enabled={webSearchEnabled}
                strategy={searchStrategy}
                useWikipedia={useWikipedia}
                onEnabledChange={setWebSearchEnabled}
                onStrategyChange={setSearchStrategy}
                onWikipediaChange={setUseWikipedia}
                disabled={loading}
              />

              <TextField
                fullWidth
                multiline
                rows={3}
                variant="outlined"
                placeholder="Ask anything..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loading}
              />
              <Stack direction="row" spacing={2}>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                  disabled={loading || !query.trim()}
                >
                  {loading ? 'Processing...' : 'Send'}
                </Button>
                {result && (
                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={() => {
                      setResult(null);
                      setQuery('');
                    }}
                    disabled={loading}
                  >
                    New Query
                  </Button>
                )}
              </Stack>
          </Stack>
        </form>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Paper sx={{ mb: 3 }} className="fade-in">
          <Box sx={{ p: 3 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h5">Answer</Typography>
              <Stack direction="row" spacing={1}>
                {getVerificationBadge()}
                <Tooltip title="Copy answer">
                  <IconButton size="small" onClick={handleCopy}>
                    <CopyIcon />
                  </IconButton>
                </Tooltip>
              </Stack>
            </Stack>

            <Box className="markdown-content" sx={{ mb: 3 }}>
              <ReactMarkdown>{result.answer}</ReactMarkdown>
            </Box>

            {result.verification && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Support Ratio: {(result.verification.support_ratio * 100).toFixed(0)}% | 
                  Unsupported Claims: {result.verification.unsupported_claims}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={result.verification.support_ratio * 100}
                  sx={{ mt: 1 }}
                  color={result.verification.hallucination_score < 0.3 ? 'success' : 'warning'}
                />
              </Box>
            )}

            <Stack direction="row" spacing={1}>
              <Button
                size="small"
                startIcon={<ThumbUpIcon />}
                variant={feedbackGiven === 'positive' ? 'contained' : 'outlined'}
                color="success"
                onClick={() => handleFeedback('positive')}
              >
                Helpful
              </Button>
              <Button
                size="small"
                startIcon={<ThumbDownIcon />}
                variant={feedbackGiven === 'negative' ? 'contained' : 'outlined'}
                color="error"
                onClick={() => handleFeedback('negative')}
              >
                Not Helpful
              </Button>
              <Button
                size="small"
                startIcon={<FlagIcon />}
                variant="outlined"
                color="warning"
              >
                Report Issue
              </Button>
            </Stack>
          </Box>

          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tab label="Sources" />
            <Tab label="Provenance" />
            <Tab label="Metadata" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <ChunkViewer chunks={result.chunks} />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <ProvenancePanel provenance={result.provenance} />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>Query Information</Typography>
                <Stack spacing={1}>
                  <Typography variant="body2">
                    <strong>Model:</strong> {result.metadata?.model || 'N/A'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Total Duration:</strong> {result.metadata?.total_duration_ms !== undefined
                      ? `${result.metadata.total_duration_ms.toFixed(2)} ms`
                      : 'N/A'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Cached:</strong> {result.metadata?.cached ? 'Yes' : 'No'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Reflection:</strong> {result.metadata?.reflection_enabled ? 'Enabled' : 'Disabled'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Memory:</strong> {result.metadata?.memory_enabled ? 'Enabled' : 'Disabled'}
                  </Typography>
                  {result.metadata?.web_search_enabled !== undefined && (
                    <Typography variant="body2">
                      <strong>Web Search:</strong> {result.metadata.web_search_enabled ? 'Enabled' : 'Disabled'}
                    </Typography>
                  )}
                  {result.metadata?.search_strategy && (
                    <Typography variant="body2">
                      <strong>Search Strategy:</strong> {result.metadata.search_strategy}
                    </Typography>
                  )}
                  {result.metadata?.num_web_results !== undefined && (
                    <Typography variant="body2">
                      <strong>Web Results:</strong> {result.metadata.num_web_results}
                    </Typography>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </TabPanel>
        </Paper>
      )}
    </Box>
  );
};

export default QueryPage;
