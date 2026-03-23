import BatchBadge from './BatchBadge';

function Toolbar({ batches, activeBatch, setActiveBatch, loadingBatches, onUploadClick }) {
	return (
		<div className="flex flex-col gap-3 border-b border-gray-700 bg-gray-900 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
			<div className="flex items-center gap-2">
				<span className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-cyan-500/40 bg-cyan-500/10">
					<svg viewBox="0 0 24 24" className="h-4 w-4 text-cyan-400" fill="none" stroke="currentColor" strokeWidth="1.8">
						<circle cx="12" cy="12" r="8" />
						<path d="M4 12h16M12 4a13 13 0 0 1 0 16M12 4a13 13 0 0 0 0 16" />
					</svg>
				</span>
				<h1 className="text-xl font-bold tracking-tight text-white">Orbis</h1>
			</div>

			<div className="flex flex-1 items-center gap-3 sm:justify-center">
				<select
					className="w-full max-w-xs rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 outline-none transition focus:border-cyan-500"
					value={activeBatch}
					onChange={(event) => setActiveBatch(event.target.value)}
					disabled={loadingBatches}
				>
					{(batches || []).map((batchOption) => (
						<option key={batchOption} value={batchOption}>
							{batchOption}
						</option>
					))}
				</select>
			</div>

			<div className="flex items-center gap-3">
				<BatchBadge batch={activeBatch} />
				<button
					type="button"
					onClick={onUploadClick}
					className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
				>
					Upload CSV
				</button>
			</div>
		</div>
	);
}

export default Toolbar;
