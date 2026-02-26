import type { SpringConfig } from "remotion";

export const SPRING_SNAPPY: SpringConfig = {
  damping: 12,
  mass: 0.5,
  stiffness: 200,
  overshootClamping: false,
};

export const SPRING_GENTLE: SpringConfig = {
  damping: 15,
  mass: 1,
  stiffness: 100,
  overshootClamping: false,
};

export const SPRING_SLAM: SpringConfig = {
  damping: 8,
  mass: 2,
  stiffness: 300,
  overshootClamping: false,
};

export const SPRING_CRISP: SpringConfig = {
  damping: 200,
  mass: 1,
  stiffness: 200,
  overshootClamping: false,
};
