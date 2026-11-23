import { useState, useEffect } from 'react';
import { api } from './api';
import { Draft, QueueItem, ReviewQueue, TriageSummary, AuditLog } from './types';

type Tab = 'queue' | 'drafts' | 'audit';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('queue');
  const [queue, setQueue] = useState<ReviewQueue | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [summary, setSummary] = useState<TriageSummary | null>(null);
  const [selectedItem, setSelectedItem] = useState<QueueItem | null>(null);
  const [selectedDraft, setSelectedDraft] = useState<Draft | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [approverName, setApproverName] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [queueData, draftsData, logsData] = await Promise.all([
        api.triage.getQueue(),
        api.drafts.list(),
        api.audit.list(50),
      ]);
      setQueue(queueData);
      setDrafts(draftsData);
      setAuditLogs(logsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const runTriage = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.triage.processAll({ import_new: true, generate_drafts: true });
      setSummary(result);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Triage failed');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (draftId: string) => {
    if (!approverName.trim()) {
      setError('Please enter your name to approve');
      return;
    }
    setLoading(true);
    try {
      await api.drafts.approve(draftId, approverName);
      await loadData();
      setSelectedItem(null);
      setSelectedDraft(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approval failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (draftId: string, reason: string) => {
    if (!approverName.trim()) {
      setError('Please enter your name to reject');
      return;
    }
    setLoading(true);
    try {
      await api.drafts.reject(draftId, approverName, reason);
      await loadData();
      setSelectedItem(null);
      setSelectedDraft(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rejection failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (draftId: string) => {
    setLoading(true);
    try {
      await api.drafts.send(draftId);
      await loadData();
      setSelectedDraft(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Send failed - approval required');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const priorityColors: Record<string, string> = {
    critical: 'bg-red-100 text-red-800 border-red-300',
    high: 'bg-orange-100 text-orange-800 border-orange-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    low: 'bg-green-100 text-green-800 border-green-300',
  };

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    sent: 'bg-blue-100 text-blue-800',
  };

  const categoryLabels: Record<string, string> = {
    sales_lead: '💼 Sales Lead',
    support_request: '🔧 Support',
    invoice: '💰 Invoice',
    scheduling: '📅 Scheduling',
    newsletter: '📰 Newsletter',
    spam: '🚫 Spam',
    urgent_escalation: '🚨 Urgent',
    personal: '👤 Personal',
    other: '📧 Other',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Inbox Triage</h1>
              <p className="text-sm text-gray-500">Intelligent email classification with human approval</p>
            </div>
            <div className="flex items-center gap-4">
              <input
                type="text"
                placeholder="Your name (for approvals)"
                value={approverName}
                onChange={(e) => setApproverName(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                onClick={runTriage}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Processing...' : 'Run Triage'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {error && (
        <div className="max-w-7xl mx-auto px-4 py-2 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-3 text-red-700 text-sm">
            {error}
            <button onClick={() => setError(null)} className="ml-2 underline">Dismiss</button>
          </div>
        </div>
      )}

      {summary && (
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="font-semibold text-blue-800 mb-2">Triage Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
              <div><span className="text-gray-600">Emails:</span> {summary.total_emails}</div>
              <div><span className="text-gray-600">Classified:</span> {summary.classified}</div>
              <div><span className="text-gray-600">Drafts Created:</span> {summary.drafts_created}</div>
              <div><span className="text-gray-600">Need Reply:</span> {summary.needs_reply}</div>
            </div>
          </div>
        </div>
      )}

      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <div className="flex space-x-8">
            {(['queue', 'drafts', 'audit'] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab === 'queue' && `Review Queue (${queue?.total_pending || 0})`}
                {tab === 'drafts' && `All Drafts (${drafts.length})`}
                {tab === 'audit' && 'Audit Log'}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {activeTab === 'queue' && queue && (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              {(['critical', 'high', 'medium', 'low'] as const).map((priority) => (
                <div key={priority}>
                  <h3 className={`text-sm font-semibold uppercase tracking-wide mb-2 px-2 py-1 rounded ${priorityColors[priority]}`}>
                    {priority} Priority ({queue.queue[priority].length})
                  </h3>
                  {queue.queue[priority].length === 0 ? (
                    <p className="text-gray-400 text-sm italic pl-2">No items</p>
                  ) : (
                    <div className="space-y-2">
                      {queue.queue[priority].map((item) => (
                        <div
                          key={item.email.id}
                          onClick={() => setSelectedItem(item)}
                          className={`p-3 bg-white rounded-lg border cursor-pointer hover:shadow-md transition ${
                            selectedItem?.email.id === item.email.id ? 'ring-2 ring-blue-500' : ''
                          }`}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 truncate">{item.email.subject}</p>
                              <p className="text-sm text-gray-500">From: {item.email.from_name || item.email.from_address}</p>
                            </div>
                            <span className="text-xs">{categoryLabels[item.classification.category] || item.classification.category}</span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{item.classification.summary}</p>
                          {item.draft && (
                            <span className={`inline-block mt-2 text-xs px-2 py-1 rounded ${statusColors[item.draft.status]}`}>
                              Draft: {item.draft.status}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {selectedItem && (
              <div className="bg-white rounded-lg border p-4 sticky top-4">
                <h2 className="text-lg font-semibold mb-2">{selectedItem.email.subject}</h2>
                <div className="text-sm text-gray-600 mb-4">
                  <p><strong>From:</strong> {selectedItem.email.from_name} &lt;{selectedItem.email.from_address}&gt;</p>
                  <p><strong>To:</strong> {selectedItem.email.to_address}</p>
                  <p><strong>Category:</strong> {categoryLabels[selectedItem.classification.category]}</p>
                  <p><strong>Priority:</strong> <span className={`px-2 py-0.5 rounded text-xs ${priorityColors[selectedItem.classification.priority]}`}>{selectedItem.classification.priority}</span></p>
                </div>
                
                <div className="bg-gray-50 rounded p-3 mb-4 max-h-48 overflow-y-auto">
                  <h4 className="text-xs uppercase text-gray-500 mb-1">Original Email</h4>
                  <pre className="text-sm whitespace-pre-wrap">{selectedItem.email.body}</pre>
                </div>

                {selectedItem.draft && (
                  <div className="border rounded p-3 mb-4">
                    <h4 className="text-xs uppercase text-gray-500 mb-1">Draft Reply</h4>
                    <p className="text-sm font-medium mb-2">{selectedItem.draft.subject}</p>
                    <pre className="text-sm whitespace-pre-wrap bg-blue-50 p-2 rounded max-h-48 overflow-y-auto">{selectedItem.draft.body}</pre>
                    <div className="flex gap-2 mt-3">
                      {selectedItem.draft.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleApprove(selectedItem.draft!.id)}
                            disabled={loading || !approverName}
                            className="flex-1 px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                          >
                            ✓ Approve
                          </button>
                          <button
                            onClick={() => handleReject(selectedItem.draft!.id, 'Not appropriate')}
                            disabled={loading || !approverName}
                            className="flex-1 px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                          >
                            ✗ Reject
                          </button>
                        </>
                      )}
                      {selectedItem.draft.status === 'approved' && (
                        <button
                          onClick={() => handleSend(selectedItem.draft!.id)}
                          disabled={loading}
                          className="flex-1 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          📤 Send (Mock)
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {!selectedItem.draft && selectedItem.classification.needs_reply && (
                  <p className="text-sm text-gray-500 italic">No draft generated yet</p>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'drafts' && (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-2">
              {drafts.map((draft) => (
                <div
                  key={draft.id}
                  onClick={() => setSelectedDraft(draft)}
                  className={`p-3 bg-white rounded-lg border cursor-pointer hover:shadow-md transition ${
                    selectedDraft?.id === draft.id ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <p className="font-medium text-gray-900">{draft.subject}</p>
                    <span className={`text-xs px-2 py-1 rounded ${statusColors[draft.status]}`}>
                      {draft.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">Email: {draft.email_id}</p>
                  <p className="text-xs text-gray-400">{new Date(draft.created_at).toLocaleString()}</p>
                </div>
              ))}
              {drafts.length === 0 && (
                <p className="text-gray-400 text-center py-8">No drafts yet. Run triage to generate drafts.</p>
              )}
            </div>

            {selectedDraft && (
              <div className="bg-white rounded-lg border p-4 sticky top-4">
                <h2 className="text-lg font-semibold mb-2">{selectedDraft.subject}</h2>
                <div className="text-sm text-gray-600 mb-4">
                  <p><strong>Status:</strong> <span className={`px-2 py-0.5 rounded text-xs ${statusColors[selectedDraft.status]}`}>{selectedDraft.status}</span></p>
                  <p><strong>Created:</strong> {new Date(selectedDraft.created_at).toLocaleString()}</p>
                  {selectedDraft.approved_by && <p><strong>Approved by:</strong> {selectedDraft.approved_by}</p>}
                  {selectedDraft.sent_at && <p><strong>Sent:</strong> {new Date(selectedDraft.sent_at).toLocaleString()}</p>}
                </div>
                
                <pre className="text-sm whitespace-pre-wrap bg-gray-50 p-3 rounded max-h-64 overflow-y-auto">{selectedDraft.body}</pre>

                <div className="flex gap-2 mt-4">
                  {selectedDraft.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleApprove(selectedDraft.id)}
                        disabled={loading || !approverName}
                        className="flex-1 px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => handleReject(selectedDraft.id, 'Not appropriate')}
                        disabled={loading || !approverName}
                        className="flex-1 px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                      >
                        ✗ Reject
                      </button>
                    </>
                  )}
                  {selectedDraft.status === 'approved' && (
                    <button
                      onClick={() => handleSend(selectedDraft.id)}
                      disabled={loading}
                      className="flex-1 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                    >
                      📤 Send (Mock)
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Entity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actor</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Details</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm font-medium">
                      <span className={`px-2 py-1 rounded text-xs ${
                        log.action.includes('blocked') ? 'bg-red-100 text-red-800' :
                        log.action.includes('approved') ? 'bg-green-100 text-green-800' :
                        log.action.includes('sent') ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      {log.entity_type}/{log.entity_id.slice(0, 8)}...
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">{log.actor}</td>
                    <td className="px-4 py-2 text-sm text-gray-500 max-w-xs truncate">
                      {log.details ? JSON.stringify(log.details).slice(0, 50) : '-'}
                    </td>
                  </tr>
                ))}
                {auditLogs.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-gray-400">No audit logs yet</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>

      <footer className="border-t bg-white mt-8">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500">
          AI Inbox Triage Agent • Human approval required for all outbound messages • Mock outbox (no real emails sent)
        </div>
      </footer>
    </div>
  );
}

export default App;
