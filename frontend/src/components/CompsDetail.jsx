import React from "react";
import { Film } from "lucide-react";

export default function CompsDetail({ detail }) {
  if (!detail) return <p className="font-courier text-sm">No comps details available.</p>;

  const {
    extracted_genres = [],
    extracted_keywords = [],
    comparable_films = [],
    positioning_statement,
    target_audience,
    market_assessment,
  } = detail;

  // TMDB poster URL base
  const TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300";

  return (
    <div className="space-y-6 text-left font-grotesk">
      <div className="border-b border-ink/20 pb-4">
        <h3 className="font-bold text-lg text-ink uppercase tracking-wider">
          Market Positioning & Comparable Films
        </h3>
        <p className="text-sm opacity-80 mt-1">
          Displays real film comparables discovered via TMDB API based on screenplay metadata.
        </p>
      </div>

      {/* Positioning & Target Audience & Market Assessment */}
      <div className="space-y-4">
        <div className="bg-paper border border-ink/20 p-4 rounded shadow-sm">
          <div className="font-bold text-xs opacity-60 uppercase mb-1">
            Market Positioning Statement
          </div>
          <p className="text-sm leading-relaxed text-ink/90">{positioning_statement}</p>
        </div>

        <div className="bg-paper border border-ink/20 p-4 rounded shadow-sm">
          <div className="font-bold text-xs opacity-60 uppercase mb-1">
            Target Audience
          </div>
          <p className="text-sm leading-relaxed text-ink/90">{target_audience}</p>
        </div>

        <div className="bg-paper border border-ink/20 p-4 rounded shadow-sm">
          <div className="font-bold text-xs opacity-60 uppercase mb-1">
            Commercial Potential & Market Assessment
          </div>
          <p className="text-sm leading-relaxed text-ink/90">{market_assessment}</p>
        </div>
      </div>

      {/* Extracted descriptors tags */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border border-ink/15 p-4 rounded bg-paper/30">
          <span className="font-bold text-xs opacity-60 uppercase block mb-2">Extracted Genres</span>
          <div className="flex flex-wrap gap-1.5">
            {extracted_genres.map((g, idx) => (
              <span key={idx} className="bg-ink/5 text-ink text-xs font-semibold px-2 py-0.5 border border-ink/15 rounded">
                {g}
              </span>
            ))}
          </div>
        </div>

        <div className="border border-ink/15 p-4 rounded bg-paper/30">
          <span className="font-bold text-xs opacity-60 uppercase block mb-2">Extracted Keywords</span>
          <div className="flex flex-wrap gap-1.5">
            {extracted_keywords.map((k, idx) => (
              <span key={idx} className="bg-carbon-blue/5 text-carbon-blue text-xs font-semibold px-2 py-0.5 border border-carbon-blue/15 rounded">
                {k}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Comparable Films List */}
      <div className="space-y-4 pt-4">
        <h4 className="font-bold text-md text-ink uppercase tracking-wide">
          Real comparable films (TMDB API verified)
        </h4>

        {comparable_films.length === 0 ? (
          <p className="text-sm font-courier opacity-70">No matching comparable films discovered in TMDB database.</p>
        ) : (
          <div className="space-y-4">
            {comparable_films.map((film) => {
              const posterUrl = film.poster_path ? `${TMDB_IMAGE_BASE}${film.poster_path}` : null;

              return (
                <div
                  key={film.tmdb_id}
                  className="border border-ink rounded p-4 bg-paper/50 flex flex-col md:flex-row gap-4"
                >
                  {/* Poster Thumbnail */}
                  <div className="w-24 h-36 bg-ink/10 border border-ink/20 rounded overflow-hidden shrink-0 flex items-center justify-center relative">
                    {posterUrl ? (
                      <img src={posterUrl} alt={film.title} className="w-full h-full object-cover" />
                    ) : (
                      <Film size={28} className="text-ink/30" />
                    )}
                  </div>

                  {/* Movie Info */}
                  <div className="flex-1 space-y-2">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <h5 className="font-bold text-base text-ink">{film.title}</h5>
                      {film.year && (
                        <span className="font-courier text-sm text-ink/75">({film.year})</span>
                      )}
                      {film.vote_average && (
                        <span className="font-courier text-xs bg-ink/5 px-2 py-0.5 border border-ink/10 rounded ml-auto">
                          Rating: {film.vote_average.toFixed(1)}/10
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-1">
                      {film.genres.map((g, idx) => (
                        <span key={idx} className="bg-ink/5 text-ink text-[10px] font-bold tracking-wide uppercase px-1.5 py-0.2 border border-ink/10 rounded">
                          {g}
                        </span>
                      ))}
                    </div>

                    <p className="text-xs text-ink/80 leading-relaxed italic">{film.overview}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Required TMDB API Attribution */}
      <div className="pt-6 border-t border-ink/10 text-center text-xs opacity-50 flex items-center justify-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" viewBox="0 0 184.62 161.54" className="h-4 fill-current">
          <path d="M129.23,0H55.38C24.8,0,0,24.8,0,55.38v50.77c0,30.58,24.8,55.38,55.38,55.38h73.85c30.58,0,55.38-24.8,55.38-55.38V55.38C184.62,24.8,159.81,0,129.23,0z M117.69,117.69H66.92V66.92h50.77V117.69z"/>
        </svg>
        <span>This product uses the TMDB API but is not endorsed or certified by TMDB.</span>
      </div>
    </div>
  );
}
