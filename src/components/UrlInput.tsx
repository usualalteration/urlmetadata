import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface UrlInputProps {
  onAnalyze: (url: string) => Promise<void>;
  loading: boolean;
}

const UrlInput = ({ onAnalyze, loading }: UrlInputProps) => {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed || loading) return;
    onAnalyze(trimmed).then(() => {
      // Clear the field only after a successful attempt; the parent
      // decides what to do with errors (it surfaces them separately).
      setUrl("");
    });
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <Label htmlFor="url-input" className="sr-only">
            URL da analizzare
          </Label>
          <Input
            id="url-input"
            name="url"
            type="text"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            autoComplete="off"
            disabled={loading}
            aria-describedby="url-help"
          />
        </div>
        <Button type="submit" disabled={loading} className="sm:w-auto">
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading...
            </>
          ) : (
            <>
              <Search className="h-4 w-4" />
              Analizza
            </>
          )}
        </Button>
      </div>
      <p id="url-help" className="mt-2 text-xs text-muted-foreground">
        Incolla un URL: verranno estratti titolo, descrizione, favicon e
        l'immagine di anteprima (Open Graph).
      </p>
    </form>
  );
};

export default UrlInput;