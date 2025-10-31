import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Stack,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Rating,
  Tooltip,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  TrendingUp as PromoteIcon,
  TrendingDown as DemoteIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { getMemories, updateMemory, deleteMemory, exportMemories } from '../services/api';

interface Memory {
  id: string;
  content: string;
  metadata: Record<string, any>;
  tags: string[];
  created_at: string;
}

const MemoryInspector: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [editDialog, setEditDialog] = useState<{ open: boolean; memory: Memory | null }>({
    open: false,
    memory: null,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [editedAnswer, setEditedAnswer] = useState('');
  const [editedImportance, setEditedImportance] = useState(0.5);

  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    setLoading(true);
    try {
      const data = await getMemories();
      setMemories(data);
    } catch (error) {
      console.error('Failed to load memories:', error);
    }
    setLoading(false);
  };

  const handleEdit = (memory: Memory) => {
    setEditDialog({ open: true, memory });
    setEditedAnswer(memory.content);
    setEditedImportance(memory.metadata?.importance_score || 0.5);
  };

  const handleSaveEdit = async () => {
    if (!editDialog.memory) return;

    try {
      await updateMemory(editDialog.memory.id, {
        content: editedAnswer,
        importance_score: editedImportance,
        metadata: editDialog.memory.metadata
      });
      await loadMemories();
      setEditDialog({ open: false, memory: null });
    } catch (error) {
      console.error('Failed to update memory:', error);
    }
  };

  const handleDelete = async (memoryId: string) => {
    if (window.confirm('Are you sure you want to delete this memory?')) {
      try {
        await deleteMemory(memoryId);
        await loadMemories();
      } catch (error) {
        console.error('Failed to delete memory:', error);
      }
    }
  };

  const handlePromote = async (memory: Memory) => {
    try {
      const currentScore = memory.metadata?.importance_score || 0.5;
      await updateMemory(memory.id, {
        importance_score: Math.min(1.0, currentScore + 0.2),
        metadata: memory.metadata
      });
      await loadMemories();
    } catch (error) {
      console.error('Failed to promote memory:', error);
    }
  };

  const handleDemote = async (memory: Memory) => {
    try {
      const currentScore = memory.metadata?.importance_score || 0.5;
      await updateMemory(memory.id, {
        importance_score: Math.max(0.0, currentScore - 0.2),
        metadata: memory.metadata
      });
      await loadMemories();
    } catch (error) {
      console.error('Failed to demote memory:', error);
    }
  };

  const handleExport = async () => {
    try {
      const blob = await exportMemories();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `memories_export_${new Date().toISOString()}.json`;
      a.click();
    } catch (error) {
      console.error('Failed to export memories:', error);
    }
  };

  const filteredMemories = memories.filter(
    (memory) =>
      memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (memory.metadata && JSON.stringify(memory.metadata).toLowerCase().includes(searchQuery.toLowerCase())) ||
      memory.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4">Memory Inspector</Typography>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadMemories}
            >
              Refresh
            </Button>
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={handleExport}
            >
              Export
            </Button>
            <Button
              variant="outlined"
              startIcon={<ImportIcon />}
              component="label"
            >
              Import
              <input type="file" hidden accept=".json" />
            </Button>
          </Stack>
        </Stack>

        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search memories..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ mb: 2 }}
        />

        <Alert severity="info" sx={{ mb: 2 }}>
          Total Memories: {memories.length} | 
          With Tags: {memories.filter(m => m.tags && m.tags.length > 0).length} | 
          High Importance: {memories.filter(m => (m.metadata?.importance_score || 0) > 0.7).length}
        </Alert>
      </Paper>

      {loading ? (
        <LinearProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Content</TableCell>
                <TableCell>Tags</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Importance</TableCell>
                <TableCell>Metadata</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredMemories.map((memory) => (
                <TableRow key={memory.id}>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {memory.content}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} flexWrap="wrap">
                      {memory.tags.map((tag, index) => (
                        <Chip key={index} label={tag} size="small" variant="outlined" />
                      ))}
                    </Stack>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {new Date(memory.created_at).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Rating
                      value={(memory.metadata?.importance_score || 0) * 5}
                      max={5}
                      readOnly
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {memory.metadata && Object.keys(memory.metadata).length > 0
                        ? JSON.stringify(memory.metadata)
                        : 'No metadata'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5}>
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => handleEdit(memory)}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Promote">
                        <IconButton size="small" onClick={() => handlePromote(memory)}>
                          <PromoteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Demote">
                        <IconButton size="small" onClick={() => handleDemote(memory)}>
                          <DemoteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton size="small" onClick={() => handleDelete(memory.id)} color="error">
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={editDialog.open} onClose={() => setEditDialog({ open: false, memory: null })} maxWidth="md" fullWidth>
        <DialogTitle>Edit Memory</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Content"
              value={editDialog.memory?.content || ''}
              disabled
              fullWidth
              multiline
              rows={3}
            />
            <TextField
              label="Answer"
              value={editedAnswer}
              onChange={(e) => setEditedAnswer(e.target.value)}
              multiline
              rows={4}
              fullWidth
            />
            <Box>
              <Typography gutterBottom>Importance Score</Typography>
              <Rating
                value={editedImportance * 5}
                max={5}
                onChange={(_, value) => setEditedImportance((value || 0) / 5)}
              />
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog({ open: false, memory: null })}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MemoryInspector;
