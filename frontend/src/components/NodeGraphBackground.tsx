// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import { useEffect, useRef } from "react";
import { useTheme } from "@mui/material";

/**
 * Animated node-and-edge background.
 *
 * Renders a force-directed graph on a full-screen canvas: nodes drift with
 * mild velocity damping, are gently pulled back toward their home position,
 * and repel from the mouse cursor. Edges connect each node to its nearest
 * few neighbors. Designed to sit behind page content as subtle ambience.
 */

type Node = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  homeX: number;
  homeY: number;
  radius: number;
  colorIndex: number;
};

interface NodeGraphBackgroundProps {
  /** Overall alpha multiplier applied to both nodes and edges. Default 0.35. */
  opacity?: number;
  /** Target density: roughly one node per this many square pixels. Default 18000. */
  density?: number;
  /** Max distance (px) over which neighbor edges are drawn. Default 180. */
  linkDistance?: number;
  /** Radius of mouse repulsion field (px). Default 220. */
  mouseRadius?: number;
  /** Strength of mouse repulsion. Default 1800. */
  mouseStrength?: number;
}

export const NodeGraphBackground = ({
  opacity = 0.35,
  density = 18000,
  linkDistance = 180,
  mouseRadius = 220,
  mouseStrength = 1800,
}: NodeGraphBackgroundProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const theme = useTheme();
  const palette = theme.palette.discrete;

  // Keep mutable state in refs so the animation loop isn't torn down on re-render.
  const nodesRef = useRef<Node[]>([]);
  const mouseRef = useRef<{ x: number; y: number; active: boolean }>({
    x: -9999,
    y: -9999,
    active: false,
  });
  const rafRef = useRef<number | null>(null);
  const sizeRef = useRef<{ w: number; h: number; dpr: number }>({
    w: 0,
    h: 0,
    dpr: 1,
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const rebuildNodes = (w: number, h: number) => {
      const count = Math.max(24, Math.min(90, Math.floor((w * h) / density)));
      const nodes: Node[] = [];
      for (let i = 0; i < count; i++) {
        const x = Math.random() * w;
        const y = Math.random() * h;
        nodes.push({
          x,
          y,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          homeX: x,
          homeY: y,
          radius: 2 + Math.random() * 3,
          colorIndex: Math.floor(Math.random() * palette.length),
        });
      }
      nodesRef.current = nodes;
    };

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      const w = window.innerWidth;
      const h = window.innerHeight;
      sizeRef.current = { w, h, dpr };
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      rebuildNodes(w, h);
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
      mouseRef.current.active = true;
    };
    const handleMouseLeave = () => {
      mouseRef.current.active = false;
      mouseRef.current.x = -9999;
      mouseRef.current.y = -9999;
    };

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseleave", handleMouseLeave);

    // Convert a hex color plus alpha [0,1] into an rgba() string.
    const hexToRgba = (hex: string, a: number) => {
      const h = hex.replace("#", "");
      const r = parseInt(h.substring(0, 2), 16);
      const g = parseInt(h.substring(2, 4), 16);
      const b = parseInt(h.substring(4, 6), 16);
      return `rgba(${r}, ${g}, ${b}, ${a})`;
    };

    const step = () => {
      const { w, h } = sizeRef.current;
      const nodes = nodesRef.current;
      const mouse = mouseRef.current;

      // --- Physics ---
      for (const n of nodes) {
        // Gentle pull toward home position so the graph stays anchored.
        n.vx += (n.homeX - n.x) * 0.0008;
        n.vy += (n.homeY - n.y) * 0.0008;

        // Mouse repulsion: inverse-square-ish force within mouseRadius.
        if (mouse.active) {
          const dx = n.x - mouse.x;
          const dy = n.y - mouse.y;
          const distSq = dx * dx + dy * dy;
          if (distSq < mouseRadius * mouseRadius && distSq > 1) {
            const dist = Math.sqrt(distSq);
            const force = mouseStrength / distSq;
            n.vx += (dx / dist) * force;
            n.vy += (dy / dist) * force;
          }
        }

        // Damping keeps motion from running away.
        n.vx *= 0.94;
        n.vy *= 0.94;

        n.x += n.vx;
        n.y += n.vy;

        // Soft bounds — wrap around edges so nodes stay on screen.
        if (n.x < -20) n.x = w + 20;
        if (n.x > w + 20) n.x = -20;
        if (n.y < -20) n.y = h + 20;
        if (n.y > h + 20) n.y = -20;
      }

      // --- Render ---
      ctx.clearRect(0, 0, w, h);

      // Edges: for each node, connect to any neighbor within linkDistance.
      // Alpha fades with distance so the web feels organic.
      const maxDistSq = linkDistance * linkDistance;
      ctx.lineWidth = 1;
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const distSq = dx * dx + dy * dy;
          if (distSq < maxDistSq) {
            const t = 1 - distSq / maxDistSq;
            const edgeColor = palette[(a.colorIndex + b.colorIndex) % palette.length];
            ctx.strokeStyle = hexToRgba(edgeColor, opacity * 0.5 * t);
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      // Nodes: filled circles with a soft glow halo.
      for (const n of nodes) {
        const color = palette[n.colorIndex];
        // Halo
        const gradient = ctx.createRadialGradient(
          n.x,
          n.y,
          0,
          n.x,
          n.y,
          n.radius * 4,
        );
        gradient.addColorStop(0, hexToRgba(color, opacity * 0.6));
        gradient.addColorStop(1, hexToRgba(color, 0));
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius * 4, 0, Math.PI * 2);
        ctx.fill();

        // Core
        ctx.fillStyle = hexToRgba(color, opacity);
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(step);
    };

    rafRef.current = requestAnimationFrame(step);

    return () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, [palette, opacity, density, linkDistance, mouseRadius, mouseStrength]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 0,
      }}
    />
  );
};
