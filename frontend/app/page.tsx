'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import useWebSocket from 'react-use-websocket';

export default function Home() {
  const [botStatus, setBotStatus] = useState({ status: 'unknown', pid: null, uptime: null, memory_usage: null });
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get API and WebSocket URLs from environment variables or use defaults
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

  // WebSocket connection for real-time logs
  const { lastMessage } = useWebSocket(wsUrl, {
    onOpen: () => console.log('WebSocket connected'),
    onError: (event) => {
      console.error('WebSocket error:', event);
      setError('Failed to connect to WebSocket for logs');
    },
    shouldReconnect: () => true,
  });

  // Fetch initial bot status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get(`${apiUrl}/status`);
        setBotStatus(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching status:', err);
        setError('Failed to fetch bot status');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [apiUrl]);

  // Fetch initial logs
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await axios.get(`${apiUrl}/logs`);
        setLogs(response.data.logs || []);
      } catch (err) {
        console.error('Error fetching logs:', err);
      }
    };

    fetchLogs();
  }, [apiUrl]);

  // Update logs when new WebSocket message arrives
  useEffect(() => {
    if (lastMessage?.data) {
      setLogs((prevLogs) => [...prevLogs, lastMessage.data as string]);
    }
  }, [lastMessage]);

  // Handle bot control actions
  const handleStartBot = async () => {
    try {
      await axios.post(`${apiUrl}/start`);
    } catch (err) {
      console.error('Error starting bot:', err);
      setError('Failed to start bot');
    }
  };

  const handleStopBot = async () => {
    try {
      await axios.post(`${apiUrl}/stop`);
    } catch (err) {
      console.error('Error stopping bot:', err);
      setError('Failed to stop bot');
    }
  };

  const handleRestartBot = async () => {
    try {
      await axios.post(`${apiUrl}/restart`);
    } catch (err) {
      console.error('Error restarting bot:', err);
      setError('Failed to restart bot');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">VigilBot Dashboard</h1>
        <p className="text-gray-600">OSINT Investigation Tool</p>
      </header>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Bot Status</h2>
          {isLoading ? (
            <p>Loading...</p>
          ) : (
            <div>
              <div className="flex items-center mb-2">
                <div 
                  className={`w-3 h-3 rounded-full mr-2 ${
                    botStatus.status === 'running' ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                <span className="font-medium">
                  Status: {botStatus.status}
                </span>
              </div>
              {botStatus.pid && <p>PID: {botStatus.pid}</p>}
              {botStatus.uptime && <p>Uptime: {botStatus.uptime}</p>}
              {botStatus.memory_usage && <p>Memory: {botStatus.memory_usage}</p>}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Controls</h2>
          <div className="flex flex-col space-y-2">
            <button
              onClick={handleStartBot}
              className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded"
              disabled={botStatus.status === 'running'}
            >
              Start Bot
            </button>
            <button
              onClick={handleStopBot}
              className="bg-red-500 hover:bg-red-600 text-white py-2 px-4 rounded"
              disabled={botStatus.status !== 'running'}
            >
              Stop Bot
            </button>
            <button
              onClick={handleRestartBot}
              className="bg-yellow-500 hover:bg-yellow-600 text-white py-2 px-4 rounded"
            >
              Restart Bot
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Info</h2>
          <p>Use this dashboard to manage your VigilBot instance.</p>
          <p className="mt-2">For commands and features, invite the bot to your Discord server and type <code>!help</code>.</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Bot Logs</h2>
        <div className="bg-gray-900 text-gray-100 p-4 rounded h-96 overflow-y-auto font-mono text-sm">
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <div key={index} className="whitespace-pre-wrap mb-1">
                {log}
              </div>
            ))
          ) : (
            <p className="text-gray-500">No logs available</p>
          )}
        </div>
      </div>
    </div>
  );
}
