import { useState, useEffect } from 'react';
import { Upload, MessageSquare, FileText, Trash2 } from 'lucide-react';
import './styles/index.css';
import UploadSection from './components/Upload/UploadSection';
import ProcessingDisplay from './components/Display/ProcessingDisplay';
import ChatInterface from './components/Chat/ChatInterface';
import { useWebSocket } from './hooks/useWebSocket';
import { useUpload } from './hooks/useUpload';
import { useChat } from './hooks/useChat';
import { clearSession } from './services/api';

type AppState = 'upload' | 'processing' | 'chat';

function App() {
  const [sessionId, setSessionId] = useState<string>('');
  const [appState, setAppState] = useState<AppState>('upload');
  
  const { progress, isConnected } = useWebSocket(sessionId);
  const { uploadDocument, isUploading, uploadError } = useUpload(sessionId);
  const { messages, sendMessage, isLoading: isChatLoading } = useChat(sessionId);

  useEffect(() => {
    // Get or create session ID
    let id = localStorage.getItem('sessionId');
    const lastActivity = localStorage.getItem('lastActivity');
    const now = Date.now();
    
    // Clear session if inactive for more than 1 hour
    if (id && lastActivity) {
      const lastActivityTime = parseInt(lastActivity);
      if (now - lastActivityTime > 3600000) {  // 1 hour in milliseconds
        console.log('Session expired, creating new session');
        // Clear progress data for expired session
        localStorage.removeItem(`progress_${id}`);
        id = null;
        localStorage.removeItem('sessionId');
        localStorage.removeItem('lastActivity');
      }
    }
    
    // Create new session if needed
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem('sessionId', id);
      console.log('Created new session:', id);
    }
    
    // Update last activity
    localStorage.setItem('lastActivity', now.toString());
    setSessionId(id);
  }, []);

  // Removed auto-transition - user has full control over navigation

  const handleFileUpload = async (file: File) => {
    // Switch to processing view immediately to show upload progress
    setAppState('processing');
    
    const result = await uploadDocument(file);
    if (!result.success) {
      // If upload fails, go back to upload view
      setAppState('upload');
    }
  };

  const handleClearSession = async () => {
    if (confirm('Are you sure you want to clear all data and start fresh?')) {
      try {
        await clearSession(sessionId);
        
        // Clear stored progress data
        localStorage.removeItem(`progress_${sessionId}`);
        
        // Create new session
        const newId = crypto.randomUUID();
        localStorage.setItem('sessionId', newId);
        localStorage.setItem('lastActivity', Date.now().toString());
        setSessionId(newId);
        setAppState('upload');
        window.location.reload();
      } catch (error) {
        console.error('Failed to clear session:', error);
      }
    }
  };

  const handleBackToUpload = () => {
    setAppState('upload');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-lg shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold gradient-text flex items-center gap-3">
                <FileText className="w-8 h-8 text-indigo-600" />
                Multi-Modal RAG
              </h1>
              <p className="text-gray-600 mt-1 text-sm">
                Intelligent Document Analysis with AI
              </p>
            </div>
            
            {/* Navigation Pills */}
            <div className="flex items-center gap-3">
              <div className="flex bg-gray-100 rounded-full p-1">
                <button
                  onClick={() => setAppState('upload')}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    appState === 'upload'
                      ? 'bg-white text-indigo-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Upload className="w-4 h-4 inline mr-2" />
                  Upload
                </button>
                <button
                  onClick={() => progress && setAppState('processing')}
                  disabled={!progress}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    appState === 'processing'
                      ? 'bg-white text-indigo-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed'
                  }`}
                >
                  <FileText className="w-4 h-4 inline mr-2" />
                  Processing
                </button>
                <button
                  onClick={() => progress?.status === 'completed' && setAppState('chat')}
                  disabled={progress?.status !== 'completed'}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    appState === 'chat'
                      ? 'bg-white text-indigo-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed'
                  }`}
                >
                  <MessageSquare className="w-4 h-4 inline mr-2" />
                  Chat
                </button>
              </div>
              
              <button
                onClick={handleClearSession}
                className="btn-secondary flex items-center gap-2"
                title="Clear session and start fresh"
              >
                <Trash2 className="w-4 h-4" />
                Clear
              </button>
            </div>
          </div>
          
          {/* Connection Status */}
          <div className="mt-3 flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <div className="text-gray-500">
              Session: <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">{sessionId.slice(0, 8)}...</code>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {appState === 'upload' && (
          <UploadSection
            onFileUpload={handleFileUpload}
            isUploading={isUploading}
            error={uploadError}
          />
        )}

        {appState === 'processing' && (
          <ProcessingDisplay
            progress={progress}
            onBackToUpload={handleBackToUpload}
          />
        )}

        {appState === 'chat' && (
          <ChatInterface
            messages={messages}
            onSendMessage={sendMessage}
            isLoading={isChatLoading}
            onBackToUpload={handleBackToUpload}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 py-8 border-t border-gray-200 bg-white/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-600 text-sm">
          <p>Multi-Modal RAG System • Powered by Groq & ChromaDB</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
