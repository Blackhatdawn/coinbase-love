import { createRoot } from "react-dom/client";
import { StrictMode } from "react";
import { SpeedInsights } from "@vercel/speed-insights/react";
import App from "./App.tsx";
import "./index.css";
import { initSentry } from "@/lib/sentry";
import { loadRuntimeConfig } from "@/lib/runtimeConfig";

async function bootstrap() {
  await loadRuntimeConfig();
  initSentry();
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
      <SpeedInsights />
    </StrictMode>
  );
}

void bootstrap();
