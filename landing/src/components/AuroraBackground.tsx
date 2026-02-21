export function AuroraBackground() {
  return (
    <div
      className="pointer-events-none absolute inset-0 overflow-hidden"
      aria-hidden="true"
    >
      {/* Cyan blob */}
      <div
        className="absolute -top-40 left-1/2 -translate-x-1/2 h-[500px] w-[600px] rounded-full opacity-30 blur-[80px] animate-aurora-1"
        style={{
          background:
            "radial-gradient(circle, #06B6D4 0%, transparent 70%)",
        }}
      />
      {/* Magenta blob */}
      <div
        className="absolute -top-20 left-1/3 h-[400px] w-[500px] rounded-full opacity-25 blur-[80px] animate-aurora-2"
        style={{
          background:
            "radial-gradient(circle, #D946EF 0%, transparent 70%)",
        }}
      />
      {/* Blue blob */}
      <div
        className="absolute top-0 left-2/3 h-[450px] w-[550px] rounded-full opacity-25 blur-[80px] animate-aurora-3"
        style={{
          background:
            "radial-gradient(circle, #3B82F6 0%, transparent 70%)",
        }}
      />
    </div>
  );
}
