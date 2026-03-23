import { useCallback, useMemo, useState } from 'react';

import { sendChatMessage } from '../api/client';

export function useChat(activeBatch) {
	const [chatHistory, setChatHistory] = useState([]);
	const [loading, setLoading] = useState(false);

	const sendMessage = useCallback(
		async (message) => {
			const trimmed = (message || '').trim();
			if (!trimmed || loading) {
				return;
			}

			const userMsg = {
				id: `u_${Date.now()}`,
				role: 'user',
				text: trimmed,
			};

			setChatHistory((prev) => [...prev, userMsg]);
			setLoading(true);

			try {
				const result = await sendChatMessage({
					message: trimmed,
					batch: activeBatch || 'merged',
				});

				const assistantMsg = {
					id: `s_${Date.now()}`,
					role: 'system',
					text: result?.response || 'No response.',
					sql: result?.sql || '',
					data: result?.data || [],
				};
				setChatHistory((prev) => [...prev, assistantMsg]);
			} catch (error) {
				setChatHistory((prev) => [
					...prev,
					{
						id: `e_${Date.now()}`,
						role: 'system',
						text: 'Failed to contact Orbis backend. Please try again.',
						sql: '',
						data: [],
					},
				]);
			} finally {
				setLoading(false);
			}
		},
		[activeBatch, loading]
	);

	const messageCount = useMemo(() => chatHistory.length, [chatHistory]);

	return { chatHistory, sendMessage, loading, messageCount };
}
