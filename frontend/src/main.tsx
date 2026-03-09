import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";

import "leaflet/dist/leaflet.css";
import "./index.css";
import App from "./App.tsx";
import { queryClient } from "@/lib/query-client";
import { AuthProvider } from "@/lib/auth-context";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
);
