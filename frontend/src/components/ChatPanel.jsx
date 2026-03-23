import { useEffect, useRef, useState } from 'react';

import BatchBadge from './BatchBadge';
import ChatBubble from './ChatBubble';

function ChatPanel({ activeBatch, chatHistory, sendMessage, loading }) {
	const [draft, setDraft] = useState('');
	const [rows, setRows] = useState(1);
	const listRef = useRef(null);

	useEffect(() => {
		if (!listRef.current) {
			return;
		}
		listRef.current.scrollTop = listRef.current.scrollHeight;
	}, [chatHistory, loading]);

	function handleSubmit(event) {
		event.preventDefault();
		const message = draft.trim();
		if (!message || loading) {
			return;
		}
		sendMessage(message);
		setDraft('');
		setRows(1);
	}

	function handleKeyDown(event) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSubmit(event);
		}
	}

	function handleInputChange(event) {
		const value = event.target.value;
		setDraft(value);
		const nextRows = Math.min(4, Math.max(1, value.split('\n').length));
		setRows(nextRows);
	}

	return (
		<div className="flex h-full flex-col bg-gray-950">
			<div className="flex items-center justify-between border-b border-gray-700 px-4 py-3">
				<h3 className="text-sm font-semibold text-gray-200">Ask Orbis</h3>
				<BatchBadge batch={activeBatch} />
			</div>

			<div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
				{chatHistory.length === 0 ? (
					<div className="rounded-xl border border-gray-800 bg-gray-900 p-4 text-sm text-gray-400">
						Ask about orders, invoices, payments, deliveries, customers, or products.
					</div>
				) : null}

				{chatHistory.map((message) => (
					<ChatBubble
						key={message.id}
						role={message.role}
						text={message.text}
						sql={message.sql}
					/>
				))}

				{loading ? (
					<div className="flex justify-start">
						<div className="inline-flex items-center gap-2 rounded-2xl rounded-bl-sm bg-gray-800 px-4 py-3">
							<span className="h-2 w-2 animate-bounce rounded-full bg-gray-300 [animation-delay:-0.3s]" />
							<span className="h-2 w-2 animate-bounce rounded-full bg-gray-300 [animation-delay:-0.15s]" />
							<span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" />
						</div>
					</div>
				) : null}
			</div>

			<form onSubmit={handleSubmit} className="border-t border-gray-700 p-4">
				<div className="flex items-end gap-2 rounded-xl border border-gray-700 bg-gray-800 p-2">
					<textarea
						className="max-h-28 min-h-[2.5rem] w-full resize-none bg-transparent px-2 py-1 text-sm text-gray-100 outline-none"
						placeholder="Ask about the selected batch..."
						rows={rows}
						value={draft}
						onChange={handleInputChange}
						onKeyDown={handleKeyDown}
					/>
					<button
						type="submit"
						disabled={!draft.trim() || loading}
						className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
					>
						Send
					</button>
				</div>
			</form>
		</div>
	);
}

export default ChatPanel;
