import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from './lib/api'; // Use our custom api client
import { ArrowLeft, Clock, Gauge, ChefHat, Heart } from 'lucide-react';
import { UserSwitch } from './components/UserSwitch';
import type { Recipe } from './types';

const ResultsPage = () => {
    const [searchParams] = useSearchParams();
    const query = searchParams.get('q') || '';
    const navigate = useNavigate();
    const [recipes, setRecipes] = useState<Recipe[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [aiMessage, setAiMessage] = useState('');

    // --- Chat State ---
    const [chatInput, setChatInput] = useState('');
    const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'assistant', content: string }[]>([]);
    const [isChatLoading, setIsChatLoading] = useState(false);

    const handleChatSubmit = async (text: string) => {
        if (!text.trim()) return;

        // 1. Add user message
        const newUserMsg = { role: 'user' as const, content: text };
        setChatHistory(prev => [...prev, newUserMsg]);
        setChatInput('');
        setIsChatLoading(true);

        try {
            // 2. Call Search API with Refinement
            // We use the original 'query' from the URL, and use the chat text as 'refinement'
            // This fulfills the user's request to "refresh recipes" based on chat input.
            // 2. Call Search API with Refinement
            // We use the original 'query' from the URL, and use the chat text as 'refinement'
            // This fulfills the user's request to "refresh recipes" based on chat input.
            const res = await api.post('/api/search', {
                query: query,
                limit: 5,
                refinement: text
            });

            // 3. Update Recipes
            if (res.data.candidates && res.data.candidates.length > 0) {
                setRecipes(res.data.candidates);
            }

            // 4. Add AI response to chat
            const reply = res.data.ai_message || "Recipes updated based on your feedback.";
            setChatHistory(prev => [...prev, { role: 'assistant', content: reply }]);

        } catch (err) {
            console.error(err);
            setChatHistory(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error while updating the recipes." }]);
        } finally {
            setIsChatLoading(false);
        }
    };

    useEffect(() => {
        const fetchRecipes = async () => {
            if (!query) return;

            // 2. Network Call (Always)
            setLoading(true);
            setRecipes([]);
            setAiMessage('');
            setChatHistory([]);
            setError('');

            try {
                const res = await api.post('/api/search', { query, limit: 5 });

                // No Cache Saving
                // sessionStorage.setItem(cacheKey, JSON.stringify(res.data));

                if (res.data.candidates) {
                    setRecipes(res.data.candidates);
                    setAiMessage(res.data.ai_message || '');
                } else if (res.data.recipe_id) {
                    setRecipes([res.data]);
                    setAiMessage('');
                } else {
                    setRecipes([]);
                }
            } catch (err: any) {
                console.error(err);
                const msg = err.response?.data?.detail
                    ? JSON.stringify(err.response.data.detail)
                    : (err.message || 'Unknown error');
                setError(`Connection Failed: ${msg}. (Status: ${err.response?.status})`);
            } finally {
                setLoading(false);
            }
        };

        fetchRecipes();
    }, [query]);

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header */}
            <header className="bg-white border-b border-slate-100 sticky top-0 z-10">
                <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
                    <button onClick={() => navigate('/')} className="p-2 hover:bg-slate-50 rounded-full transition-colors text-slate-600">
                        <ArrowLeft size={24} />
                    </button>
                    <h1 className="text-lg font-semibold text-slate-800">
                        Results for "<span className="text-primary">{query}</span>"
                    </h1>
                    <div className="flex items-center gap-4">
                        <UserSwitch />
                    </div>
                </div>
            </header>

            {/* Content */}
            <main className="max-w-5xl mx-auto px-4 py-8">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-64 space-y-4">
                        <div className="animate-spin text-orange-500">
                            <Gauge size={48} />
                        </div>
                        <div className="text-center space-y-2">
                            <h3 className="text-lg font-medium text-slate-800 animate-pulse">Consulting the AI Chef...</h3>
                            <p className="text-slate-500 text-sm">Analyzing ingredients & crafting advice...</p>
                        </div>
                    </div>
                ) : error ? (
                    <div className="text-center py-12">
                        <p className="text-red-500 mb-4">{error}</p>
                        <button onClick={() => window.location.reload()} className="px-4 py-2 bg-slate-200 rounded hover:bg-slate-300">Retry</button>
                    </div>
                ) : recipes.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">No recipes found. Try different ingredients.</div>
                ) : (
                    <>
                        {/* --- AI Chef Consultant Section (Interactive) --- */}
                        <div className="mb-8 bg-white rounded-2xl border border-orange-100 shadow-sm overflow-hidden">
                            <div className="p-4 bg-orange-50/50 border-b border-orange-100 flex items-center gap-3">
                                <div className="p-2 bg-white rounded-full text-orange-500 shadow-sm">
                                    <ChefHat size={24} />
                                </div>
                                <h2 className="font-bold text-slate-800">AI Chef Consultant</h2>
                            </div>

                            {/* Chat Area */}
                            <div className="p-6 bg-slate-50/30">
                                {/* Message List */}
                                <div className="space-y-4 mb-4 max-h-[400px] overflow-y-auto">
                                    {/* Initial Greeting */}
                                    {aiMessage && (
                                        <div className="flex gap-3">
                                            <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 shrink-0 mt-1">
                                                <ChefHat size={16} />
                                            </div>
                                            <div className="bg-white p-3 rounded-2xl rounded-tl-none border border-slate-100 shadow-sm text-slate-700 text-sm leading-relaxed max-w-[85%]">
                                                {aiMessage}
                                            </div>
                                        </div>
                                    )}

                                    {/* User Follow-up History */}
                                    {chatHistory.map((msg, idx) => (
                                        <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 ${msg.role === 'user' ? 'bg-slate-200 text-slate-600' : 'bg-orange-100 text-orange-600'
                                                }`}>
                                                {msg.role === 'user' ? <div className="text-xs font-bold">You</div> : <ChefHat size={16} />}
                                            </div>
                                            <div className={`p-3 rounded-2xl border shadow-sm text-sm leading-relaxed max-w-[85%] ${msg.role === 'user'
                                                ? 'bg-slate-800 text-white rounded-tr-none border-slate-700'
                                                : 'bg-white text-slate-700 rounded-tl-none border-slate-100'
                                                }`}>
                                                {msg.content}
                                            </div>
                                        </div>
                                    ))}

                                    {isChatLoading && (
                                        <div className="flex gap-3">
                                            <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 shrink-0 mt-1">
                                                <ChefHat size={16} />
                                            </div>
                                            <div className="bg-white p-3 rounded-2xl rounded-tl-none border border-slate-100 shadow-sm text-slate-400 text-sm flex items-center gap-2">
                                                <div className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                                <div className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                                <div className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Input Area */}
                                <form
                                    onSubmit={(e) => {
                                        e.preventDefault();
                                        handleChatSubmit(chatInput);
                                    }}
                                    className="relative flex gap-2"
                                >
                                    <input
                                        type="text"
                                        value={chatInput}
                                        onChange={(e) => setChatInput(e.target.value)}
                                        placeholder="Ask follow-up questions (e.g., 'I don't like spicy food', 'Any simpler way?')"
                                        className="flex-1 bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all shadow-sm"
                                        disabled={isChatLoading}
                                    />
                                    <button
                                        type="submit"
                                        disabled={!chatInput.trim() || isChatLoading}
                                        className="bg-slate-900 text-white px-5 py-2 rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                                    >
                                        Send
                                    </button>
                                </form>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {recipes.map((recipe, idx) => (
                                <div
                                    key={recipe.recipe_id || idx}
                                    onClick={() => navigate(`/recipe/${recipe.recipe_id}`, { state: { recipe } })}
                                    className="bg-white rounded-2xl overflow-hidden border border-slate-100 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 cursor-pointer group"
                                >
                                    {/* Image Area */}
                                    <div className="aspect-[4/3] bg-slate-100 relative overflow-hidden flex items-center justify-center">
                                        {recipe.cover_image ? (
                                            <img
                                                src={recipe.cover_image}
                                                alt={recipe.recipe_name}
                                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                                onError={(e) => {
                                                    e.currentTarget.style.display = 'none';
                                                    e.currentTarget.parentElement?.classList.add('bg-slate-200');
                                                }}
                                            />
                                        ) : (
                                            <ChefHat size={48} className="text-slate-300" />
                                        )}
                                        {/* Fallback Icon if image hidden */}
                                        <ChefHat size={48} className="text-slate-300 absolute hidden group-hover:block" />

                                        <div className="absolute top-3 right-3 bg-white/90 backdrop-blur px-2 py-1 rounded-full text-xs font-bold text-primary shadow-sm">
                                            95% Match
                                        </div>
                                    </div>

                                    {/* Content Area */}
                                    <div className="p-5">
                                        <h3 className="text-xl font-bold text-slate-800 mb-2 line-clamp-1">{recipe.recipe_name}</h3>

                                        <div className="flex flex-wrap gap-2 mb-4">
                                            {recipe.tags?.slice(0, 3).map(tag => (
                                                <span key={tag} className="px-2 py-1 bg-slate-50 text-slate-500 text-xs rounded-md border border-slate-100">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>

                                        <div className="flex items-center justify-between text-slate-400 text-sm pt-4 border-t border-slate-50">
                                            <div className="flex items-center gap-1">
                                                <Clock size={16} />
                                                <span>20 min</span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <Gauge size={16} />
                                                <span>Easy</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
};

export default ResultsPage;
