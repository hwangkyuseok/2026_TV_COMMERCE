"use client";

import { useRef, useEffect } from "react";
import { Product } from "@/types";

interface ShoppingRowProps {
  products: Product[];
  focusedIndex: number;
  isFocused: boolean;
}

const PRODUCT_EMOJIS = ["👗", "👟", "☕", "🧹", "📱", "🎧"];

const PRODUCT_GRADIENTS = [
  ["#1a2e4a", "#0a1520"],
  ["#2e1a4a", "#150a25"],
  ["#1a4a2e", "#0a2015"],
  ["#4a1a2e", "#200a14"],
];

function formatPrice(price: number): string {
  return price.toLocaleString("ko-KR") + "원";
}

export default function ShoppingRow({
  products,
  focusedIndex,
  isFocused,
}: ShoppingRowProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Smoothly scroll the focused product card into view
  useEffect(() => {
    if (!containerRef.current || !isFocused) return;
    const items = containerRef.current.querySelectorAll<HTMLElement>(
      "[data-product-card]"
    );
    const target = items[focusedIndex];
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "center",
      });
    }
  }, [focusedIndex, isFocused]);

  return (
    <div className="w-full h-full flex flex-col">
      {/* ── Section header ── */}
      <div className="flex items-center gap-3 mb-3 px-1 shrink-0">
        <h3
          className="text-[11px] font-semibold tracking-[0.18em] uppercase shrink-0"
          style={{ color: "#7070a0" }}
        >
          추천 상품
        </h3>
        <div
          className="flex-1 h-px"
          style={{
            background:
              "linear-gradient(90deg, rgba(255,255,255,0.12) 0%, transparent 100%)",
          }}
        />
        <span
          className="text-[10px] shrink-0"
          style={{
            color: "#7070a0",
            opacity: isFocused ? 1 : 0,
            transition: "opacity 0.3s ease",
          }}
        >
          ← → 이동 &nbsp;·&nbsp; Enter 선택
        </span>
      </div>

      {/* ── Product cards ── */}
      <div
        ref={containerRef}
        className="flex gap-3 overflow-x-hidden flex-1"
        style={{ scrollbarWidth: "none" }}
      >
        {products.map((product, idx) => {
          const isCardFocused = isFocused && focusedIndex === idx;
          const isExpensive = product.price >= 200_000;
          const [gradFrom, gradTo] =
            PRODUCT_GRADIENTS[idx % PRODUCT_GRADIENTS.length];

          return (
            <div
              key={product.id}
              data-product-card
              className="shrink-0 flex flex-col rounded-xl overflow-hidden"
              style={{
                width: "152px",
                background: `linear-gradient(160deg, ${gradFrom} 0%, ${gradTo} 100%)`,
                outline: isCardFocused
                  ? "2px solid rgba(0,230,118,0.65)"
                  : "2px solid transparent",
                outlineOffset: "2px",
                transform: isCardFocused ? "scale(1.06)" : "scale(1)",
                opacity: isCardFocused ? 1 : isFocused ? 0.55 : 0.8,
                boxShadow: isCardFocused
                  ? "0 0 28px rgba(0,230,118,0.30), 0 8px 24px rgba(0,0,0,0.5)"
                  : "0 4px 16px rgba(0,0,0,0.3)",
                transition:
                  "transform 0.25s ease, opacity 0.25s ease, outline-color 0.25s ease, box-shadow 0.25s ease",
              }}
            >
              {/* Product image area */}
              <div
                className="flex items-center justify-center"
                style={{
                  height: "88px",
                  background: "rgba(255,255,255,0.04)",
                  borderBottom: "1px solid rgba(255,255,255,0.06)",
                }}
              >
                <span className="text-4xl select-none">
                  {PRODUCT_EMOJIS[idx % PRODUCT_EMOJIS.length]}
                </span>
              </div>

              {/* Info area */}
              <div className="p-3 flex flex-col gap-1.5 flex-1">
                <p
                  className="text-white text-[12px] font-medium leading-snug"
                  style={{
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                    minHeight: "2.5em",
                  }}
                >
                  {product.name}
                </p>

                <p
                  className="text-[13px] font-bold mt-auto"
                  style={{ color: isExpensive ? "#fb923c" : "#00e676" }}
                >
                  {formatPrice(product.price)}
                </p>

                {/* CTA shown when card is focused */}
                {isCardFocused && (
                  <div
                    className="flex items-center justify-center py-1.5 rounded-lg mt-1"
                    style={{
                      background: "rgba(0,230,118,0.12)",
                      border: "1px solid rgba(0,230,118,0.35)",
                    }}
                  >
                    <span
                      className="text-[11px] font-semibold"
                      style={{ color: "#00e676" }}
                    >
                      {isExpensive ? "📞 상담 연결" : "🛒 바로 구매"}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
