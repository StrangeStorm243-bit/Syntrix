export function Scanlines({
  opacity = 0.03,
  className,
}: {
  opacity?: number;
  className?: string;
}) {
  return (
    <div
      className={className ?? ""}
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 50,
        pointerEvents: "none",
        backgroundImage: `repeating-linear-gradient(
          0deg,
          transparent,
          transparent 2px,
          rgba(0,0,0,${opacity}) 2px,
          rgba(0,0,0,${opacity}) 4px
        )`,
        animation: "scanline-scroll 8s linear infinite",
      }}
      aria-hidden="true"
    />
  );
}
