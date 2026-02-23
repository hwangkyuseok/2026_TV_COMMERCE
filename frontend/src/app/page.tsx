"use client";

import { useEffect, useState, useCallback } from "react";
import { MockData, Product } from "@/types";
import { useRemoteFocus } from "@/hooks/useRemoteFocus";
import Sidebar from "@/components/tv/Sidebar";
import VideoPlayer from "@/components/tv/VideoPlayer";
import ShoppingRow from "@/components/tv/ShoppingRow";
import PurchaseModal from "@/components/common/PurchaseModal";
import ConsultModal from "@/components/common/ConsultModal";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function HomePage() {
  const [data, setData] = useState<MockData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [modalProduct, setModalProduct] = useState<Product | null>(null);

  // Fetch mock data from FastAPI
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/data`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: MockData) => setData(d))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const isModalOpen = modalProduct !== null;
  const closeModal = useCallback(() => setModalProduct(null), []);

  const handleEnterProduct = useCallback(
    (index: number) => {
      if (!data) return;
      const product = data.products[index];
      if (product) setModalProduct(product);
    },
    [data]
  );

  const { focus } = useRemoteFocus({
    menuCount: data?.menus.length ?? 0,
    channelCount: data?.recommendedChannels.length ?? 0,
    productCount: data?.products.length ?? 0,
    isSidebarVisible,
    onEnterProduct: handleEnterProduct,
    isTrapped: isModalOpen,
  });

  // Sidebar toggle: 'b' key simulates a TV remote Back/Menu button
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (isModalOpen) return;
      if (e.key === "b" || e.key === "B") {
        setIsSidebarVisible((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isModalOpen]);

  // ── Loading ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center w-screen h-screen bg-tv-bg">
        <div className="text-center">
          <div className="text-5xl mb-4 select-none" style={{ animation: "pulse 2s infinite" }}>
            📺
          </div>
          <p className="text-tv-muted text-sm tracking-widest">Loading...</p>
        </div>
      </div>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────
  if (error || !data) {
    return (
      <div className="flex items-center justify-center w-screen h-screen bg-tv-bg">
        <div
          className="text-center px-10 py-8 rounded-2xl"
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <div className="text-4xl mb-4 select-none">⚠️</div>
          <p className="text-red-400 text-sm mb-2 font-medium">백엔드 연결 실패</p>
          <p className="text-tv-muted text-xs">{error ?? "데이터를 불러올 수 없습니다."}</p>
          <p className="text-tv-muted text-xs mt-1">
            FastAPI 서버({API_BASE})가 실행 중인지 확인하세요.
          </p>
        </div>
      </div>
    );
  }

  const selectedMenu = data.menus[focus.sidebarIndex] ?? data.menus[0] ?? "";

  return (
    <div className="flex w-screen h-screen overflow-hidden bg-tv-bg">
      {/* ── Area 1: Sidebar ─────────────────────────────────────────────── */}
      <div
        className="shrink-0 overflow-hidden h-full"
        style={{
          width: isSidebarVisible ? "14rem" : "0",
          transition: "width 0.35s cubic-bezier(0.4, 0, 0.2, 1)",
        }}
      >
        <Sidebar
          menus={data.menus}
          activeIndex={focus.sidebarIndex}
          isSectionFocused={focus.zone === "sidebar"}
        />
      </div>

      {/* ── Right column: VideoPlayer (Area 2) + ShoppingRow (Area 3) ── */}
      <div className="flex-1 flex flex-col min-w-0 p-4 gap-3 h-full overflow-hidden">
        {/* ── Area 2: VideoPlayer ───────────────────────────────────────── */}
        <div className="flex-1 min-h-0">
          <VideoPlayer
            channels={data.recommendedChannels}
            currentIndex={focus.videoIndex}
            isFocused={focus.zone === "video"}
          />
        </div>

        {/* ── Area 3: ShoppingRow ──────────────────────────────────────── */}
        <div
          className="shrink-0"
          style={{ height: "208px" }}
        >
          <ShoppingRow
            products={data.products}
            focusedIndex={focus.shoppingIndex}
            isFocused={focus.zone === "shopping"}
          />
        </div>
      </div>

      {/* ── Zone indicator (slim top-right badge) ── */}
      <div
        className="fixed top-3 right-4 z-30 flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px]"
        style={{
          background: "rgba(0,0,0,0.55)",
          border: "1px solid rgba(255,255,255,0.1)",
          backdropFilter: "blur(8px)",
          color: "#7070a0",
        }}
      >
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{
            background:
              focus.zone === "video"
                ? "#00e676"
                : focus.zone === "shopping"
                ? "#fb923c"
                : "#00b0ff",
            boxShadow: `0 0 6px ${
              focus.zone === "video"
                ? "rgba(0,230,118,0.8)"
                : focus.zone === "shopping"
                ? "rgba(251,146,60,0.8)"
                : "rgba(0,176,255,0.8)"
            }`,
          }}
        />
        <span>
          {selectedMenu}
          {!isSidebarVisible && " · 전체화면"}
        </span>
      </div>

      {/* ── Modals ──────────────────────────────────────────────────────── */}
      {modalProduct &&
        (modalProduct.price >= 200_000 ? (
          <ConsultModal product={modalProduct} onClose={closeModal} />
        ) : (
          <PurchaseModal product={modalProduct} onClose={closeModal} />
        ))}
    </div>
  );
}
