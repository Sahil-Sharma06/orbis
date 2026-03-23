import axios from 'axios';

const api = axios.create({
	baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
	headers: {
		'Content-Type': 'application/json',
	},
});

export async function fetchBatches() {
	const { data } = await api.get('/api/batches');
	return data;
}

export async function fetchGraph(batch = 'merged') {
	const { data } = await api.get('/api/graph', {
		params: { batch },
	});
	return data;
}

export async function sendChatMessage(payload) {
	const { data } = await api.post('/api/chat', payload);
	return data;
}

export async function uploadCsv(file) {
	const formData = new FormData();
	formData.append('file', file);
	const { data } = await api.post('/api/ingest', formData, {
		headers: {
			'Content-Type': 'multipart/form-data',
		},
	});
	return data;
}
