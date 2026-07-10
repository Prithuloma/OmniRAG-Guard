"use client";

import { useEffect, useRef } from "react";

export default function CustomCursor() {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const dot = dotRef.current!;
    const ring = ringRef.current!;

    let ringX = 0, ringY = 0;
    let mouseX = 0, mouseY = 0;

    const onMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      dot.style.transform = `translate(${mouseX}px, ${mouseY}px)`;
    };

    const animate = () => {
      ringX += (mouseX - ringX) * 0.12;
      ringY += (mouseY - ringY) * 0.12;
      ring.style.transform = `translate(${ringX}px, ${ringY}px)`;
      requestAnimationFrame(animate);
    };

    window.addEventListener("mousemove", onMouseMove);
    animate();

    return () => window.removeEventListener("mousemove", onMouseMove);
  }, []);

  return (
    <>
      {/* Outer ring — lags behind */}
      <div
        ref={ringRef}
        style={{
          position: "fixed",
          top: -20,
          left: -20,
          width: 40,
          height: 40,
          borderRadius: "50%",
          border: "1.5px solid rgba(167, 139, 250, 0.6)",
          boxShadow: "0 0 10px rgba(139, 92, 246, 0.4)",
          pointerEvents: "none",
          zIndex: 9999,
          transition: "opacity 0.3s",
        }}
      />
      {/* Inner dot — instant */}
      <div
        ref={dotRef}
        style={{
          position: "fixed",
          top: -4,
          left: -4,
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: "rgba(167, 139, 250, 1)",
          boxShadow: "0 0 10px rgba(139, 92, 246, 0.9), 0 0 20px rgba(139, 92, 246, 0.5)",
          pointerEvents: "none",
          zIndex: 9999,
        }}
      />
    </>
  );
}