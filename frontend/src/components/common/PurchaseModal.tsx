"use client";

import { useEffect, useCallback, useState } from "react";
import { Product } from "@/types";
import { KEY_CODES } from "@/constants/keyCodes";

interface PurchaseModalProps {
  product: Product;
  onClose: () => void;
}

const RELATED_PRODUCTS = [
  { label: "남성용", suffix: "남성용 고워크 글라이드 슬립인스 워킹화" },
  { label: "여성용", suffix: "여성용 고워크 글라이드 슬립인스 워킹화" },
];

const MODAL_BUTTONS = ["주문하기", "닫기"];

function formatPrice(price: number): string {
  return price.toLocaleString("ko-KR") + "원";
}

export default function PurchaseModal({ product, onClose }: PurchaseModalProps) {
  const [focusedBtn, setFocusedBtn] = useState(0); // 0 = 주문하기, 1 = 닫기
  const [selectedVariant, setSelectedVariant] = useState(0);
  const [ordered, setOrdered] = useState(false);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      switch (e.key) {
        case KEY_CODES.ARROW_LEFT:
          e.preventDefault();
          setFocusedBtn((p) => Math.max(0, p - 1));
          break;
        case KEY_CODES.ARROW_RIGHT:
          e.preventDefault();
          setFocusedBtn((p) => Math.min(MODAL_BUTTONS.length - 1, p + 1));
          break;
        case KEY_CODES.ARROW_UP:
        case KEY_CODES.ARROW_DOWN:
          e.preventDefault();
          setSelectedVariant((p) =>
            e.key === KEY_CODES.ARROW_LEFT || e.key === KEY_CODES.ARROW_UP
              ? Math.max(0, p - 1)
              : Math.min(RELATED_PRODUCTS.length - 1, p + 1)
          );
          break;
        case KEY_CODES.ENTER:
          e.preventDefault();
          if (focusedBtn === 0) {
            setOrdered(true);
            setTimeout(onClose, 1500);
          } else {
            onClose();
          }
          break;
        case KEY_CODES.ESCAPE:
          e.preventDefault();
          onClose();
          break;
      }
    },
    [focusedBtn, onClose]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75">
      <div
        className="relative rounded-2xl overflow-hidden p-6 w-full max-w-xl"
        style={{ background: "#0f0f22", border: "1px solid rgba(255,255,255,0.1)" }}
      >
        {/* Title */}
        <h2 className="text-white text-xl font-bold text-center mb-5">
          상품을 확인하고 주문을 진행해주세요
        </h2>

        {/* Products grid */}
        <div className="grid grid-cols-2 gap-4 mb-5">
          {RELATED_PRODUCTS.map((variant, idx) => {
            const isSelected = selectedVariant === idx;
            return (
              <div
                key={idx}
                className={[
                  "rounded-xl p-4 flex flex-col items-center gap-3 transition-all duration-150",
                  isSelected
                    ? "tv-focused bg-white/10"
                    : "bg-white/5 opacity-70",
                ].join(" ")}
              >
                <p className="text-white/80 text-xs text-center leading-tight">
                  {product.name.split(" ").slice(0, 2).join(" ")} {variant.suffix}
                </p>
                <div className="w-24 h-24 bg-white/10 rounded-lg flex items-center justify-center text-4xl">
                  👟
                </div>
                {isSelected && focusedBtn === 0 && (
                  <button className="px-4 py-1.5 rounded-full bg-tv-focus text-black text-sm font-bold">
                    주문하기
                  </button>
                )}
                <p className="text-white font-bold text-sm">
                  {formatPrice(product.price)}
                </p>
              </div>
            );
          })}
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-center gap-3 text-white/60 text-sm mb-5">
          <span>{"<"}</span>
          <span>1 / {RELATED_PRODUCTS.length}</span>
          <span>{">"}</span>
        </div>

        {/* Buttons */}
        <div className="flex gap-3 justify-center">
          {MODAL_BUTTONS.map((label, idx) => (
            <button
              key={label}
              className={[
                "px-8 py-3 rounded-full text-sm font-semibold transition-all duration-150",
                focusedBtn === idx
                  ? idx === 0
                    ? "bg-tv-focus text-black tv-focused"
                    : "bg-white/20 text-white tv-focused"
                  : idx === 0
                  ? "bg-tv-focus/30 text-tv-focus"
                  : "bg-white/10 text-white/60",
              ].join(" ")}
            >
              {ordered && idx === 0 ? "✓ 주문완료!" : label}
            </button>
          ))}
        </div>

        {/* Key hint */}
        <p className="text-center text-tv-muted text-xs mt-3">
          ← → 버튼 이동 &nbsp;|&nbsp; Enter 선택 &nbsp;|&nbsp; ESC 닫기
        </p>
      </div>
    </div>
  );
}
