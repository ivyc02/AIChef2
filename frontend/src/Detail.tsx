import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Clock, Flame, Heart, Share2, ChevronRight, ChefHat } from 'lucide-react';
import type { Recipe } from './types';
import { cn } from './lib/utils';
import { useUser } from './context/UserContext';
import { getNamespacedKey } from './lib/storage';

const RecipeDetail = () => {
    const navigate = useNavigate();
    const location = useLocation();

    // In a real app, we might fetch by ID if state is missing
    const recipe = location.state?.recipe as Recipe;

    const [isFavorite, setIsFavorite] = useState(false);
    const { username } = useUser();

    useEffect(() => {
        window.scrollTo(0, 0);
        // Initialize isFavorite state based on localStorage
        if (recipe?.recipe_id) {
            const favKey = getNamespacedKey('aichef_favorites', username);
            const favIds = JSON.parse(localStorage.getItem(favKey) || '[]');
            setIsFavorite(favIds.includes(recipe.recipe_id));
        }
    }, [recipe?.recipe_id, username]);

    const toggleFavorite = () => {
        // 1. Manage List of IDs
        const favKey = getNamespacedKey('aichef_favorites', username);
        const mapKey = getNamespacedKey('aichef_saved_recipes', username);

        const favIds = JSON.parse(localStorage.getItem(favKey) || '[]');
        let newFavIds;

        // 2. Manage Recipe Objects Map (Data Source for Favorites Page)
        const savedRecipes = JSON.parse(localStorage.getItem(mapKey) || '{}');

        if (isFavorite) {
            newFavIds = favIds.filter((fid: string) => fid !== recipe.recipe_id);
            delete savedRecipes[recipe.recipe_id];
        } else {
            if (!favIds.includes(recipe.recipe_id)) {
                newFavIds = [...favIds, recipe.recipe_id];
            } else {
                newFavIds = favIds;
            }
            savedRecipes[recipe.recipe_id] = recipe;
        }

        localStorage.setItem(favKey, JSON.stringify(newFavIds));
        localStorage.setItem(mapKey, JSON.stringify(savedRecipes));
        setIsFavorite(!isFavorite);
    };

    if (!recipe) {
        return <div className="p-8 text-center text-red-500">Recipe not found.</div>;
    }

    return (
        <div className="min-h-screen bg-white">
            {/* Hero Image Section */}
            <div className="relative h-96 md:h-[500px]">
                <div className="absolute top-0 left-0 right-0 p-4 z-20 flex justify-between items-start">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-3 bg-white/20 backdrop-blur-md hover:bg-white/30 rounded-full text-white transition-all shadow-sm"
                    >
                        <ArrowLeft size={24} />
                    </button>
                    <div className="flex gap-3">
                        <button
                            className="p-3 bg-white/20 backdrop-blur-md hover:bg-white/30 rounded-full text-white transition-all shadow-sm"
                            onClick={toggleFavorite}
                        >
                            <Heart size={24} className={cn("transition-colors duration-300", isFavorite ? "fill-red-500 text-red-500" : "text-white")} />
                        </button>
                        <button className="p-3 bg-white/20 backdrop-blur-md hover:bg-white/30 rounded-full text-white transition-all shadow-sm">
                            <Share2 size={24} />
                        </button>
                    </div>
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/30 z-10" />

                {recipe.cover_image ? (
                    <img
                        src={recipe.cover_image}
                        alt={recipe.recipe_name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                            e.currentTarget.style.display = 'none'; // Hide if broken
                        }}
                    />
                ) : (
                    <div className="w-full h-full bg-slate-200 flex items-center justify-center text-slate-400">
                        <span className="text-xl font-serif italic">No Image Available</span>
                    </div>
                )}

                <div className="absolute bottom-0 left-0 right-0 p-8 z-20 text-white"> {/* Increased padding */}
                    <div className="max-w-4xl mx-auto">
                        <h1 className="text-3xl md:text-5xl font-bold mb-3 font-serif tracking-wide">{recipe.recipe_name}</h1>
                        <div className="flex flex-wrap gap-2 text-sm md:text-base opacity-90">
                            {recipe.tags?.map(tag => (
                                <span key={tag} className="px-3 py-1 border border-white/40 rounded-full bg-black/20 backdrop-blur-md uppercase tracking-wider text-xs font-medium">{tag}</span>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <main className="max-w-4xl mx-auto px-6 py-12"> {/* Increased padding */}
                {/* AI Message Alert */}
                {recipe.message && (
                    <div className="mb-12 p-6 bg-orange-50/50 border border-orange-100 rounded-xl flex gap-4 items-start shadow-sm">
                        <div className="mt-1 text-orange-600 bg-orange-100 p-2 rounded-full">
                            <ChefHat size={20} />
                        </div>
                        <div>
                            <h3 className="font-bold text-slate-800 mb-2 uppercase tracking-wide text-xs">Chef's Consultant Note</h3>
                            <p className="text-slate-700 leading-relaxed font-serif text-lg italic opacity-90">{recipe.message}</p>
                        </div>
                    </div>
                )}

                <div className="grid md:grid-cols-[1fr_300px] gap-12">
                    {/* Left: Steps */}
                    <div>
                        <h2 className="text-2xl font-bold text-slate-900 mb-8 font-serif border-b pb-4">Instructions</h2>
                        <div className="space-y-12">
                            {recipe.steps.map((step, idx) => (
                                <div key={step.step_index} className="relative pl-8 border-l border-slate-200 pb-2 last:border-0 group">
                                    <div className="absolute -left-[5px] top-2 w-2.5 h-2.5 rounded-full bg-slate-300 group-hover:bg-orange-500 transition-colors" />
                                    <h3 className="text-lg font-bold text-slate-400 mb-2 flex items-center gap-2 uppercase tracking-widest text-sm">
                                        Step {step.step_index}
                                    </h3>
                                    <p className="text-slate-700 text-lg leading-relaxed mb-6 font-light">{step.description}</p>
                                    {step.image_url && (
                                        <div className="rounded-xl overflow-hidden shadow-sm aspect-video bg-slate-50 flex items-center justify-center border border-slate-100">
                                            <img src={step.image_url} alt={`Step ${step.step_index}`} className="w-full h-full object-cover" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Right: Info (Sticky) - REMOVED */}
                    <div className="space-y-6 hidden"></div>
                </div>
            </main>
        </div>
    );
};

export default RecipeDetail;
