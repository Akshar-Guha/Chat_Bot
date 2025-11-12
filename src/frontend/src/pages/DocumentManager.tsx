import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  LinearProgress,
  Alert,
  Stack,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  PictureAsPdf as PdfIcon,
  Description as TextIcon,
} from '@mui/icons-material';
import { uploadDocument, getDocuments, deleteDocument } from '../services/api';

interface Document {
  doc_id: string;
  filename: string;
  num_chunks: number;
  size: number;
  upload_date: string;
  format: string;
}

const DocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadDialog, setUploadDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (error) {
      console.error('Failed to load documents:', error);
      setError('Failed to load documents');
    }
    setLoading(false);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadDialog(true);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const response = await uploadDocument(selectedFile, (progress: number) => {
        setUploadProgress(progress);
      });

      setSuccess(`Successfully uploaded ${selectedFile.name} with ${response.num_chunks} chunks`);
      setUploadDialog(false);
      setSelectedFile(null);
      await loadDocuments();
    } catch (error: any) {
      setError(error.message || 'Upload failed');
    }

    setUploading(false);
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    try {
      await deleteDocument(docId);
      setSuccess(`Successfully deleted ${filename}`);
      await loadDocuments();
    } catch (error: any) {
      setError(error.message || 'Failed to delete document');
    }
  };

  const getFileIcon = (format: string) => {
    switch (format.toLowerCase()) {
      case 'pdf':
        return <PdfIcon />;
      case 'txt':
      case 'md':
        return <TextIcon />;
      default:
        return <FileIcon />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4">Document Manager</Typography>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadDocuments}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<UploadIcon />}
              component="label"
              disabled={uploading}
            >
              Upload Document
              <input
                type="file"
                hidden
                accept=".txt,.pdf,.html,.md"
                onChange={handleFileSelect}
              />
            </Button>
          </Stack>
        </Stack>

        <Typography variant="body2" color="text.secondary" paragraph>
          Upload and manage documents for the RAG system. Supported formats: PDF, TXT, HTML, Markdown
        </Typography>

        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <Stack direction="row" spacing={2}>
          <Chip label={`Total Documents: ${documents.length}`} />
          <Chip label={`Total Chunks: ${documents.reduce((acc, doc) => acc + doc.num_chunks, 0)}`} />
        </Stack>
      </Paper>

      {loading ? (
        <LinearProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell></TableCell>
                <TableCell>Filename</TableCell>
                <TableCell>Document ID</TableCell>
                <TableCell>Format</TableCell>
                <TableCell>Size</TableCell>
                <TableCell>Chunks</TableCell>
                <TableCell>Upload Date</TableCell>
                <TableCell>Actions</TableCell>
                <TableCell></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                      No documents uploaded yet. Click "Upload Document" to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                documents.map((doc) => (
                  <TableRow key={doc.doc_id} hover>
                    <TableCell>{getFileIcon(doc.format)}</TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      <Typography variant="body2">{doc.filename}</Typography>
                    </TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                        {doc.doc_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={doc.format.toUpperCase()} size="small" />
                    </TableCell>
                    <TableCell>{formatFileSize(doc.size)}</TableCell>
                    <TableCell>{doc.num_chunks}</TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {new Date(doc.upload_date).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(doc.doc_id, doc.filename)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={uploadDialog} onClose={() => !uploading && setUploadDialog(false)}>
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1, minWidth: 400 }}>
            {selectedFile && (
              <>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CloudUploadIcon color="primary" />
                  <Typography>{selectedFile.name}</Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Size: {formatFileSize(selectedFile.size)}
                </Typography>
                {uploading && (
                  <>
                    <LinearProgress variant="determinate" value={uploadProgress} />
                    <Typography variant="caption" align="center">
                      {uploadProgress}% uploaded
                    </Typography>
                  </>
                )}
              </>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)} disabled={uploading}>
            Cancel
          </Button>
          <Button onClick={handleUpload} variant="contained" disabled={uploading || !selectedFile}>
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentManager;
