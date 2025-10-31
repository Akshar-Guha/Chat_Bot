import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Stack,
  IconButton,
  Collapse,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Description as DocumentIcon,
} from '@mui/icons-material';

interface ChunkData {
  chunk_id: string;
  text: string;
  score: number;
  metadata?: {
    doc_id?: string;
    start_char?: number;
    end_char?: number;
    chunk_index?: number;
    source?: string;
  };
}

interface ChunkViewerProps {
  chunks: ChunkData[];
}

const ChunkViewer: React.FC<ChunkViewerProps> = ({ chunks }) => {
  const [expandedChunks, setExpandedChunks] = useState<Set<string>>(new Set());

  const toggleExpand = (chunkId: string) => {
    const newExpanded = new Set(expandedChunks);
    if (newExpanded.has(chunkId)) {
      newExpanded.delete(chunkId);
    } else {
      newExpanded.add(chunkId);
    }
    setExpandedChunks(newExpanded);
  };

  if (!chunks || chunks.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No source chunks available
      </Typography>
    );
  }

  return (
    <Stack spacing={2}>
      {chunks.map((chunk, index) => {
        const isExpanded = expandedChunks.has(chunk.chunk_id);
        const isMemory = chunk.metadata?.source === 'memory';
        const scorePercentage = typeof chunk.score === 'number' ? (chunk.score * 100).toFixed(1) : 'N/A';
        const startChar = chunk.metadata?.start_char;
        const endChar = chunk.metadata?.end_char;

        return (
          <Card 
            key={chunk.chunk_id} 
            variant="outlined"
            sx={{ 
              borderLeft: 3, 
              borderLeftColor: isMemory ? 'secondary.main' : 'primary.main' 
            }}
          >
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <DocumentIcon color={isMemory ? 'secondary' : 'primary'} fontSize="small" />
                  <Typography variant="subtitle2">
                    Source {index + 1}
                  </Typography>
                  {isMemory && (
                    <Chip label="Memory" size="small" color="secondary" />
                  )}
                </Stack>
                
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip
                    label={`${scorePercentage}%`}
                    size="small"
                    color={chunk.score > 0.8 ? 'success' : chunk.score > 0.6 ? 'warning' : 'default'}
                  />
                  <Tooltip title={isExpanded ? 'Collapse' : 'Expand'}>
                    <IconButton 
                      size="small"
                      onClick={() => toggleExpand(chunk.chunk_id)}
                    >
                      {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  </Tooltip>
                </Stack>
              </Stack>

              <Typography 
                variant="body2" 
                sx={{ 
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: isExpanded ? 'block' : '-webkit-box',
                  WebkitLineClamp: isExpanded ? 'unset' : 3,
                  WebkitBoxOrient: 'vertical',
                  whiteSpace: isExpanded ? 'pre-wrap' : 'normal',
                }}
              >
                {chunk.text}
              </Typography>

              <Collapse in={isExpanded}>
                <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                  <Typography variant="caption" color="text.secondary">
                    <strong>Chunk ID:</strong> {chunk.chunk_id}
                  </Typography>
                  {chunk.metadata?.doc_id && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      <strong>Document ID:</strong> {chunk.metadata.doc_id}
                    </Typography>
                  )}
                  {chunk.metadata?.chunk_index && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      <strong>Chunk Index:</strong> {chunk.metadata.chunk_index}
                    </Typography>
                  )}
                  {startChar !== undefined && endChar !== undefined && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      <strong>Character Range:</strong> {startChar} - {endChar}
                    </Typography>
                  )}
                </Box>
              </Collapse>
            </CardContent>
          </Card>
        );
      })}
    </Stack>
  );
};

export default ChunkViewer;
