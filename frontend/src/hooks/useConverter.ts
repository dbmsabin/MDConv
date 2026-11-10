import { useCallback, useState } from "react";
import { arrayMove } from "@dnd-kit/sortable";
import { convertFiles, convertAlt } from "@/lib/api";
import type { ConvertResult, ConverterName } from "@/types";

export type ConverterState = {
  results: ConvertResult[];
  /** Original File objects — kept in memory so we can re-send for /convert-alt */
  fileMap: Map<string, File>;
  loading: boolean;
  /** Set when the whole /convert request fails (network or 5xx) */
  globalError: string | null;
  /** Files from the last failed request so Retry all can re-send them */
  pendingFiles: File[] | null;
};

export type ConverterActions = {
  handleDrop: (files: File[]) => Promise<void>;
  retryAll: () => Promise<void>;
  tryAltConverter: (id: string, converter: ConverterName) => Promise<void>;
  reorder: (oldIndex: number, newIndex: number) => void;
  rename: (id: string, newName: string) => void;
  remove: (id: string) => void;
  clearAll: () => void;
};

export function useConverter(): ConverterState & ConverterActions {
  const [results, setResults] = useState<ConvertResult[]>([]);
  const [fileMap, setFileMap] = useState<Map<string, File>>(new Map());
  const [loading, setLoading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [pendingFiles, setPendingFiles] = useState<File[] | null>(null);

  const handleDrop = useCallback(async (files: File[]) => {
    setLoading(true);
    setGlobalError(null);
    setPendingFiles(null);

    try {
      const response = await convertFiles(files);

      // Build a map from result id -> original File (by filename match)
      const newFileMap = new Map<string, File>(fileMap);
      for (const result of response.results) {
        const original = files.find((f) => f.name === result.filename);
        if (original) {
          newFileMap.set(result.id, original);
        }
      }

      setResults((prev) => [...prev, ...response.results]);
      setFileMap(newFileMap);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setGlobalError(msg);
      setPendingFiles(files);
    } finally {
      setLoading(false);
    }
  }, [fileMap]);

  const retryAll = useCallback(async () => {
    if (!pendingFiles) return;
    await handleDrop(pendingFiles);
  }, [pendingFiles, handleDrop]);

  const tryAltConverter = useCallback(
    async (id: string, converter: ConverterName) => {
      const file = fileMap.get(id);
      if (!file) return;

      setResults((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: "ok", error: null } : r))
      );

      try {
        const updated = await convertAlt(file, converter);
        updated.id = id; // keep the same id so the row stays in place
        setResults((prev) => prev.map((r) => (r.id === id ? updated : r)));
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Unknown error";
        setResults((prev) =>
          prev.map((r) =>
            r.id === id
              ? { ...r, status: "error", error: msg, error_code: "unknown" }
              : r
          )
        );
      }
    },
    [fileMap]
  );

  const reorder = useCallback((oldIndex: number, newIndex: number) => {
    setResults((prev) => arrayMove(prev, oldIndex, newIndex));
  }, []);

  const rename = useCallback((id: string, newName: string) => {
    setResults((prev) =>
      prev.map((r) => (r.id === id ? { ...r, filename: newName } : r))
    );
  }, []);

  const remove = useCallback((id: string) => {
    setResults((prev) => prev.filter((r) => r.id !== id));
    setFileMap((prev) => {
      const next = new Map(prev);
      next.delete(id);
      return next;
    });
  }, []);

  const clearAll = useCallback(() => {
    setResults([]);
    setFileMap(new Map());
    setGlobalError(null);
    setPendingFiles(null);
  }, []);

  return {
    results,
    fileMap,
    loading,
    globalError,
    pendingFiles,
    handleDrop,
    retryAll,
    tryAltConverter,
    reorder,
    rename,
    remove,
    clearAll,
  };
}

