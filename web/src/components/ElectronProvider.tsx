"use client";

import { useEffect, useState } from "react";
import { isElectron } from "@/lib/electron";

export function ElectronProvider({ children }: { children: React.ReactNode }) {
  const [isElectronApp, setIsElectronApp] = useState(false);

  useEffect(() => {
    setIsElectronApp(isElectron());
  }, []);

  return (
    <>
      {isElectronApp && (
        <div className="electron-title-bar">
          <span>DealFinder</span>
        </div>
      )}
      {children}
    </>
  );
}
