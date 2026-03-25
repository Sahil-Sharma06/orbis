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
        <div className="flex h-full flex-col bg-zinc-950/80">
            <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950 px-5 py-3.5 z-10">
                <div className="flex flex-col">
                    <h3 className="text-[15px] font-semibold text-zinc-100">Ask Orbis</h3>
                    <span className="text-xs text-zinc-500 font-medium">AI Assistant</span>
                </div>
                <BatchBadge batch={activeBatch} />
            </div>

            <div ref={listRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-5 scroll-smooth">
                {chatHistory.length === 0 ? (
                    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-5 text-sm text-zinc-400 shadow-sm flex items-start gap-4">
                        <div className="mt-0.5 rounded-full border border-indigo-500/20 bg-indigo-500/10 p-2 text-indigo-400">
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                            </svg>
                        </div>
                        <div>
                            <p className="font-medium text-zinc-300 mb-1">Welcome to Orbis AI</p>
                            <p className="text-zinc-500 leading-relaxed">Ask about orders, invoices, payments, deliveries, customers, or products within the selected dataset.</p>
                        </div>
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
                        <div className="inline-flex items-center gap-2 rounded-2xl rounded-bl-md bg-zinc-800/80 border border-zinc-700/50 px-4 py-3.5 shadow-sm">
                            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.3s]" />
                            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.15s]" />
                            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400" />
                        </div>
                    </div>
                ) : null}
            </div>

            <form onSubmit={handleSubmit} className="border-t border-zinc-800 bg-zinc-950 p-4 z-10">
                <div className="group flex items-end gap-2 rounded-xl border border-zinc-700/60 bg-zinc-800/40 p-2 transition-all focus-within:border-indigo-500/50 focus-within:bg-zinc-800/60 focus-within:shadow-[0_0_15px_-3px_rgba(99,102,241,0.15)]">
                    <textarea
                        className="max-h-32 min-h-[2.5rem] w-full resize-none bg-transparent px-3 py-1.5 text-[15px] text-zinc-100 placeholder-zinc-500 outline-none"
                        placeholder="Ask a question... (Press Enter to send)"
                        rows={rows}
                        value={draft}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        autoFocus
                    />
                    <button
                        type="submit"
                        disabled={!draft.trim() || loading}
                        className="mb-0.5 flex h-9 min-w-[2.25rem] flex-shrink-0 items-center justify-center rounded-lg bg-indigo-600 px-3 font-semibold text-white shadow-sm shadow-indigo-600/20 transition-all hover:bg-indigo-500 active:scale-95 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-600 disabled:shadow-none"
                    >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </div>
            </form>
        </div>
    );
}

export default ChatPanel;
