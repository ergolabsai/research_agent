import React from "react";
import ReactDOM from "react-dom/client";
import "./mocks/setupMockApi";
import "../../frontend/src/index.css";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
