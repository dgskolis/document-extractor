import { useEffect } from "react";

export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} | GenHealth`;

    return () => {
      document.title = "GenHealth";
    };
  }, [title]);
}
