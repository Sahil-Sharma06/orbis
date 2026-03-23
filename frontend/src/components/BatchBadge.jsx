function BatchBadge({ batch }) {
	return (
		<span className="inline-flex items-center rounded-full border border-sky-700 bg-sky-900/40 px-2.5 py-1 text-xs font-medium uppercase tracking-wide text-sky-300">
			{batch || 'merged'}
		</span>
	);
}

export default BatchBadge;
