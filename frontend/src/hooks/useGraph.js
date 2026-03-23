import { useEffect, useState } from 'react';

import { fetchGraph } from '../api/client';

export function useGraph(activeBatch) {
	const [nodes, setNodes] = useState([]);
	const [edges, setEdges] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');

	useEffect(() => {
		let mounted = true;

		async function loadGraph() {
			setLoading(true);
			setError('');
			try {
				const response = await fetchGraph(activeBatch || 'merged');
				if (!mounted) {
					return;
				}
				setNodes(response?.nodes || []);
				setEdges(response?.edges || []);
			} catch (loadError) {
				if (!mounted) {
					return;
				}
				setError('Unable to load graph data.');
				setNodes([]);
				setEdges([]);
			} finally {
				if (mounted) {
					setLoading(false);
				}
			}
		}

		loadGraph();
		return () => {
			mounted = false;
		};
	}, [activeBatch]);

	return { nodes, edges, loading, error };
}
