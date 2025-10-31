import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Stack,
} from '@mui/material';
import { Link as LinkIcon } from '@mui/icons-material';

interface ProvenanceItem {
  chunk_id: string;
  doc_id?: string;
  score?: number;
  text_snippet: string;
}

interface ProvenancePanelProps {
  provenance: ProvenanceItem[];
}

const ProvenancePanel: React.FC<ProvenancePanelProps> = ({ provenance }) => {
  if (!provenance || provenance.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No provenance information available
      </Typography>
    );
  }

  return (
    <Stack spacing={2}>
      {provenance.map((item, index) => (
        <Card key={index} variant="outlined">
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
              <Stack direction="row" spacing={1} alignItems="center">
                <LinkIcon color="primary" fontSize="small" />
                <Typography variant="subtitle2">
                  Citation {index + 1}
                </Typography>
              </Stack>
              {typeof item.score === 'number' && (
                <Chip
                  label={`Score: ${(item.score * 100).toFixed(1)}%`}
                  size="small"
                  color={item.score > 0.8 ? 'success' : item.score > 0.6 ? 'warning' : 'default'}
                />
              )}
            </Stack>
            
            <Typography variant="caption" color="text.secondary" display="block" mb={1}>
              Chunk ID: {item.chunk_id}
              {item.doc_id ? ` | Doc ID: ${item.doc_id}` : ''}
            </Typography>
            
            <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
              "{item.text_snippet}..."
            </Typography>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
};

export default ProvenancePanel;
