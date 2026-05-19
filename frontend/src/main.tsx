// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

async function bootstrap() {
  // Dynamic import keeps axios-mock-adapter out of production bundles.
  if (import.meta.env.MODE === "mock" || import.meta.env.VITE_MOCK_API === "true") {
    const { setupMockApi } = await import("./mocks/mockApi");
    setupMockApi();
  }

  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

bootstrap();
