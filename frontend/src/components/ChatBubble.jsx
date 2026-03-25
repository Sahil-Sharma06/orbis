function ChatBubble({ role, text, sql }) {
    const isUser = role === 'user';

    return (
        <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`max-w-[85%] px-4 py-3 text-[15px] leading-relaxed relative ${
                    isUser
                        ? 'rounded-2xl rounded-br-md bg-indigo-600 text-white shadow-sm shadow-indigo-900/20'
                        : 'rounded-2xl rounded-bl-md bg-zinc-800/80 border border-zinc-700/50 text-zinc-200 shadow-sm'
                }`}
            >
                <div className="whitespace-pre-wrap">{text}</div>
                {!isUser && sql ? (
                    <details className="mt-3 group">
                        <summary className="text-xs font-semibold text-zinc-400 cursor-pointer select-none hover:text-zinc-300 transition-colors flex items-center gap-1.5 marker:content-['']">
                            <svg className="w-3.5 h-3.5 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                            </svg>
                            View Generated SQL
                        </summary>
                        <div className="mt-2 rounded-lg border border-zinc-700/50 bg-zinc-950/80 p-1">
                            <div className="flex items-center justify-between px-3 py-1.5 border-b border-zinc-800/50 bg-zinc-900/50 rounded-t-lg">
                                <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">SQL</span>
                            </div>
                            <pre className="p-3 overflow-x-auto font-mono text-xs text-indigo-300 leading-relaxed">
                                {sql}
                            </pre>
                        </div>
                    </details>
                ) : null}
            </div>
        </div>
    );
}

export default ChatBubble;
