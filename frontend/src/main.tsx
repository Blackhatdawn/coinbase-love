import { createRoot } from "react-dom/client";
import { StrictMode } from "react";
import { SpeedInsights } from "@vercel/speed-insights/react";
import App from "./App.tsx";
import "./index.css";
import { initSentry } from "@/lib/sentry";
import { loadRuntimeConfig } from "@/lib/runtimeConfig";

const root = createRoot(document.getElementById("root")!);

const renderApp = () => {
  root.render(
    <StrictMode>
      <App />
      <SpeedInsights />
    </StrictMode>
  );
};

const bootstrap = async () => {
  try {
    await loadRuntimeConfig();
  } finally {
    initSentry();
    renderApp();
  }
};

void bootstrap();
