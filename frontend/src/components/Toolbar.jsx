import BatchBadge from './BatchBadge';

function Toolbar({ batches, activeBatch, setActiveBatch, loadingBatches, onUploadClick }) {
    return (
        <div className="flex flex-col gap-3 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md px-4 py-3 sm:flex-row sm:items-center sm:justify-between sticky top-0 z-50">
            <div className="flex items-center gap-2.5 sm:w-1/4">
                <div className="relative flex h-8 w-8 items-center justify-center rounded-lg border border-indigo-500/30 bg-gradient-to-b from-indigo-500/20 to-indigo-600/10 shadow-[0_0_15px_-3px_rgba(99,102,241,0.3)]">
                    <svg viewBox="0 0 24 24" className="h-4.5 w-4.5 text-indigo-400" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="8" />
                        <path d="M4 12h16M12 4a13 13 0 0 1 0 16M12 4a13 13 0 0 0 0 16" />
                    </svg>
                </div>
                <h1 className="text-xl font-bold tracking-tight bg-gradient-to-br from-white to-zinc-400 bg-clip-text text-transparent">Orbis</h1>
            </div>

            <div className="flex flex-1 items-center gap-3 sm:justify-center">
                <div className="relative w-full max-w-xs">
                    <select
                        className="w-full appearance-none rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-2 pr-10 text-sm font-medium text-zinc-100 outline-none transition hover:border-zinc-700 hover:bg-zinc-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed"
                        value={activeBatch}
                        onChange={(event) => setActiveBatch(event.target.value)}
                        disabled={loadingBatches}
                    >
                        {(batches || []).map((batchOption) => (
                            <option key={batchOption} value={batchOption} className="bg-zinc-900 text-zinc-100">
                                {batchOption}
                            </option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                        <svg className="h-4 w-4 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-3 sm:w-1/4 sm:justify-end">
                <BatchBadge batch={activeBatch} />
                <button
                    type="button"
                    onClick={onUploadClick}
                    className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-indigo-600/20 transition-all hover:bg-indigo-500 active:scale-95"
                >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    Upload CSV
                </button>
            </div>
        </div>
    );
}

export default Toolbar;
