import { useEffect, useMemo, useRef } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';

cytoscape.use(dagre);

const NODE_COLORS = {
	customer: '#3B82F6',
	order: '#22C55E',
	product: '#F97316',
	invoice: '#EF4444',
	payment: '#A855F7',
	delivery: '#14B8A6',
	address: '#6B7280',
	order_item: '#EAB308',
};

function GraphPanel({ nodes, edges, loading, error, onNodeSelect }) {
	const containerRef = useRef(null);
	const cyRef = useRef(null);

	const elements = useMemo(() => {
		const nodeElements = nodes.map((node) => ({
			data: {
				id: node.id,
				label: node.label,
				type: node.type,
				color: NODE_COLORS[node.type] || '#94A3B8',
				...node.data,
			},
		}));

		const edgeElements = edges.map((edge, index) => ({
			data: {
				id: `e_${index}_${edge.source}_${edge.target}`,
				source: edge.source,
				target: edge.target,
				relationship: edge.relationship,
			},
		}));

		return [...nodeElements, ...edgeElements];
	}, [nodes, edges]);

	useEffect(() => {
		if (!containerRef.current) {
			return undefined;
		}

		if (cyRef.current) {
			cyRef.current.destroy();
		}

		const cy = cytoscape({
			container: containerRef.current,
			elements,
			style: [
				{
					selector: 'node',
					style: {
						label: 'data(label)',
						'font-size': 10,
						'text-valign': 'center',
						'text-halign': 'center',
						color: '#E5E7EB',
						'background-color': 'data(color)',
						width: 42,
						height: 42,
						'border-width': 2,
						'border-color': '#111827',
					},
				},
				{
					selector: 'edge',
					style: {
						width: 2,
						'line-color': '#4B5563',
						'target-arrow-color': '#4B5563',
						'target-arrow-shape': 'triangle',
						'curve-style': 'bezier',
					},
				},
			],
			layout: {
				name: 'dagre',
				rankDir: 'LR',
				nodeSep: 60,
				rankSep: 120,
			},
			wheelSensitivity: 0.2,
		});

		cy.on('tap', 'node', (event) => {
			const nodeData = event.target.data();
			onNodeSelect?.(nodeData);
		});

		cyRef.current = cy;
		return () => {
			cy.destroy();
		};
	}, [elements, onNodeSelect]);

	if (loading) {
		return (
			<div className="flex h-full w-full items-center justify-center rounded-xl bg-gray-900">
				<div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
			</div>
		);
	}

	if (error) {
		return (
			<div className="flex h-full w-full items-center justify-center rounded-xl bg-gray-900 px-4 text-center text-sm text-red-300">
				{error}
			</div>
		);
	}

	if (!nodes.length) {
		return (
			<div className="flex h-full w-full items-center justify-center rounded-xl bg-gray-900 px-4 text-center text-sm text-gray-400">
				No graph data found for this batch.
			</div>
		);
	}

	return <div ref={containerRef} className="h-full w-full rounded-xl bg-gray-900" />;
}

export default GraphPanel;
