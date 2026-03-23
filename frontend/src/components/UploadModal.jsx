import { useState } from 'react';

function UploadModal({ open, onClose, onUploaded }) {
	const [file, setFile] = useState(null);
	const [dragOver, setDragOver] = useState(false);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState('');

	if (!open) {
		return null;
	}

	function resetAndClose() {
		setFile(null);
		setError('');
		setLoading(false);
		onClose();
	}

	function onDrop(event) {
		event.preventDefault();
		setDragOver(false);
		const droppedFile = event.dataTransfer.files?.[0];
		if (!droppedFile) {
			return;
		}
		setFile(droppedFile);
	}

	async function handleUpload() {
		if (!file || loading) {
			return;
		}

		setLoading(true);
		setError('');

		try {
			await onUploaded(file);
			resetAndClose();
		} catch (uploadError) {
			setError(uploadError?.response?.data?.detail || 'Upload failed.');
		} finally {
			setLoading(false);
		}
	}

	return (
		<div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4 backdrop-blur">
			<div className="w-full max-w-md rounded-2xl border border-gray-700 bg-gray-800 p-6 shadow-2xl">
				<div className="mb-4 flex items-center justify-between">
					<h3 className="text-lg font-semibold text-white">Upload CSV</h3>
					<button
						type="button"
						className="rounded border border-gray-600 px-2 py-1 text-xs text-gray-300 hover:bg-gray-700"
						onClick={resetAndClose}
					>
						Close
					</button>
				</div>

				<div
					onDragOver={(event) => {
						event.preventDefault();
						setDragOver(true);
					}}
					onDragLeave={() => setDragOver(false)}
					onDrop={onDrop}
					className={`rounded-xl border-2 border-dashed p-6 text-center transition ${
						dragOver ? 'border-cyan-500 bg-cyan-500/10' : 'border-gray-600 bg-gray-900'
					}`}
				>
					<p className="text-sm text-gray-300">Drag and drop CSV here</p>
					<p className="my-2 text-xs text-gray-500">or</p>
					<label className="inline-flex cursor-pointer rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700">
						Choose File
						<input
							type="file"
							accept=".csv"
							className="hidden"
							onChange={(event) => setFile(event.target.files?.[0] || null)}
						/>
					</label>
					{file ? <p className="mt-3 text-xs text-green-300">{file.name}</p> : null}
				</div>

				{error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}

				<button
					type="button"
					onClick={handleUpload}
					disabled={!file || loading}
					className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
				>
					{loading ? 'Uploading...' : 'Upload'}
				</button>
			</div>
		</div>
	);
}

export default UploadModal;
