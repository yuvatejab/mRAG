import { useState, useCallback } from 'react';
import { CheckCircle, Clock, FileText, Grid, Zap, Upload, ChevronDown, ChevronUp, Image as ImageIcon, Table as TableIcon } from 'lucide-react';
import { ProcessingProgress } from '../../types';

interface ProcessingDisplayProps {
  progress: ProcessingProgress | null;
  onBackToUpload: () => void;
}

type Section = 'upload' | 'partitioning' | 'chunking' | 'vectorization';

export default function ProcessingDisplay({ progress, onBackToUpload }: ProcessingDisplayProps) {
  const [activeSection, setActiveSection] = useState<Section>('upload');
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set());

  // Track which stages have been completed
  const stageStatus = {
    upload: progress?.stage === 'uploading' || progress ? 'completed' : 'pending',
    partitioning: progress?.stage === 'partitioning' ? 'active' : 
                  (progress?.stage === 'chunking' || progress?.stage === 'vectorization' || progress?.stage === 'completed') ? 'completed' : 'pending',
    chunking: progress?.stage === 'chunking' ? 'active' :
              (progress?.stage === 'vectorization' || progress?.stage === 'completed') ? 'completed' : 'pending',
    vectorization: progress?.stage === 'vectorization' ? 'active' :
                   progress?.stage === 'completed' ? 'completed' : 'pending',
  };

  const isCompleted = progress?.status === 'completed';

  // Memoize toggle function to prevent re-creation on every render
  const toggleChunk = useCallback((chunkId: number) => {
    setExpandedChunks(prev => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(chunkId)) {
        newExpanded.delete(chunkId);
      } else {
        newExpanded.add(chunkId);
      }
      return newExpanded;
    });
  }, []);

  const getStatusIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (status === 'active') return <Clock className="w-5 h-5 text-indigo-600 animate-pulse" />;
    return <Clock className="w-5 h-5 text-gray-400" />;
  };

  const getStatusColor = (status: string) => {
    if (status === 'completed') return 'bg-green-50 border-green-200';
    if (status === 'active') return 'bg-indigo-50 border-indigo-200';
    return 'bg-gray-50 border-gray-200';
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mb-4 shadow-lg">
          {isCompleted ? (
            <CheckCircle className="w-8 h-8 text-white" />
          ) : (
            <Clock className="w-8 h-8 text-white animate-pulse" />
          )}
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          {isCompleted ? 'Processing Complete!' : 'Document Processing Pipeline'}
        </h2>
        <p className="text-gray-600 text-lg">
          {isCompleted
            ? 'Your document is ready for chat'
            : progress?.message || 'Uploading your document...'}
        </p>
      </div>

      {/* Section Navigation */}
      <div className="card mb-6">
        <div className="grid grid-cols-4 gap-2">
          <button
            onClick={() => setActiveSection('upload')}
            className={`p-4 rounded-lg border-2 transition-all ${
              activeSection === 'upload' 
                ? 'border-indigo-500 bg-indigo-50' 
                : 'border-gray-200 hover:border-indigo-300'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <Upload className="w-5 h-5 text-indigo-600" />
              {getStatusIcon(stageStatus.upload)}
            </div>
            <h3 className="font-semibold text-sm text-gray-900">Upload</h3>
            <p className="text-xs text-gray-600 mt-1">File upload status</p>
          </button>

          <button
            onClick={() => setActiveSection('partitioning')}
            className={`p-4 rounded-lg border-2 transition-all ${
              activeSection === 'partitioning' 
                ? 'border-indigo-500 bg-indigo-50' 
                : 'border-gray-200 hover:border-indigo-300'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <FileText className="w-5 h-5 text-indigo-600" />
              {getStatusIcon(stageStatus.partitioning)}
            </div>
            <h3 className="font-semibold text-sm text-gray-900">Partitioning</h3>
            <p className="text-xs text-gray-600 mt-1">Element extraction</p>
          </button>

          <button
            onClick={() => setActiveSection('chunking')}
            className={`p-4 rounded-lg border-2 transition-all ${
              activeSection === 'chunking' 
                ? 'border-indigo-500 bg-indigo-50' 
                : 'border-gray-200 hover:border-indigo-300'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <Grid className="w-5 h-5 text-indigo-600" />
              {getStatusIcon(stageStatus.chunking)}
            </div>
            <h3 className="font-semibold text-sm text-gray-900">Chunking</h3>
            <p className="text-xs text-gray-600 mt-1">Semantic chunks</p>
          </button>

          <button
            onClick={() => setActiveSection('vectorization')}
            className={`p-4 rounded-lg border-2 transition-all ${
              activeSection === 'vectorization' 
                ? 'border-indigo-500 bg-indigo-50' 
                : 'border-gray-200 hover:border-indigo-300'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <Zap className="w-5 h-5 text-indigo-600" />
              {getStatusIcon(stageStatus.vectorization)}
            </div>
            <h3 className="font-semibold text-sm text-gray-900">Vectorization</h3>
            <p className="text-xs text-gray-600 mt-1">Embeddings & storage</p>
          </button>
        </div>
      </div>

      {/* Section Content */}
      <div className="card mb-6">
        {/* Upload Section */}
        {activeSection === 'upload' && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <Upload className="w-6 h-6 text-indigo-600" />
              <h3 className="text-xl font-bold text-gray-900">Upload Status</h3>
            </div>
            
            {progress?.stage === 'uploading' || progress ? (
              <div className="space-y-4">
                <div className={`p-4 rounded-lg border-2 ${getStatusColor('completed')}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-900">File Upload</span>
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </div>
                  <p className="text-sm text-gray-600">
                    {progress?.details?.filename || 'Document uploaded successfully'}
                  </p>
                  {progress?.details?.file_size && (
                    <p className="text-xs text-gray-500 mt-1">
                      Size: {(progress.details.file_size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  )}
                </div>
                
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-sm text-green-800">
                    Your document has been uploaded and is being processed. Check other sections for detailed progress.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Upload className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>Waiting for file upload...</p>
              </div>
            )}
          </div>
        )}

        {/* Partitioning Section */}
        {activeSection === 'partitioning' && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <FileText className="w-6 h-6 text-indigo-600" />
              <h3 className="text-xl font-bold text-gray-900">Document Partitioning</h3>
            </div>
            
            {stageStatus.partitioning !== 'pending' ? (
              <div className="space-y-4">
                {/* Progress Bar */}
                {stageStatus.partitioning === 'active' && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-700">Extracting elements...</span>
                      <span className="font-semibold text-indigo-600">{progress?.progress || 0}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-purple-600 h-3 rounded-full transition-all duration-500 animate-pulse"
                        style={{ width: `${progress?.progress || 0}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Element Counts */}
                {progress?.details?.elements_count && (
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Total Elements Extracted</h4>
                    <div className="text-3xl font-bold text-indigo-600 mb-4">
                      {progress.details.elements_count}
                    </div>
                    
                    {/* Element Types Breakdown */}
                    {progress.details.element_types && Object.keys(progress.details.element_types).length > 0 && (
                      <div className="mt-4">
                        <h5 className="text-sm font-semibold text-gray-700 mb-3">Element Types Breakdown</h5>
                        <div className="grid grid-cols-2 gap-3">
                          {Object.entries(progress.details.element_types).map(([type, count]) => (
                            <div key={type} className="bg-white rounded-lg p-3 border border-indigo-100">
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-600 capitalize flex items-center gap-2">
                                  {type === 'text' && <FileText className="w-4 h-4" />}
                                  {type === 'table' && <TableIcon className="w-4 h-4" />}
                                  {type === 'image' && <ImageIcon className="w-4 h-4" />}
                                  {type}
                                </span>
                                <span className="text-lg font-bold text-indigo-600">{count}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {stageStatus.partitioning === 'completed' && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="font-semibold text-green-900">Partitioning Complete</span>
                    </div>
                    <p className="text-sm text-green-700 mt-2">
                      Successfully extracted all elements from your document
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>Waiting for partitioning to start...</p>
              </div>
            )}
          </div>
        )}

        {/* Chunking Section */}
        {activeSection === 'chunking' && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <Grid className="w-6 h-6 text-indigo-600" />
              <h3 className="text-xl font-bold text-gray-900">Chunking Process</h3>
            </div>
            
            {stageStatus.chunking !== 'pending' ? (
              <div className="space-y-4">
                {/* Progress Bar */}
                {stageStatus.chunking === 'active' && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-700">Creating chunks...</span>
                      <span className="font-semibold text-indigo-600">{progress?.progress || 0}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-purple-600 h-3 rounded-full transition-all duration-500 animate-pulse"
                        style={{ width: `${progress?.progress || 0}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Chunk Summary */}
                {progress?.details?.chunks_count && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Chunks Created</h4>
                    <div className="text-3xl font-bold text-purple-600 mb-2">
                      {progress.details.chunks_count}
                    </div>
                    <p className="text-sm text-gray-600">
                      Semantic chunks ready for embedding
                    </p>
                  </div>
                )}

                {/* Chunk Details - Show if available */}
                {progress?.details?.chunk_details && progress.details.chunk_details.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Chunk Details (Full Transparency)</h4>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {progress.details.chunk_details.map((chunk: any, index: number) => (
                        <div key={`chunk-${chunk.id || index}`} className="border border-gray-200 rounded-lg">
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              toggleChunk(chunk.id || index);
                            }}
                            type="button"
                            className="w-full p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <span className="font-mono text-sm text-gray-600">#{chunk.id || (index + 1)}</span>
                              <div className="flex gap-2">
                                {chunk.hasText && (
                                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                    Text ({chunk.fullTextLength} chars)
                                  </span>
                                )}
                                {chunk.hasTable && (
                                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded flex items-center gap-1">
                                    <TableIcon className="w-3 h-3" />
                                    {chunk.tableCount} Table(s)
                                  </span>
                                )}
                                {chunk.hasImage && (
                                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded flex items-center gap-1">
                                    <ImageIcon className="w-3 h-3" />
                                    {chunk.imageCount} Image(s)
                                  </span>
                                )}
                              </div>
                            </div>
                            {expandedChunks.has(chunk.id || index) ? (
                              <ChevronUp className="w-5 h-5 text-gray-400" />
                            ) : (
                              <ChevronDown className="w-5 h-5 text-gray-400" />
                            )}
                          </button>
                          
                          {expandedChunks.has(chunk.id || index) && (
                            <div className="p-4 border-t border-gray-200 bg-gray-50">
                              <div className="mb-3">
                                <span className="text-xs font-semibold text-gray-700 uppercase">Text Content:</span>
                                <div className="mt-2 text-sm text-gray-700 whitespace-pre-wrap bg-white p-3 rounded border border-gray-200">
                                  {chunk.text || 'No text content'}
                                </div>
                              </div>
                              {chunk.metadata && (
                                <div className="mt-3">
                                  <span className="text-xs font-semibold text-gray-700 uppercase">Metadata:</span>
                                  <div className="mt-2 text-xs text-gray-600 bg-white p-3 rounded border border-gray-200 font-mono">
                                    Tables: {chunk.metadata.tables}, Images: {chunk.metadata.images}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {stageStatus.chunking === 'completed' && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="font-semibold text-green-900">Chunking Complete</span>
                    </div>
                    <p className="text-sm text-green-700 mt-2">
                      All chunks created and ready for vectorization
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Grid className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>Waiting for chunking to start...</p>
              </div>
            )}
          </div>
        )}

        {/* Vectorization Section */}
        {activeSection === 'vectorization' && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <Zap className="w-6 h-6 text-indigo-600" />
              <h3 className="text-xl font-bold text-gray-900">Vectorization & Storage</h3>
            </div>
            
            {stageStatus.vectorization !== 'pending' ? (
              <div className="space-y-4">
                {/* Progress Bar */}
                {stageStatus.vectorization === 'active' && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-700">Generating embeddings...</span>
                      <span className="font-semibold text-indigo-600">{progress?.progress || 0}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-purple-600 h-3 rounded-full transition-all duration-500 animate-pulse"
                        style={{ width: `${progress?.progress || 0}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Vectorization Stats */}
                {progress?.details?.vectors_stored && (
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Vectors Stored</h4>
                    <div className="text-3xl font-bold text-indigo-600 mb-2">
                      {progress.details.vectors_stored}
                    </div>
                    <p className="text-sm text-gray-600">
                      Embeddings generated and stored in vector database
                    </p>
                  </div>
                )}

                {isCompleted && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="font-semibold text-green-900">Processing Complete!</span>
                    </div>
                    <p className="text-sm text-green-700 mb-4">
                      Your document has been fully processed and is ready for chat
                    </p>
                    <div className="grid grid-cols-3 gap-3 mt-4">
                      <div className="text-center p-3 bg-white rounded-lg">
                        <div className="text-2xl font-bold text-indigo-600">
                          {progress?.details?.elements_count || 0}
                        </div>
                        <div className="text-xs text-gray-600 mt-1">Elements</div>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          {progress?.details?.chunks_count || 0}
                        </div>
                        <div className="text-xs text-gray-600 mt-1">Chunks</div>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          {progress?.details?.vectors_stored || 0}
                        </div>
                        <div className="text-xs text-gray-600 mt-1">Vectors</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Zap className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>Waiting for vectorization to start...</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      {isCompleted && (
        <div className="text-center">
          <button
            onClick={() => {
              // Parent will handle navigation to chat
            }}
            className="btn-primary text-lg px-8 py-3"
          >
            Start Chatting with Your Document
          </button>
        </div>
      )}
    </div>
  );
}
