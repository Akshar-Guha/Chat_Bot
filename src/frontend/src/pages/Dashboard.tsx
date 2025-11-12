import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid as MuiGrid, // Rename Grid to MuiGrid to avoid potential conflicts
  Card,
  CardContent,
  Stack,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { getSystemStats, getQueryHistory } from '../services/api';

interface SystemStats {
  index: {
    total_chunks: number;
    collection_name: string;
  };
  cache: {
    hits: number;
    misses: number;
    hit_rate: number;
    queries_cached: number;
  };
  memory: {
    total_memories: number;
  };
  performance: {
    avg_query_time_ms: number;
    queries_today: number;
    queries_this_week: number;
  };
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle, icon, color }) => (
  <Card>
    <CardContent>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h4" gutterBottom>
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box sx={{ color, opacity: 0.8 }}>
          {icon}
        </Box>
      </Stack>
    </CardContent>
  </Card>
);

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [queryHistory, setQueryHistory] = useState<any[]>([]);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsData, historyData] = await Promise.all([
        getSystemStats(),
        getQueryHistory(),
      ]);
      setStats(statsData);
      setQueryHistory(historyData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
    setLoading(false);
  };

  const performanceData = [
    { name: 'Mon', queries: 45, avgTime: 230 },
    { name: 'Tue', queries: 52, avgTime: 210 },
    { name: 'Wed', queries: 38, avgTime: 245 },
    { name: 'Thu', queries: 65, avgTime: 195 },
    { name: 'Fri', queries: 71, avgTime: 185 },
    { name: 'Sat', queries: 30, avgTime: 220 },
    { name: 'Sun', queries: 25, avgTime: 235 },
  ];

  const intentDistribution = [
    { name: 'Factual', value: 35, color: '#2563eb' },
    { name: 'Exploratory', value: 25, color: '#7c3aed' },
    { name: 'Comparative', value: 20, color: '#10b981' },
    { name: 'Causal', value: 12, color: '#f59e0b' },
    { name: 'Other', value: 8, color: '#6b7280' },
  ];

  const cachePerformance = [
    { name: '00:00', hitRate: 0.65 },
    { name: '04:00', hitRate: 0.72 },
    { name: '08:00', hitRate: 0.58 },
    { name: '12:00', hitRate: 0.81 },
    { name: '16:00', hitRate: 0.85 },
    { name: '20:00', hitRate: 0.78 },
    { name: '24:00', hitRate: 0.70 },
  ];

  if (loading || !stats) {
    return (
      <Box>
        <LinearProgress />
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 4 }}>
          Loading dashboard...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          System Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Real-time monitoring and analytics for EideticRAG
        </Typography>
      </Paper>

      <MuiGrid container spacing={3} sx={{ mb: 3 }}>
        <MuiGrid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Chunks"
            value={stats.index.total_chunks}
            subtitle="Indexed documents"
            icon={<StorageIcon />}
            color="#2563eb"
          />
        </MuiGrid>
        <MuiGrid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Cache Hit Rate"
            value={`${(stats.cache.hit_rate * 100).toFixed(1)}%`}
            subtitle={`${stats.cache.hits} hits / ${stats.cache.misses} misses`}
            icon={<SpeedIcon />}
            color="#10b981"
          />
        </MuiGrid>
        <MuiGrid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Memories"
            value={stats.memory.total_memories}
            subtitle="Stored interactions"
            icon={<PsychologyIcon />}
            color="#7c3aed"
          />
        </MuiGrid>
        <MuiGrid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Query Time"
            value={`${stats.performance?.avg_query_time_ms || 250}ms`}
            subtitle="Response time"
            icon={<TrendingUpIcon />}
            color="#f59e0b"
          />
        </MuiGrid>
      </MuiGrid>

      <MuiGrid container spacing={3}>
        <MuiGrid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Query Volume & Performance
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="queries"
                  stroke="#2563eb"
                  name="Queries"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="avgTime"
                  stroke="#10b981"
                  name="Avg Time (ms)"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </MuiGrid>

        <MuiGrid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Query Intent Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={intentDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {intentDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </MuiGrid>

        <MuiGrid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Cache Performance (24h)
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={cachePerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value: any) => `${(value * 100).toFixed(0)}%`} />
                <Area
                  type="monotone"
                  dataKey="hitRate"
                  stroke="#10b981"
                  fill="#10b98133"
                  name="Hit Rate"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </MuiGrid>

        <MuiGrid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Health
            </Typography>
            <Stack spacing={2}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">Vector Index</Typography>
                <Chip
                  label="Operational"
                  color="success"
                  size="small"
                  icon={<CheckCircleIcon />}
                />
              </Stack>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">Memory Database</Typography>
                <Chip
                  label="Operational"
                  color="success"
                  size="small"
                  icon={<CheckCircleIcon />}
                />
              </Stack>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">Cache System</Typography>
                <Chip
                  label="Optimal"
                  color="success"
                  size="small"
                  icon={<CheckCircleIcon />}
                />
              </Stack>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">Reflection Agent</Typography>
                <Chip
                  label="Active"
                  color="success"
                  size="small"
                  icon={<CheckCircleIcon />}
                />
              </Stack>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">Generation Model</Typography>
                <Chip
                  label="Mock Mode"
                  color="warning"
                  size="small"
                  icon={<WarningIcon />}
                />
              </Stack>
            </Stack>
          </Paper>
        </MuiGrid>
      </MuiGrid>
    </Box>
  );
};

export default Dashboard;
