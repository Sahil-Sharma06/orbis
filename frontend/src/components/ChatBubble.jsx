function ChatBubble({ role, text, sql }) {
	const isUser = role === 'user';

	return (
		<div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
			<div
				className={`max-w-[85%] px-4 py-3 text-sm leading-relaxed ${
					isUser
						? 'rounded-2xl rounded-br-sm bg-blue-600 text-white'
						: 'rounded-2xl rounded-bl-sm bg-gray-800 text-gray-100'
				}`}
			>
				<p className="whitespace-pre-wrap">{text}</p>
				{!isUser && sql ? (
					<details className="mt-3">
						<summary className="cursor-pointer text-xs font-semibold text-gray-300">SQL</summary>
						<pre className="mt-2 overflow-x-auto rounded-lg bg-gray-950 p-3 font-mono text-xs text-green-400">
							{sql}
						</pre>
					</details>
				) : null}
			</div>
		</div>
	);
}

export default ChatBubble;
