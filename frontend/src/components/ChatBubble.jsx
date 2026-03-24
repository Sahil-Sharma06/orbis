
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
						<summary className="text-xs font-semibold text-gray-300 cursor-pointer">SQL</summary>
						<pre className="p-3 mt-2 overflow-x-auto font-mono text-xs text-green-400 rounded-lg bg-gray-950">
							{sql}
						</pre>
					</details>
				) : null}
			</div>
		</div>
	);
}

export default ChatBubble;
