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
		await refetchBatches();
		setActiveBatch(result.batch_id);
	}

	return (
		<div className="h-screen w-full bg-gray-950 text-gray-100">
			<div className="flex h-full w-full flex-col lg:flex-row">
				<section className="flex h-[55vh] w-full flex-col border-b border-r-0 border-gray-700 lg:h-full lg:w-3/5 lg:border-b-0 lg:border-r">
					<Toolbar
						batches={batches}
						activeBatch={activeBatch}
						setActiveBatch={setActiveBatch}
						loadingBatches={loadingBatches}
						onUploadClick={() => setUploadOpen(true)}
					/>

					{uploadMessage ? (
						<div className="mx-4 mt-3 rounded-lg border border-green-800 bg-green-900/30 px-3 py-2 text-sm text-green-300">
							{uploadMessage}
						</div>
					) : null}

					<div className="relative min-h-0 flex-1 p-4">
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
					<div className="min-h-0 flex-1">
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
