"use client";

import { LiveHomeShoppingChannel } from "@/types";

interface ShoppingGridProps {
  channels: LiveHomeShoppingChannel[];
  focusedIndex: number;
  isSectionFocused: boolean;
}

const GRID_COLORS = [
  "#1a2e4a",
  "#2e1a4a",
  "#1a4a2e",
  "#4a2e1a",
  "#2e4a1a",
  "#1a3a4a",
];

const CHANNEL_EMOJIS: Record<string, string> = {
  현대홈쇼핑: "🏠",
  "CJ온스타일": "✨",
  "GS SHOP": "🛒",
  롯데홈쇼핑: "🌸",
};

export default function ShoppingGrid({
  channels,
  focusedIndex,
  isSectionFocused,
}: ShoppingGridProps) {
  // Build grid: we display provided channels + fill to at least 6 cells
  const cells = [...channels];
  while (cells.length < 6) {
    cells.push({
      id: `placeholder_${cells.length}`,
      channelName: "채널 준비중",
      currentProgram: "곧 방송 예정",
      bg: GRID_COLORS[cells.length % GRID_COLORS.length],
    });
  }

  return (
    <div className="w-full h-full grid grid-cols-3 grid-rows-2 gap-3">
      {cells.map((ch, idx) => {
        const isItemFocused = isSectionFocused && focusedIndex === idx;
        const isLive = idx < channels.length;

        return (
          <div
            key={ch.id}
            className={[
              "tv-card relative rounded-xl overflow-hidden flex flex-col justify-between p-4",
              isItemFocused ? "tv-focused" : "",
            ].join(" ")}
            style={{
              background: `linear-gradient(135deg, ${ch.bg} 0%, rgba(10,10,26,0.9) 100%)`,
              minHeight: "180px",
            }}
          >
            {/* Overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent" />

            {/* Live badge */}
            {isLive && (
              <div className="relative flex items-center gap-2">
                <span className="flex items-center gap-1 px-2 py-0.5 bg-red-600 text-white text-xs font-bold rounded">
                  <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                  LIVE
                </span>
                <span className="text-white/70 text-xs">{ch.channelName}</span>
              </div>
            )}

            {/* Channel icon */}
            <div className="relative flex-1 flex items-center justify-center">
              <span className="text-5xl">
                {CHANNEL_EMOJIS[ch.channelName] ?? "📺"}
              </span>
            </div>

            {/* Program info */}
            <div className="relative">
              <div className="text-white font-semibold text-sm leading-tight truncate">
                {ch.currentProgram}
              </div>
              <div className="text-white/60 text-xs mt-0.5">{ch.channelName}</div>
            </div>

            {/* Focus indicator */}
            {isItemFocused && (
              <div className="absolute bottom-2 right-2 w-2 h-2 bg-tv-focus rounded-full" />
            )}
          </div>
        );
      })}
    </div>
  );
}
