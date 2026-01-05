import { useCallback, useState } from "react";

export function useStatus() {
  const [message, setMessage] = useState("");
  const [kind, setKind] = useState("");
  const set = useCallback((msg, k = "") => {
    setMessage(msg);
    setKind(k);
  }, []);
  return [message, kind, set];
}

