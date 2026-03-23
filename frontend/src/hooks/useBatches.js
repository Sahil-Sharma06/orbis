import { useCallback, useEffect, useState } from 'react';

import { fetchBatches } from '../api/client';

export function useBatches() {
	const [batches, setBatches] = useState(['merged']);
	const [loading, setLoading] = useState(true);

	const refetch = useCallback(async () => {
		setLoading(true);
		try {
			const response = await fetchBatches();
			setBatches(response?.batches?.length ? response.batches : ['merged']);
		} catch (error) {
			setBatches(['merged']);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		refetch();
	}, [refetch]);

	return { batches, loading, refetch };
}
