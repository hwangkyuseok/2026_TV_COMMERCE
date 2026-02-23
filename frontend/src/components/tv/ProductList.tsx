"use client";

import { Product } from "@/types";

interface ProductListProps {
  products: Product[];
  focusedIndex: number;
  isSectionFocused: boolean;
}

const PRODUCT_COLORS = ["#1a2e4a", "#2e1a4a", "#1a4a2e", "#4a1a2e"];
const PRODUCT_EMOJIS = ["👗", "👟", "☕", "🧹"];

function formatPrice(price: number): string {
  return price.toLocaleString("ko-KR") + "원";
}

export default function ProductList({
  products,
  focusedIndex,
  isSectionFocused,
}: ProductListProps) {
  return (
    <div className="w-full">
      <h3 className="text-tv-muted text-xs uppercase tracking-widest mb-3 px-1">
        추천 상품
      </h3>
      <div className="flex gap-4 overflow-x-hidden">
        {products.map((product, idx) => {
          const isItemFocused = isSectionFocused && focusedIndex === idx;
          const isExpensive = product.price >= 200000;

          return (
            <div
              key={product.id}
              className={[
                "tv-card shrink-0 rounded-xl overflow-hidden flex flex-col",
                isItemFocused ? "tv-focused" : "",
              ].join(" ")}
              style={{
                width: "200px",
                background: `linear-gradient(160deg, ${
                  PRODUCT_COLORS[idx % PRODUCT_COLORS.length]
                } 0%, #0f0f22 100%)`,
              }}
            >
              {/* Product image area */}
              <div className="flex-1 flex items-center justify-center py-6 bg-white/5">
                <span className="text-5xl">
                  {PRODUCT_EMOJIS[idx % PRODUCT_EMOJIS.length]}
                </span>
              </div>

              {/* Product info */}
              <div className="p-3">
                <p className="text-white text-xs font-medium leading-tight line-clamp-2 min-h-[2.5rem]">
                  {product.name}
                </p>
                <p
                  className={`text-sm font-bold mt-2 ${
                    isExpensive ? "text-orange-400" : "text-tv-focus"
                  }`}
                >
                  {formatPrice(product.price)}
                </p>

                {/* CTA hint */}
                {isItemFocused && (
                  <div className="mt-2 flex items-center justify-center gap-1 py-1 rounded bg-tv-focus/20 border border-tv-focus/50">
                    <span className="text-tv-focus text-xs font-semibold">
                      {isExpensive ? "📞 상담원 연결" : "🛒 바로 구매"}
                    </span>
                  </div>
                )}

                {/* Price tag */}
                {isExpensive && (
                  <span className="inline-block mt-1 px-1.5 py-0.5 bg-orange-500/20 border border-orange-500/40 text-orange-400 text-xs rounded">
                    고가 상품
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Navigation hint */}
      <div className="mt-3 flex items-center gap-2 text-tv-muted text-xs px-1">
        <span>← →</span>
        <span>이동</span>
        <span className="ml-4 px-2 py-0.5 border border-tv-muted/40 rounded text-xs">
          Enter
        </span>
        <span>선택</span>
      </div>
    </div>
  );
}
