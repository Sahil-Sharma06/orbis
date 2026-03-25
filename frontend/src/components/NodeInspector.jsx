const TYPE_COLOR = {
	customer: 'bg-blue-500/20 text-blue-300 border-blue-600/40',
	order: 'bg-green-500/20 text-green-300 border-green-600/40',
	product: 'bg-orange-500/20 text-orange-300 border-orange-600/40',
	invoice: 'bg-red-500/20 text-red-300 border-red-600/40',
	payment: 'bg-purple-500/20 text-purple-300 border-purple-600/40',
	delivery: 'bg-teal-500/20 text-teal-300 border-teal-600/40',
	address: 'bg-zinc-500/20 text-zinc-300 border-zinc-600/40',
	order_item: 'bg-yellow-500/20 text-yellow-300 border-yellow-600/40',
};

function NodeInspector({ selectedNode, onClose }) {
	if (!selectedNode) {
		return null;
	}

	const entries = Object.entries(selectedNode).filter(
		([key]) => !['color'].includes(key)
	);

	return (
		<aside className="absolute right-6 top-6 z-10 w-full max-w-sm animate-slide-in rounded-xl shadow-sm border border-zinc-800 bg-zinc-900/50/95 backdrop-blur-md p-4 shadow-2xl shadow-black/50">
			<div className="mb-3 flex items-start justify-between">
				<div>
					<h3 className="text-lg font-semibold text-white">Node Inspector</h3>
					<span
						className={`mt-2 inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-wide ${
							TYPE_COLOR[selectedNode.type] || 'bg-slate-500/20 text-slate-300 border-slate-600/40'
						}`}
					>
						{selectedNode.type}
					</span>
				</div>
				<button
					type="button"
					onClick={onClose}
					className="rounded-md border border-zinc-800 px-2 py-1 text-sm text-zinc-300 transition hover:bg-zinc-700"
				>
					X
				</button>
			</div>

			<div className="max-h-80 overflow-y-auto rounded-lg border border-zinc-800">
				<table className="w-full text-sm">
					<tbody>
						{entries.map(([key, value]) => (
							<tr key={key} className="border-b border-zinc-800 last:border-b-0">
								<td className="w-2/5 bg-zinc-900/50 px-3 py-2 text-zinc-400">{key}</td>
								<td className="break-all px-3 py-2 text-zinc-100">{String(value)}</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</aside>
	);
}

export default NodeInspector;
