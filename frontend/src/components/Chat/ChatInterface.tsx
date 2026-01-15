import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader, Image as ImageIcon, Table as TableIcon } from 'lucide-react';
import { ChatMessage } from '../../types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => Promise<void>;
  isLoading: boolean;
  onBackToUpload: () => void;
}

export default function ChatInterface({
  messages,
  onSendMessage,
  isLoading,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input.trim();
    setInput('');
    await onSendMessage(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="max-w-6xl mx-auto h-[calc(100vh-200px)] flex flex-col">
      {/* Chat Header */}
      <div className="card mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Chat with Your Document</h2>
            <p className="text-gray-600 mt-1">
              Ask questions about your document. I'll provide answers with context.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>Ready</span>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 card overflow-y-auto mb-4 space-y-6 p-6">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mb-4">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Start a Conversation
            </h3>
            <p className="text-gray-600 mb-6">
              Ask me anything about your document
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {[
                'What is this document about?',
                'Summarize the key points',
                'What are the main findings?',
                'Explain the methodology',
              ].map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => setInput(suggestion)}
                  className="p-3 text-left text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 ${
                  message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                }`}
              >
                {/* Avatar */}
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                    message.role === 'user'
                      ? 'bg-indigo-100'
                      : 'bg-gradient-to-br from-purple-500 to-pink-600'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User className="w-5 h-5 text-indigo-600" />
                  ) : (
                    <Bot className="w-5 h-5 text-white" />
                  )}
                </div>

                {/* Message Content */}
                <div
                  className={`flex-1 ${
                    message.role === 'user' ? 'text-right' : 'text-left'
                  }`}
                >
                  <div
                    className={`inline-block p-5 rounded-2xl max-w-4xl ${
                      message.role === 'user'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed text-base">{message.content}</p>
                    
                    {/* Display Tables */}
                    {message.role === 'assistant' && message.metadata?.tables && message.metadata.tables.length > 0 && (
                      <div className="mt-4 space-y-4">
                        {message.metadata.tables.map((table: string, idx: number) => (
                          <div key={idx} className="bg-white rounded-lg p-4 border border-gray-200 overflow-x-auto">
                            <div className="flex items-center gap-2 mb-3">
                              <TableIcon className="w-4 h-4 text-blue-600" />
                              <span className="text-sm font-semibold text-gray-700">Table {idx + 1}</span>
                            </div>
                            <div 
                              className="prose prose-sm max-w-none"
                              dangerouslySetInnerHTML={{ __html: table }}
                              style={{
                                fontSize: '0.875rem',
                              }}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Display Images */}
                    {message.role === 'assistant' && message.metadata?.images && message.metadata.images.length > 0 && (
                      <div className="mt-4 space-y-4">
                        {message.metadata.images.map((image: string, idx: number) => (
                          <div key={idx} className="bg-white rounded-lg p-4 border border-gray-200">
                            <div className="flex items-center gap-2 mb-3">
                              <ImageIcon className="w-4 h-4 text-purple-600" />
                              <span className="text-sm font-semibold text-gray-700">Image {idx + 1}</span>
                            </div>
                            <img
                              src={`data:image/png;base64,${image}`}
                              alt={`Document image ${idx + 1}`}
                              className="max-w-full h-auto rounded-lg shadow-sm"
                              style={{
                                maxHeight: '500px',
                                objectFit: 'contain',
                              }}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Metadata */}
                  {message.metadata && (
                    <div className="mt-3 space-y-2">
                      {message.metadata.chunks_used && (
                        <div className="text-xs text-gray-500">
                          📄 Used {message.metadata.chunks_used} document chunks
                        </div>
                      )}
                    </div>
                  )}

                  <div className="mt-2 text-xs text-gray-500">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-600">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <div className="inline-block p-4 rounded-2xl bg-gray-100">
                <div className="flex items-center gap-2">
                  <Loader className="w-4 h-4 animate-spin text-indigo-600" />
                  <span className="text-gray-600">Thinking...</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <div className="card">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your document..."
            className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
