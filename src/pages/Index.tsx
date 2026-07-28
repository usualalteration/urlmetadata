import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link2, AlertCircle, Loader2, LinkIcon } from "lucide-react";
import { toast } from "sonner";
import UrlInput from "@/components/UrlInput";
import MetadataCard from "@/components/MetadataCard";
import { extractMetadata, listMetadata, type MetadataItem } from "@/lib/api";

const Index = () => {
  const queryClient = useQueryClient();
  const [extracting, setExtracting] = useState(false);

  // Load the saved metadata gallery on mount (and on manual refetch).
  const {
    data: items = [],
    isLoading: listLoading,
    error: listError,
  } = useQuery<MetadataItem[], Error>({
    queryKey: ["metadata"],
    queryFn: listMetadata,
  });

  const handleAnalyze = async (url: string) => {
    setExtracting(true);
    try {
      const result = await extractMetadata(url);
      toast.success("Metadati estratti e salvati");
      if (result.warning) {
        toast.warning(result.warning);
      }
      // Refresh the gallery so the new item appears at the top.
      void queryClient.invalidateQueries({ queryKey: ["metadata"] });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Errore durante l'estrazione";
      toast.error(message);
      throw err; // re-throw so UrlInput keeps the typed value on failure
    } finally {
      setExtracting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Link2 className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">
              URL Metadata Collector
            </h1>
            <p className="text-sm text-muted-foreground">
              Estrai e archivia i metadati delle tue pagine web
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        {/* Input section */}
        <section className="mb-8">
          <div className="rounded-2xl border bg-card p-5 shadow-sm">
            <UrlInput onAnalyze={handleAnalyze} loading={extracting} />
          </div>
        </section>

        {/* Gallery / Dashboard */}
        <section>
          <div className="mb-4 flex items-center gap-2">
            <LinkIcon className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-lg font-semibold text-foreground">
              Link salvati
            </h2>
            <span className="text-sm text-muted-foreground">
              ({items.length})
            </span>
          </div>

          {listLoading ? (
            <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              Caricamento...
            </div>
          ) : listError ? (
            <div className="flex flex-col items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/5 py-12 text-center text-destructive">
              <AlertCircle className="h-6 w-6" />
              <p className="text-sm">
                Impossibile caricare lo storico: {listError.message}
              </p>
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed py-16 text-center text-muted-foreground">
              <Link2 className="h-8 w-8" />
              <p className="text-sm">
                Nessun URL analizzato. Inserisci un link sopra per iniziare.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((item, idx) => (
                <MetadataCard
                  key={`${item.url}-${idx}`}
                  item={item}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      <footer className="mx-auto max-w-5xl px-4 py-8 text-center text-xs text-muted-foreground">
        Powered by Nuvolaris OpenServerless · React + Tailwind
      </footer>
    </div>
  );
};

export default Index;