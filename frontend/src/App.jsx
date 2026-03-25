import { useEffect, useMemo, useState } from 'react';

import { uploadCsv } from './api/client';
import ChatPanel from './components/ChatPanel';
import GraphPanel from './components/GraphPanel';
import NodeInspector from './components/NodeInspector';
import Toolbar from './components/Toolbar';
import UploadModal from './components/UploadModal';
import { useBatches } from './hooks/useBatches';
import { useChat } from './hooks/useChat';
import { useGraph } from './hooks/useGraph';

function App() {
    const { batches, loading: loadingBatches, refetch: refetchBatches } = useBatches();
    const [activeBatch, setActiveBatch] = useState('merged');
    const [selectedNode, setSelectedNode] = useState(null);
    const [uploadOpen, setUploadOpen] = useState(false);
    const [uploadMessage, setUploadMessage] = useState('');

    const { nodes, edges, loading: loadingGraph, error } = useGraph(activeBatch);
    const { chatHistory, sendMessage, loading: chatLoading } = useChat(activeBatch);

    const graphData = useMemo(() => ({ nodes, edges }), [nodes, edges]);

    useEffect(() => {
        if (loadingBatches || !batches.length) {
            return;
        }

        if (activeBatch === 'merged' && batches.length > 1) {
            setActiveBatch(batches[batches.length - 1]);
        }
    }, [activeBatch, batches, loadingBatches]);

    async function handleUpload(file) {
        const result = await uploadCsv(file);
        setUploadMessage(
            `Uploaded successfully: ${result.batch_id} (${result.records_inserted} records inserted)`
        );
        setTimeout(() => setUploadMessage(''), 5000);
        await refetchBatches();
        setActiveBatch(result.batch_id);
    }

    return (
        <div className="h-screen w-full bg-[#09090b] text-zinc-100 overflow-hidden">
            <div className="flex h-full w-full flex-col lg:flex-row">
                <section className="flex h-[55vh] w-full flex-col border-b border-r-0 border-zinc-800 lg:h-full lg:w-3/5 lg:border-b-0 lg:border-r relative">
                    <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAyKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] pointer-events-none"></div>
                    <Toolbar
                        batches={batches}
                        activeBatch={activeBatch}
                        setActiveBatch={setActiveBatch}
                        loadingBatches={loadingBatches}
                        onUploadClick={() => setUploadOpen(true)}
                    />

                    {uploadMessage ? (
                        <div className="mx-4 mt-4 animate-slide-in rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400 shadow-lg shadow-emerald-500/5 flex items-center justify-between z-10">
                            <div className="flex items-center gap-2">
                                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                                {uploadMessage}
                            </div>
                            <button onClick={() => setUploadMessage('')} className="text-emerald-500 hover:text-emerald-300">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                            </button>
                        </div>
                    ) : null}

                    <div className="relative min-h-0 flex-1 p-4 lg:p-6 z-10 flex">
                        <GraphPanel
                            nodes={graphData.nodes}
                            edges={graphData.edges}
                            loading={loadingGraph}
                            error={error}
                            onNodeSelect={setSelectedNode}
                        />
                        <NodeInspector selectedNode={selectedNode} onClose={() => setSelectedNode(null)} />
                    </div>
                </section>

                <section className="flex h-[45vh] w-full flex-col lg:h-full lg:w-2/5">
                    <div className="min-h-0 flex-1 h-full">
                        <ChatPanel
                            activeBatch={activeBatch}
                            chatHistory={chatHistory}
                            sendMessage={sendMessage}
                            loading={chatLoading}
                        />
                    </div>
                </section>
            </div>

            <UploadModal
                open={uploadOpen}
                onClose={() => setUploadOpen(false)}
                onUploaded={handleUpload}
            />
        </div>
    );
}

export default App;
