import React from 'react';
import {
  Box,
  FormControlLabel,
  Switch,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack,
  Typography,
} from '@mui/material';
import { Language as LanguageIcon } from '@mui/icons-material';

interface WebSearchToggleProps {
  enabled: boolean;
  strategy: 'local_only' | 'web_only' | 'hybrid';
  useWikipedia: boolean;
  onEnabledChange: (enabled: boolean) => void;
  onStrategyChange: (strategy: 'local_only' | 'web_only' | 'hybrid') => void;
  onWikipediaChange: (enabled: boolean) => void;
  disabled?: boolean;
}

const WebSearchToggle: React.FC<WebSearchToggleProps> = ({
  enabled,
  strategy,
  useWikipedia,
  onEnabledChange,
  onStrategyChange,
  onWikipediaChange,
  disabled = false,
}) => {
  return (
    <Box
      sx={{
        p: 2,
        border: '1px solid',
        borderColor: enabled ? 'primary.main' : 'divider',
        borderRadius: 2,
        bgcolor: enabled ? 'primary.50' : 'background.paper',
        transition: 'all 0.3s ease',
      }}
    >
      <Stack spacing={2}>
        <Stack direction="row" alignItems="center" spacing={2}>
          <FormControlLabel
            control={
              <Switch
                checked={enabled}
                onChange={(e) => onEnabledChange(e.target.checked)}
                disabled={disabled}
                color="primary"
              />
            }
            label={
              <Stack direction="row" alignItems="center" spacing={1}>
                <LanguageIcon fontSize="small" />
                <Typography variant="body1" fontWeight="medium">
                  Web Search
                </Typography>
              </Stack>
            }
          />
          {enabled && (
            <Chip
              label="LIVE"
              size="small"
              color="success"
              sx={{
                fontWeight: 'bold',
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.7 },
                },
              }}
            />
          )}
        </Stack>

        {enabled && (
          <FormControl fullWidth size="small" disabled={disabled}>
            <InputLabel id="search-strategy-label">Search Strategy</InputLabel>
            <Select
              labelId="search-strategy-label"
              value={strategy}
              label="Search Strategy"
              onChange={(e) =>
                onStrategyChange(
                  e.target.value as 'local_only' | 'web_only' | 'hybrid'
                )
              }
            >
              <MenuItem value="local_only">
                <Stack>
                  <Typography variant="body2" fontWeight="medium">
                    Local Only
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Search only in indexed documents
                  </Typography>
                </Stack>
              </MenuItem>
              <MenuItem value="web_only">
                <Stack>
                  <Typography variant="body2" fontWeight="medium">
                    Web Only
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Search only on the web using DuckDuckGo
                  </Typography>
                </Stack>
              </MenuItem>
              <MenuItem value="hybrid">
                <Stack>
                  <Typography variant="body2" fontWeight="medium">
                    Hybrid (Recommended)
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Combine local knowledge with live web results
                  </Typography>
                </Stack>
              </MenuItem>
            </Select>
          </FormControl>
        )}

        {enabled && (
          <FormControlLabel
            control={
              <Switch
                checked={useWikipedia}
                onChange={(e) => onWikipediaChange(e.target.checked)}
                disabled={disabled}
                color="secondary"
              />
            }
            label={
              <Stack direction="row" alignItems="center" spacing={1}>
                <Typography variant="body1" fontWeight="medium">
                  Include Wikipedia
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Adds detailed encyclopedic context
                </Typography>
              </Stack>
            }
          />
        )}
      </Stack>
    </Box>
  );
};

export default WebSearchToggle;
