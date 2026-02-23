"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { KEY_CODES } from "@/constants/keyCodes";

export type Zone = "sidebar" | "video" | "shopping";

export interface FocusState {
  zone: Zone;
  sidebarIndex: number;
  videoIndex: number;
  shoppingIndex: number;
}

interface UseRemoteFocusOptions {
  menuCount: number;
  channelCount: number;
  productCount: number;
  isSidebarVisible: boolean;
  onEnterProduct?: (index: number) => void;
  isTrapped?: boolean;
}

export function useRemoteFocus({
  menuCount,
  channelCount,
  productCount,
  isSidebarVisible,
  onEnterProduct,
  isTrapped = false,
}: UseRemoteFocusOptions) {
  const [focus, setFocus] = useState<FocusState>({
    zone: "video",
    sidebarIndex: 0,
    videoIndex: 0,
    shoppingIndex: 0,
  });

  // Keep a ref so the keydown handler always reads fresh state without stale closures
  const focusRef = useRef(focus);
  focusRef.current = focus;

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // When a modal is open, yield all key handling to the modal's own listener
      if (isTrapped) return;

      const f = focusRef.current;

      switch (e.key) {
        // ─── Vertical: used for sidebar menu + zone switch (video ↔ shopping) ───
        case KEY_CODES.ARROW_UP: {
          e.preventDefault();
          if (f.zone === "sidebar") {
            const newIdx = Math.max(0, f.sidebarIndex - 1);
            setFocus((prev) => ({ ...prev, sidebarIndex: newIdx }));
          } else if (f.zone === "shopping") {
            setFocus((prev) => ({ ...prev, zone: "video" }));
          }
          break;
        }

        case KEY_CODES.ARROW_DOWN: {
          e.preventDefault();
          if (f.zone === "sidebar") {
            const newIdx = Math.min(menuCount - 1, f.sidebarIndex + 1);
            setFocus((prev) => ({ ...prev, sidebarIndex: newIdx }));
          } else if (f.zone === "video") {
            setFocus((prev) => ({ ...prev, zone: "shopping" }));
          }
          break;
        }

        // ─── Horizontal: zone switch (sidebar ↔ video) + channel/product scroll ───
        case KEY_CODES.ARROW_LEFT: {
          e.preventDefault();
          if (f.zone === "video") {
            if (f.videoIndex > 0) {
              // Go to previous channel
              setFocus((prev) => ({
                ...prev,
                videoIndex: prev.videoIndex - 1,
              }));
            } else if (isSidebarVisible) {
              // First channel → enter sidebar
              setFocus((prev) => ({ ...prev, zone: "sidebar" }));
            }
          } else if (f.zone === "shopping") {
            setFocus((prev) => ({
              ...prev,
              shoppingIndex: Math.max(0, prev.shoppingIndex - 1),
            }));
          }
          // sidebar: ArrowLeft has no effect
          break;
        }

        case KEY_CODES.ARROW_RIGHT: {
          e.preventDefault();
          if (f.zone === "sidebar") {
            // Leave sidebar → enter video zone
            setFocus((prev) => ({ ...prev, zone: "video" }));
          } else if (f.zone === "video") {
            if (f.videoIndex < channelCount - 1) {
              setFocus((prev) => ({
                ...prev,
                videoIndex: prev.videoIndex + 1,
              }));
            }
          } else if (f.zone === "shopping") {
            setFocus((prev) => ({
              ...prev,
              shoppingIndex: Math.min(
                productCount - 1,
                prev.shoppingIndex + 1
              ),
            }));
          }
          break;
        }

        // ─── Confirm ───────────────────────────────────────────────────
        case KEY_CODES.ENTER: {
          e.preventDefault();
          if (f.zone === "shopping") {
            onEnterProduct?.(f.shoppingIndex);
          } else if (f.zone === "sidebar") {
            // Treat Enter in sidebar same as ArrowRight → enter video
            setFocus((prev) => ({ ...prev, zone: "video" }));
          }
          break;
        }

        default:
          break;
      }
    },
    [
      isTrapped,
      menuCount,
      channelCount,
      productCount,
      isSidebarVisible,
      onEnterProduct,
    ]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return { focus, setFocus };
}
