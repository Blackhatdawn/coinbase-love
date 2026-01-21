import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { initSentry } from "./lib/sentry.ts";
import { loadRuntimeConfig } from "./lib/runtimeConfig";
import { SpeedInsights } from "@vercel/speed-insights/react";

async function bootstrap() {
  await loadRuntimeConfig();
  initSentry();
  createRoot(document.getElementById("root")!).render(
    <>
      <App />
      <SpeedInsights />
    </>
  );
}

void bootstrap();
