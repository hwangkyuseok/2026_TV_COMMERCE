"use client";

import { RecommendedChannel } from "@/types";

interface CarouselProps {
  channels: RecommendedChannel[];
  focusedIndex: number;
  isSectionFocused: boolean;
}

export default function Carousel({
  channels,
  focusedIndex,
  isSectionFocused,
}: CarouselProps) {
  if (channels.length === 0) return null;

  // Show active channel as main banner
  const activeChannel = channels[focusedIndex] ?? channels[0];

  return (
    <div className="w-full">
      {/* Main Banner */}
      <div
        className="relative w-full rounded-xl overflow-hidden flex items-end"
        style={{
          height: "320px",
          background: `linear-gradient(135deg, ${activeChannel.bg} 0%, #1a1a35 100%)`,
        }}
      >
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />

        {/* Channel badge */}
        <div className="absolute top-4 left-4 flex items-center gap-2">
          <span className="px-2 py-1 bg-red-600 text-white text-xs font-bold rounded">
            {activeChannel.badge}
          </span>
          <span className="text-white/80 text-sm">{activeChannel.title}</span>
        </div>

        {/* Mock TV program preview */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-5xl mb-2">📺</div>
            <div className="text-white text-lg font-semibold opacity-80">
              {activeChannel.title}
            </div>
            <div className="text-white/60 text-sm">{activeChannel.desc}</div>
          </div>
        </div>

        {/* Bottom info */}
        <div className="relative z-10 p-4 w-full">
          <h2 className="text-white text-xl font-bold">{activeChannel.title}</h2>
          <p className="text-white/70 text-sm">{activeChannel.desc}</p>
        </div>

        {/* Pagination dots — use channel id as key */}
        <div className="absolute bottom-3 right-4 flex gap-1">
          {channels.map((ch, i) => (
            <span
              key={ch.id}
              className={`block w-2 h-2 rounded-full transition-all ${
                i === focusedIndex ? "bg-tv-focus w-6" : "bg-white/40"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Thumbnail strip */}
      <div className="flex gap-3 mt-3">
        {channels.map((ch, idx) => {
          const isItemFocused = isSectionFocused && focusedIndex === idx;
          return (
            <div
              key={ch.id}
              className={[
                "tv-card flex-1 rounded-lg overflow-hidden p-3 flex items-center gap-2",
                isItemFocused ? "tv-focused" : "opacity-60",
              ].join(" ")}
              style={{ background: ch.bg, minWidth: 0 }}
            >
              <span className="text-2xl">📺</span>
              <div className="min-w-0">
                <div className="text-white text-xs font-semibold truncate">
                  {ch.title}
                </div>
                <div className="text-white/60 text-xs truncate">{ch.desc}</div>
              </div>
              {ch.badge && (
                <span className="ml-auto px-1 py-0.5 bg-red-600 text-white text-xs rounded shrink-0">
                  {ch.badge}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
