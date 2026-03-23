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
	const isLargeGraph = nodes.length > 220;
	const isVeryLargeGraph = nodes.length > 500;

	const { visibleNodes, visibleEdges } = useMemo(() => {
		if (!isVeryLargeGraph) {
			return { visibleNodes: nodes, visibleEdges: edges };
		}

		const nodesWithoutItems = nodes.filter((node) => node.type !== 'order_item');
		const allowedIds = new Set(nodesWithoutItems.map((node) => node.id));
		const edgesWithoutItems = edges.filter(
			(edge) => allowedIds.has(edge.source) && allowedIds.has(edge.target)
		);

		return {
			visibleNodes: nodesWithoutItems,
			visibleEdges: edgesWithoutItems,
		};
	}, [edges, isVeryLargeGraph, nodes]);

	const elements = useMemo(() => {
		const nodeElements = visibleNodes.map((node) => ({
			data: {
				id: node.id,
				label: node.label,
				type: node.type,
				color: NODE_COLORS[node.type] || '#94A3B8',
				...node.data,
			},
		}));

		const edgeElements = visibleEdges.map((edge, index) => ({
			data: {
				id: `e_${index}_${edge.source}_${edge.target}`,
				source: edge.source,
				target: edge.target,
				relationship: edge.relationship,
			},
		}));

		return [...nodeElements, ...edgeElements];
	}, [visibleNodes, visibleEdges]);

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
			pixelRatio: 1,
			hideEdgesOnViewport: true,
			textureOnViewport: true,
			motionBlur: false,
			style: [
				{
					selector: 'node',
					style: {
						label: isLargeGraph ? '' : 'data(label)',
						'font-size': isLargeGraph ? 8 : 10,
						'text-valign': 'center',
						'text-halign': 'center',
						color: '#E5E7EB',
						'background-color': 'data(color)',
						width: isLargeGraph ? 16 : 42,
						height: isLargeGraph ? 16 : 42,
						'border-width': 2,
						'border-color': '#111827',
					},
				},
				{
					selector: 'edge',
					style: {
						width: isLargeGraph ? 1 : 2,
						'line-color': '#4B5563',
						'target-arrow-color': '#4B5563',
						'target-arrow-shape': isLargeGraph ? 'none' : 'triangle',
						'curve-style': 'bezier',
						opacity: isLargeGraph ? 0.35 : 0.9,
					},
				},
			],
			layout: isVeryLargeGraph
				? {
						name: 'concentric',
						fit: true,
						animate: false,
						padding: 48,
						minNodeSpacing: 20,
						concentric: (node) => {
							const type = node.data('type');
							if (type === 'customer') return 8;
							if (type === 'order') return 7;
							if (type === 'delivery') return 6;
							if (type === 'invoice') return 5;
							if (type === 'payment') return 4;
							if (type === 'address') return 3;
							if (type === 'product') return 2;
							return 1;
						},
						levelWidth: () => 1,
				  }
				: isLargeGraph
				? {
						name: 'cose',
						animate: false,
						fit: true,
						padding: 48,
						nodeRepulsion: 6000,
						edgeElasticity: 40,
						gravity: 0.3,
						numIter: 350,
				  }
				: {
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
	}, [elements, isLargeGraph, isVeryLargeGraph, onNodeSelect]);

	if (loading) {
		return (
			<div className="flex items-center justify-center w-full h-full bg-gray-900 rounded-xl">
				<div className="w-8 h-8 border-2 rounded-full animate-spin border-cyan-500 border-t-transparent" />
			</div>
		);
	}

	if (error) {
		return (
			<div className="flex items-center justify-center w-full h-full px-4 text-sm text-center text-red-300 bg-gray-900 rounded-xl">
				{error}
			</div>
		);
	}

	if (!nodes.length) {
		return (
			<div className="flex items-center justify-center w-full h-full px-4 text-sm text-center text-gray-400 bg-gray-900 rounded-xl">
				No graph data found for this batch.
			</div>
		);
	}

	return (
		<div className="relative w-full h-full bg-gray-900 rounded-xl">
			<div ref={containerRef} className="w-full h-full bg-gray-900 rounded-xl" />
			<div className="absolute px-2 py-1 text-xs text-gray-300 border border-gray-700 rounded-md pointer-events-none left-3 top-3 bg-gray-950/85">
				{visibleNodes.length}/{nodes.length} nodes, {visibleEdges.length}/{edges.length} edges
				{isVeryLargeGraph
					? ' - performance mode (order items hidden)'
					: isLargeGraph
						? ' - dense view enabled'
						: ''}
			</div>
		</div>
	);
}

export default GraphPanel;
