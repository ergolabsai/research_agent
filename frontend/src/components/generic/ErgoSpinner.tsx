import { useTheme } from "@mui/material/styles";

export const ErgoSpinner: React.FC<{ size?: number; color?: string }> = ({
  size = 60,
  color,
}) => {
  const theme = useTheme();
  const dotColor = color || theme.palette.primary.main;

  const dotSize = size * 0.15;
  const radius = size * 0.15;
  const center = size / 2;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: size,
          height: size,
          position: "relative",
        }}
      >
        <style>{`
          @keyframes variableSpin {
            0% {
              transform: rotate(0deg);
              animation-timing-function: ease-in;
            }
            25% {
              transform: rotate(180deg);
              animation-timing-function: ease-out;
            }
            50% {
              transform: rotate(360deg);
              animation-timing-function: ease-in;
            }
            75% {
              transform: rotate(540deg);
              animation-timing-function: ease-out;
            }
            100% {
              transform: rotate(720deg);
            }
          }
          
          .spinner-container {
            animation: variableSpin 3s infinite;
          }
          
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
              transform: scale(1);
            }
            50% {
              opacity: 0.7;
              transform: scale(0.9);
            }
          }
          
          .dot {
            animation: pulse 1.5s ease-in-out infinite;
          }
          
          .dot:nth-child(2) {
            animation-delay: 0.5s;
          }
          
          .dot:nth-child(3) {
            animation-delay: 1s;
          }
        `}</style>

        <div
          className="spinner-container"
          style={{
            position: "absolute",
            inset: 0,
            transformOrigin: "center",
          }}
        >
          {/* Dot 1 - Top */}
          <div
            className="dot"
            style={{
              position: "absolute",
              width: dotSize,
              height: dotSize,
              borderRadius: "50%",
              backgroundColor: dotColor,
              left: center - dotSize / 2,
              top: center - radius - dotSize / 2,
            }}
          />

          {/* Dot 2 - Bottom Right */}
          <div
            className="dot"
            style={{
              position: "absolute",
              width: dotSize,
              height: dotSize,
              borderRadius: "50%",
              backgroundColor: dotColor,
              left: center + radius * Math.cos(Math.PI / 6) - dotSize / 2,
              top: center + radius * Math.sin(Math.PI / 6) - dotSize / 2,
            }}
          />

          {/* Dot 3 - Bottom Left */}
          <div
            className="dot"
            style={{
              position: "absolute",
              width: dotSize,
              height: dotSize,
              borderRadius: "50%",
              backgroundColor: dotColor,
              left: center - radius * Math.cos(Math.PI / 6) - dotSize / 2,
              top: center + radius * Math.sin(Math.PI / 6) - dotSize / 2,
            }}
          />
        </div>
      </div>
    </div>
  );
};
